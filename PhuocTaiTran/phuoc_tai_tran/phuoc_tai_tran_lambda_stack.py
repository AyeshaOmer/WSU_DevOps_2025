from ast import alias
from logging import config
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    # aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns_subscriptions as subscriptions,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cw,   
    aws_iam as iam,
    aws_codedeploy as codedeploy
)

from Module import constantSource

import aws_cdk as cdk
import aws_cdk.aws_cloudwatch_actions as cw_actions


from constructs import Construct

class PhuocTaiTranLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage_name: str = "default", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store stage name for unique resource naming
        self.stage_name = stage_name
        # Create IAM role for Lambda function
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/README.html
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSNSFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")
            ]
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html
        # Create DynamoDB table for storing alarm notifications
        table = dynamodb.TableV2(self, "WebsiteAlarmsTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
        )

        fn = _lambda.Function( 
        self, "PhuocTaiTranLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="ObtainMetrics.handler",
        code=_lambda.Code.from_asset("Module"),  # Changed from "lib/lambda-handler/Module"
        role=lambda_role  # <-- assign the role here (policy above)
        )

        fn_hello = _lambda.Function(
        self, "PhuocTaiTranHelloLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="helloLambda.handler",
        code=_lambda.Code.from_asset("Module"),  # Changed from "lib/lambda-handler/Module"
        role=lambda_role  # <-- assign the role here (policy above)
        )

        # Add DB Lambda to handle alarms
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
        # When CloudWatch alarms trigger → They send notifications to SNS
        # SNS topic → Triggers the fn_db Lambda function
        # fn_db → Processes the alarm data and stores it in DynamoDB
        
        fn_db = _lambda.Function(
        self, "PhuocTaiTranDBLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="DBLambda.lambda_handler",
        code=_lambda.Code.from_asset("Module"),
        role=lambda_role,
        environment={
            "DYNAMODB_TABLE": table.table_name
        }
        )

        

        endpoint = apigw.LambdaRestApi(
        self, "ApiGwEndpoint",
        handler=fn,
        rest_api_name="PhuocTaiTranLambdaAPI",
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html
        # Schedule the Lambda function to run every 5 minutes (can be deleted as cloudwatch event has a trigger already)
        rule = events.Rule(
            self, "ScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(fn),
                     targets.LambdaFunction(fn_hello)]
        )

        # SNS TOPIC
        #https://docs.aws.amazo# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.k/api/v//pyth.htmlaws_snsTopic
        topic = sns.Topic(self, "Alarm notification", display_name="SNS notification for www.com")

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html
        topic.add_subscription(subscriptions.EmailSubscription("tranphuoctaibxan13@gmail.com"))
        #add lambda subscription to SNS topic for DB logging
        topic.add_subscription(subscriptions.LambdaSubscription(fn_db))

        # DASHBOARD
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        # Create single CloudWatch dashboard with all URLs
        dashboard = cw.Dashboard(self, "PhuocTaiTranDashboard",
            dashboard_name=f"PhuocTaiTranDashboard-{self.stage_name}"
        )
        
        # Use imported URLS for dashboard and alarms
        for i, url in enumerate(constantSource.URLS):
            availability_metric = cw.Metric(
                namespace=constantSource.URL_NAMESPACE,
                metric_name=constantSource.URL_MONITOR_AVAILABILITY,
                dimensions_map={"URL": url},
                period=Duration.minutes(5),  # Match your Lambda schedule
                statistic="Average"
            )
            latency_metric = cw.Metric(
                namespace=constantSource.URL_NAMESPACE,
                metric_name=constantSource.URL_MONITOR_LATENCY,
                dimensions_map={"URL": url},
                period=Duration.minutes(5),  # Match your Lambda schedule
                statistic="Average"
            )

            # Add combined widget with separate Y-axes for each URL
            dashboard.add_widgets(
                cw.GraphWidget(
                    title=f"Monitoring for {url}",
                    left=[availability_metric],
                    right=[latency_metric],
                    left_y_axis=cw.YAxisProps(min=0, max=1, label="Availability"),
                    right_y_axis=cw.YAxisProps(min=0, label="Latency (seconds)"),
                    width=24,
                    height=6
                )
            )

            # ALARMS
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
            # Create alarm for availability drop to 0
            availability_alarm = cw.Alarm(
                self, f"AvailabilityAlarm-{url}",
                metric=availability_metric,
                threshold=0,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
                alarm_description=f"Availability dropped to 0 for {url}",
                treat_missing_data=cw.TreatMissingData.BREACHING
            )

            # Create alarm for latency higher than 0.5
            latency_alarm = cw.Alarm(
                self, f"LatencyAlarm-{url}",
                metric=latency_metric,
                threshold=0.5,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Latency higher than 0.5 for {url}",
                treat_missing_data=cw.TreatMissingData.BREACHING
            )

            # Trigger SNS topic on alarm
            availability_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            latency_alarm.add_alarm_action(cw_actions.SnsAction(topic))

        # Lambda function metrics and alarms
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        # fn: function       
        invocMetric = cw.Metric(
            namespace="AWS/Lambda",
            metric_name="Invocations",
            period=Duration.minutes(5),
        )
        
        WHIMetric = fn.metric_invocations()
        invocation_alarm = cw.Alarm(
                self, f"alarm_invocation",
                metric = WHIMetric,
                threshold=5,  # Alert if less than 5 invocations in 5 minutes
                evaluation_periods=2,  # Check for 2 consecutive periods (10 minutes)
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                treat_missing_data=cw.TreatMissingData.BREACHING,
                alarm_description="Lambda function has unusually low invocation count"
            )

        WHNMetric = fn.metric_duration()
        duration_alarm = cw.Alarm(
                self, f"alarm_duration",
                metric = WHNMetric,
                threshold=30000,  # Alert if duration > 30 seconds (30,000 ms)
                evaluation_periods=2,  # Check for 2 consecutive periods
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
                alarm_description="Lambda function execution duration is too high"
            )
        
        # Add error rate alarm for better monitoring
        error_metric = fn.metric_errors()
        error_alarm = cw.Alarm(
                self, f"alarm_errors",
                metric = error_metric,
                threshold=1,  # Alert on any errors
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
                alarm_description="Lambda function is experiencing errors"
            )
        
        # Connect Lambda alarms to SNS topic for notifications and DynamoDB logging
        invocation_alarm.add_alarm_action(cw_actions.SnsAction(topic))
        duration_alarm.add_alarm_action(cw_actions.SnsAction(topic))
        error_alarm.add_alarm_action(cw_actions.SnsAction(topic))
        

        # ROLLBACK
        # Set up CodeDeploy for Lambda with alarms for rollback
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html
        version = fn.current_version
        alias = _lambda.Alias(self, "LambdaAlias",
            alias_name="Prod",
            version=version
        )

        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
            alarms=[invocation_alarm, duration_alarm, error_alarm]  # Include error alarm for rollback
        )
    
        # Note: Log groups are automatically created by Lambda functions
        # and removal policy is typically set at the stack level
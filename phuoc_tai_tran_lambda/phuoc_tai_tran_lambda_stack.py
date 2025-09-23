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
    aws_iam as iam
)

from Module import constantSource

import aws_cdk as cdk
import aws_cdk.aws_cloudwatch_actions as cw_actions


from constructs import Construct

class PhuocTaiTranLambdaStack(Stack):

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        fn = _lambda.Function( 
        self, "PhuocTaiTranLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="ObtainMetrics.handler",
        code=_lambda.Code.from_asset("lib/lambda-handler/Module"),
        role=lambda_role  # <-- assign the role here (policy above)
        )

        fn_hello = _lambda.Function(
        self, "PhuocTaiTranHelloLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="helloLambda.handler",
        code=_lambda.Code.from_asset("lib/lambda-handler/Module"),
        role=lambda_role  # <-- assign the role here (policy above)
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

        #https://docs.aws.amazo# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.k/api/v//pyth.htmlaws_snsTopic
        topic = sns.Topic(self, "Alarm notification", display_name="SNS notification for www.com")

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html
        topic.add_subscription(subscriptions.EmailSubscription("tranphuoctaibxan13@gmail.com"))
        #add lambda subscription to SNS topic

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html
        table = dynamodb.TableV2(self, "Table",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING)
        )       
        app = cdk.App()
        stack = cdk.Stack(app, "Stack", env=cdk.Environment(region="us-west-2"))

        global_table = dynamodb.TableV2(stack, "GlobalTable",
        partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        replicas=[dynamodb.ReplicaTableProps(region="us-east-1"), dynamodb.ReplicaTableProps(region="us-east-2")
        ]
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        # Create CloudWatch dashboard
        dashboard = cw.Dashboard(self, "PhuocTaiTranDashboard",
            dashboard_name="PhuocTaiTranDashboard"
        )

        # Use imported URLS for dashboard and alarms
        for url in constantSource.URLS:
            availability_metric = cw.Metric(
                namespace=constantSource.URL_NAMESPACE,
                metric_name=constantSource.URL_MONITOR_AVAILABILITY,
                dimensions_map={"URL": url},
                period=Duration.minutes(1),
                statistic="Average"
            )
            latency_metric = cw.Metric(
                namespace=constantSource.URL_NAMESPACE,
                metric_name=constantSource.URL_MONITOR_LATENCY,
                dimensions_map={"URL": url},
                period=Duration.minutes(1),
                statistic="Average"
            )

            # Add combined graph widget
            dashboard.add_widgets(
                cw.GraphWidget(
                    title=f"Availability & Latency for {url}",
                    left=[availability_metric, latency_metric],
                    left_y_axis=cw.YAxisProps(min=0),
                    width=24,
                    height=6
                )
            )

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
                threshold=0.31,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Latency higher than 0.5 for {url}",
                treat_missing_data=cw.TreatMissingData.BREACHING
            )

            # Optionally, add alarm actions (e.g., SNS notification)
            availability_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            latency_alarm.add_alarm_action(cw_actions.SnsAction(topic))


        fn_log_group = fn.log_group
        fn_log_group.apply_removal_policy(RemovalPolicy.DESTROY)
        
        fn_log_group_2 = fn_hello.log_group
        fn_log_group_2.apply_removal_policy(RemovalPolicy.DESTROY)
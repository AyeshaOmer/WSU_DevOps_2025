# import necessary libraries
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_events as events_,
    aws_events_targets as targets_,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_codedeploy as codedeploy,
)
from constructs import Construct
import os, json, re
from aws_cdk.aws_dynamodb import TableV2, Attribute, AttributeType, Billing, TableEncryptionV2

NAMESPACE = "THOMASPROJECT_WSU2025"


class DangQuocToanStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        #--- 1. Load website so we can create per-URL alarms/widgets
        websites_path = os.path.join(os.path.dirname(__file__), "..", "modules", "website.json")
        with open(websites_path, "r", encoding = "utf-8") as f:
            website_list = [entry["url"] for entry in json.load(f)]
        
        #--- 2. Create and define the Lambda function
        # Reference: AWS CDK Python – aws_lambda.Function
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function
        fn = _lambda.Function(self, "WHlambda",
            runtime=_lambda.Runtime.PYTHON_3_13,  # see aws_lambda.Runtime options
            handler="WHLambda.lambda_handler",    # see aws_lambda.Function handler param
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "modules")
            ),  # see aws_lambda.Code.from_asset
            timeout=Duration.seconds(30),  # see aws_lambda.Function timeout param
        )

        # Give the Lambda function permissions to publish metrics to CLoudWatch
        # Reference: AWS CDK Python – iam.PolicyStatement
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/README.html#policystatement
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],   # cloudwatch metric permission
                resources=["*"],
            )
        )
        
        # --- Attach basic Lambda execution role ---
        # Reference: AWS CDK Python – iam.ManagedPolicy.from_aws_managed_policy_name
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/README.html#managedpolicy
        fn.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )
        
        # Publish a version + alias for CodeDeploy traffic shifting
        version = fn.current_version
        alias = _lambda.Alias(self, "WHAlias", alias_name="live", version=version)

        # Schedule for scheduled events rules
        # Reference: AWS CDK Python – aws_events.Rule
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/README.html#rule
        schedule= events_.Schedule.rate(Duration.minutes(5))   # Reference: aws_events.Schedule.rate

        # Create the event target (invoke the alias so deployments shift traffic gradually)
        # Reference: AWS CDK Python – aws_events_targets.LambdaFunction
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/README.html#lambdafunction
        target = targets_.LambdaFunction(alias)
        
        # AWS evetns_.Rule
        events_.Rule (
            self, "CanaryScheduleRule",
            schedule=schedule,
            targets=[target],
            description="This is a test rule that invokes a lambda function every 5 minutes"
        )

        #--- 3. SNS Topic for alarms (uncomment and add your email)
        # Reference: AWS CDK Python – aws_sns.Topic
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/README.html#topic
        topic = sns.Topic(
            self,
            "WebHealthAlarms",
            topic_name=f"web-health-alarms-{self.stack_name}".lower(),
        )
        # Reference: AWS CDK Python – aws_sns_subscriptions.EmailSubscription
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/README.html#emailsubscription
        topic.add_subscription(subs.EmailSubscription("22119278@student.westernsydney.edu.au"))

        #--- 4. DynamoDB for alarm logs
            # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        alarm_log_table = TableV2(
            self,
            "AlarmLogTable",
            table_name=f"AlarmLogTable-{self.stack_name}",
            partition_key=Attribute(name="AlarmName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.STRING),
            billing=Billing.on_demand(),
            encryption=TableEncryptionV2.dynamo_owned_key(),
        )
        alarm_log_table.apply_removal_policy(RemovalPolicy.DESTROY)

            #--- 5. Logger Lambda: subscribe to SNS and writes to DynamoDN
            # Reference:
        log_lambda = _lambda.Function(
            self, "LogAlarmLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="LogAlarmLambda.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "modules")
            ),
            timeout=Duration.seconds(30),
            environment={"TABLE_NAME": alarm_log_table.table_name}
        )

        # Allow Lambda to write to the table
        alarm_log_table.grant_write_data(log_lambda)

        # Explicitly allow LogAlarmLambda to PutItem into the DynamoDB table
        log_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem"
                ],
                resources=[
                    alarm_log_table.table_arn
                ]
            )
        )

        # Subscribe Lambda to SNS topic                              
        topic.add_subscription(subs.LambdaSubscription(log_lambda))


        #--- 6. Operational alarms for the crawler Lambda (errors, throttles, duration, invocations, memory)
        errors_alarm = cloudwatch.Alarm(
            self, "LambdaErrorsAlarm",
            metric=fn.metric_errors(period=Duration.minutes(5), statistic="sum"),
            threshold=0,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            alarm_description="Lambda errors > 0"
        )

        throttles_alarm = cloudwatch.Alarm(
            self, "LambdaThrottlesAlarm",
            metric=fn.metric_throttles(period=Duration.minutes(5), statistic="sum"),
            threshold=0,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            alarm_description="Lambda throttles > 0"
        )

        duration_alarm = cloudwatch.Alarm(
            self, "LambdaDurationP99Alarm",
            metric=fn.metric_duration(period=Duration.minutes(5), statistic="p99"),
            threshold=5000,  # ms
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            alarm_description="Lambda p99 duration > 5s"
        )

        invocations_low_alarm = cloudwatch.Alarm(
            self, "LambdaInvocationsLowAlarm",
            metric=fn.metric_invocations(period=Duration.minutes(5), statistic="sum"),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            alarm_description="Lambda invocations < 1 in 5m"
        )

        # Memory: MaxMemoryUsed is available via CloudWatch for many accounts.
        # If missing, alarm treats missing data as NOT_BREACHING.
        memory_metric = cloudwatch.Metric(
            namespace="AWS/Lambda",
            metric_name="MaxMemoryUsed",
            dimensions_map={"FunctionName": fn.function_name},
            period=Duration.minutes(5),
            statistic="max",
        )
        memory_alarm = cloudwatch.Alarm(
            self, "LambdaMemoryAlarm",
            metric=memory_metric,
            threshold=120,  # MB (approx for default 128MB)
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Lambda max memory used > 120MB"
        )

        # Send operational alarms to the same SNS topic
        for op_alarm in [errors_alarm, throttles_alarm, duration_alarm, invocations_low_alarm, memory_alarm]:
            op_alarm.add_alarm_action(cw_actions.SnsAction(topic))

        #--- 7. Create CloudWatch metrics with dimension for each URL
        # Reference: AWS CDK Python – aws_cloudwatch.Metric
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/README.html#metric
        def metric_availability(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="availability",
                period=Duration.minutes(5),
                label=f"availability: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        def metric_latency(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="latency",
                period=Duration.minutes(5),
                label=f"latency: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        def metric_status(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="status",
                period=Duration.minutes(5),
                label=f"status: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        #--- 7. Alarms per URL
        for url in website_list:
            safe_id = self._sanitize_id(url)
            
        # Availability alarm: alarm when < 1 (site down or non-2xx/3xx)
        # Reference: AWS CDK Python – aws_cloudwatch.Alarm
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/README.html#alarm
            avail_alarm = cloudwatch.Alarm(
            self, f"AvailabilityAlarm-{safe_id}",
            metric=metric_availability(url),
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Availability < 1 for {url}"
        )

        # Latency alarm: > 2000 ms (tune as needed)
            latency_alarm = cloudwatch.Alarm(
            self, f"LatencyAlarm-{safe_id}",
            metric=metric_latency(url),
            threshold=2000,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Latency > 2000 ms for {url}"
        )
            
        # Create an SNS topic for alarm notifications
            status_alarm = cloudwatch.Alarm(
            self, f"StatusAlarm-{safe_id}",
            metric=metric_status(url),
            threshold=399,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Status > 399 for {url}"
            ) 

            # Link alarms to SNS topic
            # Reference: AWS CDK Python – aws_cloudwatch_actions.SnsAction
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch_actions/README.html#snsaction
            avail_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            latency_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            status_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            

            
 


        #--- 8. Create a graph widget for availability metric
         # Reference: AWS CDK Python – aws_cloudwatch.GraphWidget
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/README.html#graphwidget
        avail_widget = cloudwatch.GraphWidget(
            title = "Availability (avg by URL, 5m)",
            left = [metric_availability(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a graph widget for the latency metric
        latency_widget = cloudwatch.GraphWidget(
            title = "Latency (avg by URL, 5m)",
            left = [metric_latency(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a graph widget for the status code metric
        status_code_widget = cloudwatch.GraphWidget(
            title = "HTTP Status (avg by URL, 5m)",
            left = [metric_status(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a dashboard
        # Reference: AWS CDK Python – aws_cloudwatch.Dashboard
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/README.html#dashboard
        cloudwatch.Dashboard(
            self,
            "WHLambdaDashboard",
            dashboard_name=f"URLMONITOR_DASHBOARD_{self.stack_name}",
            widgets=[
                [avail_widget],
                [latency_widget],
                [status_code_widget],
            ],
        )

        # --- 10. Targets CRUD API (DynamoDB + Lambda + API Gateway)
        targets_table = TableV2(
            self,
            "TargetsTable",
            table_name=f"TargetsTable-{self.stack_name}",
            partition_key=Attribute(name="WebsiteName", type=AttributeType.STRING),
            billing=Billing.on_demand(),
            encryption=TableEncryptionV2.dynamo_owned_key(),
        )
        targets_table.apply_removal_policy(RemovalPolicy.DESTROY)

        targets_lambda = _lambda.Function(
            self,
            "TargetsApiLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="TargetsApiLambda.handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "modules")
            ),
            timeout=Duration.seconds(30),
            environment={
                "TARGETS_TABLE_NAME": targets_table.table_name,
                "METRIC_NAMESPACE": NAMESPACE,
            },
        )
        targets_table.grant_read_write_data(targets_lambda)
        targets_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        api = apigw.RestApi(
            self,
            "TargetsApi",
            rest_api_name=f"TargetsApi-{self.stack_name}",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
            deploy_options=apigw.StageOptions(stage_name="v1"),
        )

        lambda_integration = apigw.LambdaIntegration(targets_lambda, proxy=True)
        targets_res = api.root.add_resource("targets")
        targets_res.add_method("ANY", lambda_integration)
        item_res = targets_res.add_resource("{id}")
        item_res.add_method("ANY", lambda_integration)

        #--- 9. CodeDeploy application + deployment group (Prod-only by default)
        enable_cd_ctx = self.node.try_get_context("enable_code_deploy")
        # Only enable CodeDeploy when explicitly requested via context
        if isinstance(enable_cd_ctx, str) and enable_cd_ctx.lower() in ("1", "true", "yes"):
            cd_app = codedeploy.LambdaApplication(self, "WHDeploymentApp")
            cd_app.apply_removal_policy(RemovalPolicy.RETAIN)

            dg = codedeploy.LambdaDeploymentGroup(
                self,
                "WHDeploymentGroup",
                alias=alias,
                application=cd_app,
                deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
                alarms=[errors_alarm, throttles_alarm, duration_alarm],  # key health signals
                auto_rollback=codedeploy.AutoRollbackConfig(
                    deployment_in_alarm=True,
                    failed_deployment=True,
                    stopped_deployment=True,
                ),
            )
            # Retain on delete to avoid subscription/delete failures in some accounts
            dg.apply_removal_policy(RemovalPolicy.RETAIN)

        # Helper for ID-safe names (CDK IDs must avoid problematic chars)
    def _sanitize_id(self, url: str) -> str:
        clean = url.replace("https://", "").replace("http://", "")
        # replace any non-alphanumeric or underscore with underscore

        clean = re.sub(r'[^A-Za-z0-9_]', '_', clean)
        # truncate to 100 chars just in case
        
        return clean[:100]
## API Gateway.............

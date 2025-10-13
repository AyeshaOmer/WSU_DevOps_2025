from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_cloudwatch as cw,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_dynamodb as dynamodb,
    aws_cloudwatch_actions as actions,
    CfnOutput,
    aws_lambda_event_sources as event_sources,
)
from constructs import Construct
from modules.WebHealthLambda import get_urls

class PatDowdStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

       
        # Create DynamoDB table for URLs
        url_table = dynamodb.Table(
            self,
            "UrlTable",
            partition_key=dynamodb.Attribute(
                name="type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # For development; change to RETAIN for production
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Create URL Manager Lambda function
        url_manager = _lambda.Function(
            self,
            "UrlManagerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="url_manager.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": url_table.table_name
            },
        )

        # Grant DynamoDB permissions to the URL Manager Lambda
        url_table.grant_read_write_data(url_manager)

        # Create API Gateway
        api = apigw.RestApi(
            self,
            "UrlManagerApi",
            rest_api_name="URL Manager API",
            description="API for managing monitored URLs"
        )

        urls = api.root.add_resource("urls")
        urls.add_method("GET", apigw.LambdaIntegration(url_manager))
        urls.add_method("POST", apigw.LambdaIntegration(url_manager))
        
        url = urls.add_resource("{url}")
        url.add_method("DELETE", apigw.LambdaIntegration(url_manager))


        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="URL of the API Gateway endpoint",
            export_name="UrlApiEndpoint",
        )
        # Create Web Health Lambda function
        fn = _lambda.Function(
            self,
            "WebHelperFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="WebHealthLambda.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(30),
            environment={
                "URL_TABLE_NAME": url_table.table_name
            },
        )

        # Grant DynamoDB read permissions to Web Health Lambda
        url_table.grant_read_data(fn)
        
        rule = events.Rule(
            self, "EveryMinuteRule", schedule=events.Schedule.rate(Duration.minutes(1))
        )
        rule.add_target(targets.LambdaFunction(fn))

        #role definitons
        fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"], resources=["*"]
            )
        )

        # create dashboard
        # Create DynamoDB table for alarm logging
        alarm_table = dynamodb.Table(
            self,
            "AlarmLogsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # For development; change to RETAIN for production
        )

        # Create Lambda function for logging alarms to DynamoDB
        alarm_logger = _lambda.Function(
            self,
            "AlarmLoggerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="alarm_logger.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": alarm_table.table_name
            },
        )

        # Grant DynamoDB permissions to the Lambda function
        alarm_table.grant_write_data(alarm_logger)

        # New: Dynamic Updater Lambda (triggered by stream)
        dynamic_updater = _lambda.Function(
            self,
            "DynamicUpdaterFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="dynamic_updater.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(60),  # Longer for many URLs
            environment={
                "URL_TABLE_NAME": url_table.table_name,
                "ALARM_TABLE_NAME": alarm_table.table_name,  # If needed for logging
                "DASHBOARD_NAME": "Dash",
                "EMAIL_SUB": "patdowd07@gmail.com",
            },
        )

        # Grant permissions to Dynamic Updater
        url_table.grant_read_data(dynamic_updater)  # Query current URLs
        # CloudWatch: Manage alarms and dashboard
        dynamic_updater.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:DeleteAlarms",
                    "cloudwatch:PutMetricAlarm",
                    "cloudwatch:DescribeAlarms",  # To list/delete old ones
                    "cloudwatch:PutDashboard",
                    "cloudwatch:DeleteDashboards",  # Optional: If recreating
                ],
                resources=["*"],  # Scope to your namespace if possible
            )
        )
        # SNS: Create/delete topics and subscriptions
        dynamic_updater.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sns:CreateTopic",
                    "sns:DeleteTopic",
                    "sns:AddPermission",
                    "sns:Subscribe",
                    "sns:Unsubscribe",
                    "sns:ListSubscriptionsByTopic",
                    "sns:RemovePermission",
                ],
                resources=["*"],
            )
        )
        # Trigger: Add Event Source Mapping for the stream
        dynamic_updater.add_event_source(
            event_sources.DynamoEventSource(
                url_table,
                starting_position=_lambda.StartingPosition.TRIM_HORIZON,  # Start from now; change to LATEST for ongoing
                batch_size=10,  # Small batches for URL changes
                # Filter to only 'url' type changes (optional, via bisect if needed)
            )
        )

        # Grant permission for alarm_logger to be subscribed (if using per-topic subs)
        alarm_logger.add_permission(
            "SubscribeFromDynamicUpdater",
            principal=iam.ServicePrincipal("sns.amazonaws.com"),
            source_arn="*",  # Or specific topic ARNs; broad for dynamic
            action="lambda:InvokeFunction",
        )

        # Create empty initial dashboard (will be updated by Lambda)
        dashboard = cw.Dashboard(
            self, "Dash",
            dashboard_name="Dash",  # Explicit name for Lambda reference
            # Remove variables if not needed; or keep for region filter
        )
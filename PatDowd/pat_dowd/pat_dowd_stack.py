from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_cloudwatch as cw,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_dynamodb as dynamodb,
    aws_cloudwatch_actions as actions,
)
from constructs import Construct

class PatDowdStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

       
        fn = _lambda.Function(
            self,
            "WebHelperFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="WebHealthLambda.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(30),
        )
        #cadence definition
        
        rule = events.Rule(
            self, "EveryMinuteRule", schedule=events.Schedule.rate(Duration.minutes(1))
        )
        rule.add_target(targets.LambdaFunction(fn))

        #role definitons
        fn.add_to_role_policy(
            aws_iam.PolicyStatement(
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
            }
        )

        # Grant DynamoDB permissions to the Lambda function
        alarm_table.grant_write_data(alarm_logger)

        dashboard = cw.Dashboard(self, "Dash",
            default_interval=Duration.days(7),
            variables=[cw.DashboardVariable(
                id="board1",
                type=cw.VariableType.PATTERN,
                label="Web Health",
                input_type=cw.VariableInputType.INPUT,
                value="us-east-1",
                default_value=cw.DefaultValue.value("us-east-1"),
                visible=True
            )]
        )
        # create widgets
        for url in ["www.google.com", "www.youtube.com", "www.coolmathgames.com"]:

            availability_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="Availability",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1)
            )

            latency_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="Latency",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1)
            )

            size_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="ResponseSize",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1),

            )
            # Create SNS Topic for alarms
            alarm_topic = sns.Topic(
                self,
                f"{url}-alarm-topic",
                display_name=f"Web Health Alarms for {url}",
            )

            # Add email subscription to the topic
            alarm_topic.add_subscription(
                sns_subs.EmailSubscription("patdowd07@gmail.com")
            )
            
            # Add Lambda subscription to log alarms in DynamoDB
            alarm_topic.add_subscription(
                sns_subs.LambdaSubscription(alarm_logger)
            )

            # Create alarms
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
            availability_alarm = cw.Alarm(
                self,
                f"{url} Availability Alarm",
                metric=availability_metric,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
                threshold=0,
                evaluation_periods=1,

            )
            availability_alarm.add_alarm_action(actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(
                self,
                f"{url} Latency Alarm",
                metric=latency_metric,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                threshold=1,
                evaluation_periods=1,


            )
            latency_alarm.add_alarm_action(actions.SnsAction(alarm_topic))
            
            size_alarm = cw.Alarm(
                self,
                f"{url} Size Alarm",
                metric=size_metric,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                threshold=1,
                evaluation_periods=1,
            )
            size_alarm.add_alarm_action(actions.SnsAction(alarm_topic))


            widget_array = []
            widget_array.append(cw.AlarmWidget(
                title=f"{url} Availability",
                alarm=availability_alarm
            ))

            widget_array.append(cw.AlarmWidget(
                title=f"{url} Latency",
                alarm=latency_alarm
            ))

            widget_array.append(cw.AlarmWidget(
                title=f"{url} Size",
                alarm=size_alarm
            ))
        
            dashboard.add_widgets(*widget_array)



from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch_actions as actions,
    RemovalPolicy
)
from constructs import Construct

class BraydenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a DynamoDB table to store alarm events
        alarm_table = dynamodb.Table(self, "AlarmTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create a log group for the Lambda function with a removal policy.
        log_group = logs.LogGroup(self, "WanMONLambdaLogGroup",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create the Lambda function that monitors the website.
        fn = lambda_.Function(self, "WanMONLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="WanMONLambda.lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
            log_group=log_group
        )

        # Add a policy to the Lambda function's IAM role to allow it to push metrics to CloudWatch.
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"]
        ))

        # Create a second Lambda function to process alarm events and log to DynamoDB.
        log_fn = lambda_.Function(self, "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="AlarmLogger.lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
            environment={
                "TABLE_NAME": alarm_table.table_name
            }
        )

        # Grant the new Lambda function read/write permissions to the DynamoDB table.
        alarm_table.grant_read_write_data(log_fn)

        # Create an SNS topic for all alarms.
        alarm_topic = sns.Topic(self, "AlarmTopic")

        # Subscribe the alarm logger Lambda to the SNS topic.
        alarm_topic.add_subscription(subscriptions.LambdaSubscription(log_fn))

        # Trigger the monitoring Lambda every 5 min.
        rule = events.Rule(self, "WanMONLambdaSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )

        # Target the monitoring Lambda function for the rule.
        rule.add_target(targets.LambdaFunction(fn))

        # Availability Alarm: Triggers if the website returns a status code other than 200.
        availability_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="Availability",
            dimensions_map={"URL": "https://www.google.com"}
        )

        availability_alarm = cloudwatch_.Alarm(self, "AvailabilityAlarm",
            metric=availability_metric,
            threshold=1,
            comparison_operator=cloudwatch_.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when website availability is down (value is 0)."
        )

        # Latency Alarm: Triggers if the website response latency is over 30ms.
        latency_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="Latency",
            dimensions_map={"URL": "https://www.google.com"}
        )

        latency_alarm = cloudwatch_.Alarm(self, "LatencyAlarm",
            metric=latency_metric,
            threshold=200,
            comparison_operator=cloudwatch_.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when website latency is above 100ms."
        )

        # SSL Certificate Expiry Alarm: Triggers if the SSL certificate has 5 or fewer days remaining.
        ssl_expiry_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="SSLCertificateExpiryDays",
            dimensions_map={"URL": "www.google.com"}
        )

        ssl_expiry_alarm = cloudwatch_.Alarm(self, "SSLExpiryAlarm",
            metric=ssl_expiry_metric,
            threshold=5,
            comparison_operator=cloudwatch_.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when SSL certificate has 5 or fewer days remaining."
        )

        # Add alarm actions to send notifications to the SNS topic
        availability_alarm.add_alarm_action(actions.SnsAction(alarm_topic))
        latency_alarm.add_alarm_action(actions.SnsAction(alarm_topic))
        ssl_expiry_alarm.add_alarm_action(actions.SnsAction(alarm_topic))
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cw,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
import os
import json

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        METRIC_NAMESPACE = "NYTMonitor"

        # --- NEW: resolve repo-relative paths based on THIS file ---
        here = os.path.dirname(__file__)                 # .../week2prac/week2prac
        lambda_dir = os.path.normpath(os.path.join(here, "..", "lambda"))
        alarm_logger_dir = os.path.normpath(os.path.join(here, "..", "lambda_alarm_logger"))
        sites_file = os.path.normpath(os.path.join(lambda_dir, "sites.json"))

        # Lambda function to monitor websites
        monitor_fn = lambda_.Function(
            self,
            "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(lambda_dir),     # <-- FIXED
            timeout=Duration.seconds(30),
            environment={"METRIC_NAMESPACE": METRIC_NAMESPACE}
        )

        # IAM permissions for Lambda to publish metrics
        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}}
            )
        )

        # EventBridge: trigger Lambda every 5 minutes
        events.Rule(
            self,
            "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)]
        )

        # Load sites for dashboard and alarms (use file path above)
        with open(sites_file, "r", encoding="utf-8") as f:
            sites = json.load(f)

        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealthDashboard")
        widgets = []

        # SNS Topic for Alarm Notifications
        alarm_topic = sns.Topic(self, "WebMonitorAlarmTopic", topic_name="WebMonitorAlarms")
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

        # DynamoDB Table for Alarm Logging
        alarm_log_table = dynamodb.Table(
            self,
            "AlarmLogTable",
            table_name="WebMonitorAlarmLogs",
            partition_key=dynamodb.Attribute(name="alarm_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_class=dynamodb.TableClass.STANDARD
        )

        # Lambda to log alarms into DynamoDB
        log_lambda = lambda_.Function(
            self,
            "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=lambda_.Code.from_asset(alarm_logger_dir),   # <-- FIXED
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": alarm_log_table.table_name}
        )

        alarm_log_table.grant_write_data(log_lambda)
        alarm_topic.add_subscription(subs.LambdaSubscription(log_lambda))

        # Create metrics, dashboard widgets, and alarms per site
        for site in sites:
            avail_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Availability",
                dimensions_map={"Site": site},
                period=Duration.minutes(5),
                label=f"{site} Availability",
            )
            latency_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Latency",
                dimensions_map={"Site": site},
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,
                label=f"{site} Latency",
            )

            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency - {site}", left=[latency_metric], width=12, height=6))

            availability_alarm = cw.Alarm(
                self,
                f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} becomes unavailable"
            )
            availability_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(
                self,
                f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} latency is too high"
            )
            latency_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard.add_widgets(*widgets)

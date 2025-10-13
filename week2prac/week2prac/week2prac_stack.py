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

        # Resolve paths RELATIVE TO THIS FILE so CodeBuild can find assets
        here = os.path.dirname(__file__)                          # .../week2prac/week2prac
        lambda_dir = os.path.normpath(os.path.join(here, "..", "lambda"))
        alarm_logger_dir = os.path.normpath(os.path.join(here, "..", "lambda_alarm_logger"))
        sites_file = os.path.normpath(os.path.join(lambda_dir, "sites.json"))

        # Lambda: monitor websites
        monitor_fn = lambda_.Function(
            self,
            "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(lambda_dir),              # <-- points to week2prac/lambda
            timeout=Duration.seconds(30),
            environment={"METRIC_NAMESPACE": METRIC_NAMESPACE},
        )

        # IAM: allow Lambda to publish custom metrics
        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}},
            )
        )

        # EventBridge: run every 5 minutes
        events.Rule(
            self,
            "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)],
        )

        # Read sites list for dashboard & alarms
        with open(sites_file, "r", encoding="utf-8") as f:
            sites = json.load(f)

        # Dashboard
        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealthDashboard")

        # SNS Topic for alarm notifications
        alarm_topic = sns.Topic(self, "WebMonitorAlarmTopic", topic_name="WebMonitorAlarms")
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

        # DynamoDB for alarm logs
        alarm_log_table = dynamodb.Table(
            self,
            "AlarmLogTable",
            table_name="WebMonitorAlarmLogs",
            partition_key=dynamodb.Attribute(name="alarm_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_class=dynamodb.TableClass.STANDARD,
        )

        # Lambda to log alarms → DynamoDB
        log_lambda = lambda_.Function(
            self,
            "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=lambda_.Code.from_asset(alarm_logger_dir),        # <-- points to week2prac/lambda_alarm_logger
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": alarm_log_table.table_name},
        )
        alarm_log_table.grant_write_data(log_lambda)
        alarm_topic.add_subscription(subs.LambdaSubscription(log_lambda))

        # Widgets & Alarms
        widgets = []
        for site in sites:
            avail_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Availability",
                dimensions_map={"Site": site},
                period=Duration.minutes(5),
                statistic="Average",
                label=f"{site} Availability",
            )
            latency_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Latency",
                dimensions_map={"Site": site},
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,
                statistic="p95",
                label=f"{site} Latency (p95)",
            )

            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6))

            # Alarms → send to SNS
            cw.Alarm(
                self,
                f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} becomes unavailable",
            ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

            cw.Alarm(
                self,
                f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} latency is too high",
            ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard.add_widgets(*widgets)

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

        # ---------- FIX 1: robust path to lambda code (relative to this file) ----------
        code_path = os.path.join(os.path.dirname(__file__), "..", "lambda")

        monitor_fn = lambda_.Function(
            self, "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(code_path),
            timeout=Duration.seconds(30),
            environment={"METRIC_NAMESPACE": METRIC_NAMESPACE}
        )

        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}},
            )
        )

        events.Rule(
            self, "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)],
        )

        # Load sites for dashboard/alarms
        sites_file = os.path.join(code_path, "sites.json")  # use same base as function code
        with open(sites_file, "r", encoding="utf-8") as f:
            sites = json.load(f)

        # ---------- FIX 2: unique names per stage/stack ----------
        stack_suffix = f"{Stack.of(self).stack_name}"

        dashboard = cw.Dashboard(
            self, "WebHealthDashboard",
            dashboard_name=f"{stack_suffix}-WebHealthDashboard",
        )
        # Optional: clean up on stack delete in non-prod
        dashboard.apply_removal_policy(RemovalPolicy.DESTROY)

        # SNS for alarm notifications (unique per stage)
        alarm_topic = sns.Topic(
            self, "WebMonitorAlarmTopic",
            topic_name=f"{stack_suffix}-WebMonitorAlarms",
        )
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

        # DynamoDB for alarm logging (unique per stage)
        alarm_log_table = dynamodb.Table(
            self, "AlarmLogTable",
            table_name=f"{stack_suffix}-AlarmLogs",
            partition_key=dynamodb.Attribute(name="alarm_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Alarm logger lambda (keep path relative)
        logger_code_path = os.path.join(os.path.dirname(__file__), "..", "lambda_alarm_logger")
        log_lambda = lambda_.Function(
            self, "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=lambda_.Code.from_asset(logger_code_path),
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": alarm_log_table.table_name},
        )
        alarm_log_table.grant_write_data(log_lambda)
        alarm_topic.add_subscription(subs.LambdaSubscription(log_lambda))

        # Metrics, dashboard widgets, alarms
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
                statistic="p95",
                unit=cw.Unit.MILLISECONDS,
                label=f"{site} Latency (p95 ms)",
            )

            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6))

            availability_alarm = cw.Alarm(
                self, f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} becomes unavailable",
            )
            availability_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(
                self, f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} latency is too high",
            )
            latency_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard.add_widgets(*widgets)

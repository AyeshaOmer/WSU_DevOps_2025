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
from pathlib import Path
import json

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        METRIC_NAMESPACE = "NYTMonitor"

        # --- Paths (relative to this file) ---
        base_dir = Path(__file__).resolve().parent
        lambda_dir = str(base_dir / "lambda")
        alarm_logger_dir = str(base_dir / "lambda_alarm_logger")
        sites_file = base_dir / "lambda" / "sites.json"

        # --- Lambda: site monitor ---
        monitor_fn = lambda_.Function(
            self,
            "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(lambda_dir),
            timeout=Duration.seconds(30),
            environment={"METRIC_NAMESPACE": METRIC_NAMESPACE},
        )

        # Allow Lambda to publish custom metrics to CloudWatch
        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}},
            )
        )

        # Run every 5 minutes
        events.Rule(
            self,
            "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)],
        )

        # --- Load sites for dashboard & alarms (synth-time read is fine) ---
        with sites_file.open("r", encoding="utf-8") as f:
            sites = json.load(f)

        # --- Dashboard ---
        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealthDashboard")
        widgets: list[cw.IWidget] = []

        # --- SNS topic for notifications ---
        alarm_topic = sns.Topic(self, "WebMonitorAlarmTopic", topic_name="WebMonitorAlarms")
        # Email subscription (user must confirm email)
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

        # --- DynamoDB table for alarm logging (Week 6–7) ---
        alarm_log_table = dynamodb.Table(
            self,
            "AlarmLogTable",
            table_name="WebMonitorAlarmLogs",
            partition_key=dynamodb.Attribute(name="alarm_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_class=dynamodb.TableClass.STANDARD,
        )
        
        alarm_log_table.apply_removal_policy(RemovalPolicy.DESTROY)

        # --- Lambda: write alarm notifications to DynamoDB ---
        log_lambda = lambda_.Function(
            self,
            "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=lambda_.Code.from_asset(alarm_logger_dir),
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": alarm_log_table.table_name},
        )
        alarm_log_table.grant_write_data(log_lambda)

        # Subscribe logging Lambda to the SNS topic
        alarm_topic.add_subscription(subs.LambdaSubscription(log_lambda))

        # --- Metrics, widgets, and alarms per site ---
        for site in sites:
            # Metrics
            avail_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Availability",
                dimensions_map={"Site": site},
                statistic="Average",            
                period=Duration.minutes(5),
                label=f"{site} Availability",
            )
            latency_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Latency",
                dimensions_map={"Site": site},
                statistic="p95",                   # 95th percentile
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,       
                label=f"{site} Latency (p95 ms)",
            )

            # Dashboard widgets
            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6))

            # Alarms (+ SNS action)
            availability_alarm = cw.Alarm(
                self,
                f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1, 
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} becomes unavailable",
            )
            availability_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(
                self,
                f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,  
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} latency is too high",
            )
            latency_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard.add_widgets(*widgets)

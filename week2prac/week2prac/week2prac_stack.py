from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cw,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions,
)
from constructs import Construct
import os
import json

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        METRIC_NAMESPACE = "NYTMonitor"

        # Lambda function to monitor websites
        monitor_fn = lambda_.Function(self, "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), "lambda")),
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
        events.Rule(self, "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)]
        )

        # Load sites for dashboard and alarms
        sites_file = os.path.join(os.getcwd(), "lambda", "sites.json")
        with open(sites_file, "r", encoding="utf-8") as f:
            sites = json.load(f)

        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealthDashboard")
        widgets = []

     
        # SNS topic for alarm notifications
        alarm_topic = sns.Topic(self, "WebMonitorAlarmTopic", topic_name="WebMonitorAlarms")

        #  Subscribe email 
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

       
        # Loop through sites to create metrics, dashboard widgets, and alarms
        for site in sites:
            # Metrics (defined once per site)
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
                statistic="p95",
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,
                label=f"{site} Latency (p95 ms)",
            )

            # Dashboard widgets
            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6))

            # -------------------------
            # CloudWatch Alarms with SNS
            # -------------------------
            availability_alarm = cw.Alarm(self, f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} becomes unavailable"
            )
            availability_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(self, f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Alarm if {site} latency is too high"
            )
            latency_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard.add_widgets(*widgets)


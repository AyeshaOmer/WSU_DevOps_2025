from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cw,
)
from constructs import Construct
import os
import json

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define the namespace for CloudWatch metrics
        METRIC_NAMESPACE = "NYTMonitor"  # You can change this to a custom namespace if needed

        # Lambda function
        monitor_fn = lambda_.Function(self, "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), "lambda")),
            timeout=Duration.seconds(30),  # Increased timeout to allow enough time for site crawling
            environment={
                "METRIC_NAMESPACE": METRIC_NAMESPACE  # Pass the namespace to Lambda via environment variable
            }
        )

        # Allow Lambda to publish custom metrics to CloudWatch
        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],  # Allow all resources; you could specify resources if needed
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}}  # Restrict access to the specified namespace
            )
        )

        # EventBridge rule to trigger Lambda every 5 minutes
        events.Rule(self, "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),  # Runs every 5 minutes
            targets=[targets.LambdaFunction(monitor_fn)]
        )

        # ---- CloudWatch Dashboard ----
        # Read the same sites list at synth-time to build widgets
        sites_file = os.path.join(os.getcwd(), "lambda", "sites.json")
        with open(sites_file, "r", encoding="utf-8") as f:
            sites = json.load(f)

        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealthDashboard")

        # For each site, show Availability & Latency
        rows = []
        for site in sites:
            avail_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Availability",
                dimensions_map={"Site": site},
                statistic="Average",
                period=Duration.minutes(5),
            )
            latency_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Latency",
                dimensions_map={"Site": site},
                statistic="p95",
                period=Duration.minutes(5),
            )

            rows.append([
                cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6),
                cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6),
            ])

        # Optionally, a status code widget that filters by dimension "Code"
        status_5xx = cw.Metric(
            namespace=METRIC_NAMESPACE,
            metric_name="StatusCode",
            dimensions_map={"Code": "500"},  # no Site dimension → totals across all sites
            statistic="Sum",
            period=Duration.minutes(5),
        )

        dashboard.add_widgets(*[w for row in rows for w in row])
        dashboard.add_widgets(cw.GraphWidget(title="5xx Errors (Sum)", left=[status_5xx], width=24, height=6))

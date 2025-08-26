"This file is for deploy and call built in services/components in lambda"

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    Duration
)
from constructs import Construct

websites = [
        {"name": "Google", "url": "https://www.google.com"},
        {"name": "Facebook", "url": "https://www.facebook.com"},
        {"name": "YouTube", "url": "https://www.youtube.com"}
    ]

metrix = ["latency", "availability", "status_code"]

THRESHOLD_METRICS = {
    "latency": 100,
    "availability": 1,
    "status_code": 200
}

class DanStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Add trigger interval time
        self.trigger_interval = Duration.minutes(5)

        # Handle Lambda function with calculation
        web_crawler_lambda = _lambda.Function(
            self, "WebCrawlerFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="Metrix.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.minutes(5),
            memory_size=256
        )

        # Create EventBridge rule and add Lambda as target (runs every trigger_interval)
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.rate(self.trigger_interval),
        )
        rule.add_target(targets.LambdaFunction(web_crawler_lambda))

        # Add permissions for CloudWatch
        web_crawler_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"]
            )
        )

        
        for site in websites:
            # Add metrix for website and alarm
            latency_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="Latency",
                dimensions_map={"Website": site["name"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            availability_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="Availability",
                dimensions_map={"Website": site["name"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            status_code_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="StatusCode",
                dimensions_map={"Website": site["name"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            # Add alarm for each metrix
            cloudwatch.Alarm(
                self, f"{site['name']}LatencyAlarm",
                metric=latency_metrix,
                threshold=THRESHOLD_METRICS["latency"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
            cloudwatch.Alarm(
                self, f"{site['name']}AvailabilityAlarm",
                metric=availability_metrix,
                threshold=THRESHOLD_METRICS["availability"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
            )
            # Status code "not equal to expected" is implemented as two alarms:
            # one for status > expected and one for status < expected.
            cloudwatch.Alarm(
                self, f"{site['name']}StatusCodeHighAlarm",
                metric=status_code_metrix,
                threshold=THRESHOLD_METRICS["status_code"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
            cloudwatch.Alarm(
                self, f"{site['name']}StatusCodeLowAlarm",
                metric=status_code_metrix,
                threshold=THRESHOLD_METRICS["status_code"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
            )
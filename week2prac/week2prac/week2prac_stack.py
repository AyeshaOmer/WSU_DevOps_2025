from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct
import os

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Lambda function
        monitor_fn = lambda_.Function(self, "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), "lambda")),
            timeout=Duration.seconds(10),
        )

        # EventBridge rule to run every 5 minutes
        events.Rule(self, "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)]
        )

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

class DanStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        web_crawler_lambda = _lambda.Function(
            self, "WebCrawlerFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="Metrix.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.minutes(5),
            memory_size=256
        )
        web_crawler_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"]
            )
        )


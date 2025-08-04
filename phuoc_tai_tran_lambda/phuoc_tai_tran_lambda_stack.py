from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    # aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class PhuocTaiTranLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.Function( 
        self, "PhuocTaiTranLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="index.handler",
        code = _lambda.Code.from_asset("lib/lambda-handler"),
        )

        endpoint = apigw.LambdaRestApi(
        self, "ApiGwEndpoint",
        handler=fn,
        rest_api_name="PhuocTaiTranLambdaAPI",
        )

        # Schedule the Lambda function to run every 15 minutes (can be deleted as cloudwatch event has a trigger already)
        rule = events.Rule(
            self, "ScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            targets=[targets.LambdaFunction(fn)]
        )

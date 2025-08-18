from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    # aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class PhuocTaiTranLambdaStack(Stack):

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.Function( 
        self, "PhuocTaiTranLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="ObtainMetrics.handler",
        code = _lambda.Code.from_asset("lib/lambda-handler/Module"),
        )

        fn_hello = _lambda.Function(
        self, "PhuocTaiTranHelloLambda",
        runtime=_lambda.Runtime.PYTHON_3_12,
        handler="helloLambda.handler",
        code=_lambda.Code.from_asset("lib/lambda-handler/Module"),
        )

        fn_log_group = fn.log_group
        fn_log_group.apply_removal_policy(RemovalPolicy.DESTROY)
        
        fn_log_group_2 = fn_hello.log_group
        fn_log_group_2.apply_removal_policy(RemovalPolicy.DESTROY)

        endpoint = apigw.LambdaRestApi(
        self, "ApiGwEndpoint",
        handler=fn,
        rest_api_name="PhuocTaiTranLambdaAPI",
        )

        # Schedule the Lambda function to run every 15 minutes (can be deleted as cloudwatch event has a trigger already)
        rule = events.Rule(
            self, "ScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(fn),
                     targets.LambdaFunction(fn_hello)]
        )


from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as lambda_,
    aws_logs as logs, RemovalPolicy
)
from constructs import Construct

class BraydenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        fn = lambda_.Function(self, "WanMONLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="WanMONLambda.lambda_handler",    
            code=lambda_.Code.from_asset("./modules"),
            log_removal_policy=RemovalPolicy.DESTROY
        )   

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    RemovalPolicy
)
from constructs import Construct

class BraydenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        log_group = logs.LogGroup(self, "WanMONLambdaLogGroup",
            removal_policy=RemovalPolicy.DESTROY
        )
        fn = lambda_.Function(self, "WanMONLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="WanMONLambda.lambda_handler",    
            code=lambda_.Code.from_asset("./modules"),
            log_group=log_group
        )   

     # Triger lamda every 5 min
        rule = events.Rule(self, "WanMONLambdaSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )

        # Target the lamdba function for the rule
        rule.add_target(targets.LambdaFunction(fn))
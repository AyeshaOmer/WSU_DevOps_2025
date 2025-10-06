from aws_cdk import Stage
from constructs import Construct
from .app_stack import AppStack

# Define the stage
class MyAppStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Add both stacks to the stage
        AppStack(self, "AppStack")

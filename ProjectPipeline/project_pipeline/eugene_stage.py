# https://docs.aws.amazon.com/cdk/v2/guide/stages.html

from aws_cdk import Stage
from constructs import Construct
from .eugene_stack import EugeneStack

# Define the stage
class MyAppStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.Stage = EugeneStack(self, "EugeneApplicationStack")
        # EugeneStack(self, f"EugeneApplicationStack-{id}")
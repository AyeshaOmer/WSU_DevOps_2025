from aws_cdk import (
    Stage,  
)
from constructs import Construct

from ayesha_pipelines.ash_stack import AshStack

class MypipelineStage(Stage):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs) 
        self.stage=AshStack(self,"AshApplicationStack")
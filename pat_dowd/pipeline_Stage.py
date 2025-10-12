from aws_cdk import (
    Stage,  
)
from constructs import Construct

from pat_dowd.pat_dowd_stack import PatDowdStack

class MypipelineStage(Stage):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs) 
        self.stage=PatDowdStack(self,"PatApplicationStack")
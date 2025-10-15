from aws_cdk import (
    Stage,  
)
from constructs import Construct

from .phuoc_tai_tran_lambda_stack import PhuocTaiTranLambdaStack

class MypipelineStage(Stage):
    
    def __init__(self, scope: Construct, construct_id: str, stage_name: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Pass the stage name to the lambda stack to make resource names unique
        self.stage=PhuocTaiTranLambdaStack(self,"PhuocTaiTranApplicationStack", stage_name=stage_name or construct_id)
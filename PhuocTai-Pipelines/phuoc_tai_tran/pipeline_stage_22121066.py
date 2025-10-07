from aws_cdk import (
    Stage,  
)
from constructs import Construct

from .phuoc_tai_tran_lambda_stack import PhuocTaiTranLambdaStack

class MypipelineStage(Stage):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.stage=PhuocTaiTranLambdaStack(self,"PhuocTaiTranApplicationStack")
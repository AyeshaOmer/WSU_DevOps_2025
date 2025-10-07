from aws_cdk import Stage
from constructs import Construct
import AppStack

class PhuocTaiTranStage(Stage):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Define the stacks in this stage
        self.Stage = AppStack(self, "AppStack")



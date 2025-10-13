from aws_cdk import Stage
from constructs import Construct
from .week2prac_stack import Week2PracStack

class AppStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        Week2PracStack(self, "WebHealthStack")

from aws_cdk import Stage
from constructs import Construct

from week2prac_stack import Week2PracStack

class AppStage(Stage):
    """
    A deployable unit that includes your web-health monitoring stack.
    The pipeline adds this Stage 3 times (Beta, Gamma, Prod).
    """
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        Week2PracStack(self, "WebHealthStack")

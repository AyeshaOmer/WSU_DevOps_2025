from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,
    pipelines as pipelines,
    Stage
)
from constructs import Construct
from DangQuocToan.dang_quoc_toan.dang_quoc_toan_stack import DangQuocToanStack
from aws_cdk.aws_codepipeline_actions import GitHubTrigger
class ThomasStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.git_hub(
                repo_string="ThomasToan/WSU_DevOps_2025",
                branch="main",
                action_name="WSU_DevOps_2025",
                authentication = SecretValue.secrets_manager("mytoken"),
                trigger=GitHubTrigger.POLL
)
        
        synth = pipelines.ShellStep(
            "BuildCommands",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "pip install -r Thomas/requirements.txt",
                "cd Thomas",
                "cdk synth",
            ],
            primary_output_directory="Thomas/cdk.out",
        )
        
        pipeline = pipelines.CodePipeline(self, "ThomasPipeline", synth=synth)

        beta_stage = pipeline.add_stage(BetaStage(self, "Beta"))
        gamma_stage = pipeline.add_stage(GammaStage(self, "Gamma"))
        prod_stage = pipeline.add_stage(ProdStage(self, "Prod"))


        beta_stage.add_post(
             pipelines.ShellStep("BetaTests",
                                 commands=["pytest tests/beta"]
         )                               
     )        

        gamma_stage.add_post(
            pipelines.ShellStep("GammaTests",
                                commands=["pytest tests/gamma"]        
        )
        )

        prod_stage.add_post(                 
            pipelines.ShellStep("ProdTests",
                                commands=["pytest tests/prod"]
        )
        )
        

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "ThomasQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
class BetaStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "BetaWebHealth")

class GammaStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "GammaWebHealth")

class ProdStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "ProdWebHealth")

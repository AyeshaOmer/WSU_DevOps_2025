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

class ThomasStack(Stack): # define a CDK Stack named ThomasStack
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

## Define source: pull from GitHub repo
## https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html#aws_cdk.pipelines.CodePipelineSource.git_hub
        source = pipelines.CodePipelineSource.git_hub(
                repo_string="ThomasToan/WSU_DevOps_2025", # GitHub repo owner/name
                branch="main", # Branch to watch
                action_name="WSU_DevOps_2025", # Action name show in pipeline
                authentication = SecretValue.secrets_manager("mytoken"), # GitHub token stored in Secrets Manger
                trigger=GitHubTrigger.POLL # pipline check repo preiodically (polling)
)
        
## Synthesis step: build environment
# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/ShellStep.html
        synth = pipelines.ShellStep(
            "BuildCommands", # Step name
            input=source, # Uses the GitHub source defined above
            commands=[
                "npm install -g aws-cdk",
                "pip install -r Thomas/requirements.txt",
                # Run unit tests before synth so failures stop the pipeline early
                "export PYTHONPATH=.",
                "pytest DangQuocToan/tests/unit -q",
                "pytest Thomas/tests/unit -q",
                "cd Thomas", # Change into the Thomas app folder
                "cdk synth -c enable_code_deploy=false", # Generate templates (disable CodeDeploy in CI)
            ],
            primary_output_directory="Thomas/cdk.out", # Tell pipeline where synthesized files go
        )
        
## Define CodePipeline itself
## https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipeline.html
        pipeline = pipelines.CodePipeline(self, "ThomasPipeline", synth=synth)

## Add pipeline stages
## https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipeline.html#aws_cdk.pipelines.CodePipeline.add_stage
        beta_stage = pipeline.add_stage(BetaStage(self, "Beta"))
        gamma_stage = pipeline.add_stage(GammaStage(self, "Gamma"))

        # New Staging stage between Gamma and Prod
        staging_stage = pipeline.add_stage(StagingStage(self, "Staging"))

        # Require a manual approval before deploying to Prod
        prod_stage = pipeline.add_stage(
            ProdStage(self, "Prod"),
            pre=[pipelines.ManualApprovalStep("ApproveBeforeProd")]
        )

## Add post-deployment tests steps for Beta stage
## https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/StageDeployment.html#aws_cdk.pipelines.StageDeployment.add_post
        beta_stage.add_post(
            pipelines.ShellStep(
                "BetaTests", # Step name
                commands=[
                    "pip install -r Thomas/requirements.txt",
                    "cd Thomas",
                    "pytest tests/beta",
                ],
            )
        )        

## Add post-deployment tests steps for Gamma stage
        gamma_stage.add_post(
            pipelines.ShellStep(
                "GammaTests",
                commands=[
                    "pip install -r Thomas/requirements.txt",
                    "cd Thomas",
                    "pytest tests/gamma",
                ],
            )
        )

        # Add post-deployment tests steps for Staging stage
        staging_stage.add_post(
            pipelines.ShellStep(
                "StagingTests",
                commands=[
                    "pip install -r Thomas/requirements.txt",
                    "cd Thomas",
                    "pytest tests/staging",
                ],
            )
        )

## Add post-deployment tests steps for Prod stage
        prod_stage.add_post(                 
            pipelines.ShellStep(
                "ProdTests",
                commands=[
                    "pip install -r Thomas/requirements.txt",
                    "cd Thomas",
                    "pytest tests/prod",
                ],
            )
        )
        

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "ThomasQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

## Stage definitions
##https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/Stage.html
class BetaStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "BetaWebHealth") # Deploys WebHealth monitoring app into Beta

class GammaStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "GammaWebHealth") # Deploys WebHealth monitoring app into Gamma

class ProdStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "ProdWebHealth") # Deploys WebHealth monitoring app into Prod

class StagingStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        DangQuocToanStack(self, "StagingWebHealth") # Deploys WebHealth monitoring app into Staging

from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_iam as iam,
    Environment,
)
from constructs import Construct
from .app_stage import AppStage  # your deployable app with Lambda, etc.

class WebMonitorPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Define the synth step
        synth_step = pipelines.ShellStep("Synth",
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install -r requirements.txt"
            ],
            commands=[
                "cdk synth"
            ]
        )

        pipeline = pipelines.CodePipeline(self, "WebMonitorPipeline",
            synth=synth_step,
            pipeline_name="WebMonitorMultiStagePipeline"
        )

        # Beta Stage
        beta_stage = pipeline.add_stage(AppStage(self, "Beta", env=Environment(region="ap-southeast-2")))

        beta_stage.add_post(
            pipelines.ShellStep("BetaSmokeTest", commands=["echo Running Beta tests", "curl https://example.com"])
        )

        # Gamma Stage 
        gamma_stage = pipeline.add_stage(AppStage(self, "Gamma", env=Environment(region="ap-southeast-2")))

        gamma_stage.add_pre(
            pipelines.ManualApprovalStep("ApproveGamma", comment="Approve Gamma rollout?")
        )
        gamma_stage.add_post(
            pipelines.ShellStep("GammaHealthCheck", commands=["echo Gamma passed smoke tests."])
        )

        # Prod Stage
        prod_stage = pipeline.add_stage(AppStage(self, "Prod", env=Environment(region="ap-southeast-2")))

        prod_stage.add_pre(
            pipelines.ManualApprovalStep("FinalApproval", comment="Approve Prod Deployment?")
        )
        prod_stage.add_post(
            pipelines.ShellStep("ProdPostCheck", commands=["echo Prod verification."])
        )

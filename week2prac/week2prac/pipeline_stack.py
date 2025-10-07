# Multi-stage CI/CD pipeline using CDK Pipelines (Beta → Gamma → Prod)
from aws_cdk import (
    Stack,
    Environment,
    pipelines as pipelines,  # CDK Pipelines
)
from constructs import Construct
from .app_stage import AppStage


class WebMonitorPipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        repo_string: str,
        branch: str,
        codestar_connection_arn: str,
        deploy_region: str = "ap-southeast-2",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Source from your GitHub (via CodeStar Connections) ---
        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=codestar_connection_arn,
        )

        # --- Synth step (NOTE the cd into week2prac) ---
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install --upgrade pip",
                #  install requirements from the subfolder
                "python -m pip install -r week2prac/requirements.txt",
            ],
            commands=[
                #  synth the app located in the subfolder 
                "cdk synth --app 'python week2prac/app.py'",
                # (alternative if your image doesn’t have cdk on PATH)
                # "npx cdk synth --app 'python week2prac/app.py'",
            ],
                    # (Optional) help the pipeline find the assembly if it complains:
                    # primary_output_directory="week2prac/cdk.out",
                )

        pipeline = pipelines.CodePipeline(
            self,
            "WebMonitorPipeline",
            pipeline_name="WebMonitorMultiStagePipeline",
            synth=synth_step,
        )

        stage_env = Environment(region=deploy_region)

        # Stages
        beta = pipeline.add_stage(AppStage(self, "Beta", env=stage_env))
        beta.add_post(
            pipelines.ShellStep("BetaSmokeTests", commands=[
                'echo "Running Beta smoke tests..."',
                'python -c "print(\'ok\')"',
            ])
        )

        gamma = pipeline.add_stage(AppStage(self, "Gamma", env=stage_env))
        gamma.add_pre(
            pipelines.ManualApprovalStep(
                "ApproveGamma",
                comment="Review Beta before promoting to Gamma.",
            )
        )
        gamma.add_post(
            pipelines.ShellStep("GammaHealthChecks", commands=[
                'echo "Running Gamma health checks..."',
                'python -c "print(\'gamma checks ok\')"',
            ])
        )

        prod = pipeline.add_stage(AppStage(self, "Prod", env=stage_env))
        prod.add_pre(
            pipelines.ManualApprovalStep(
                "FinalApproval",
                comment="Final sign-off to deploy to Prod.",
            )
        )
        prod.add_post(
            pipelines.ShellStep("ProdVerification", commands=[
                'echo "Verifying Prod..."',
                'python -c "print(\'prod verification ok\')"',
            ])
        )

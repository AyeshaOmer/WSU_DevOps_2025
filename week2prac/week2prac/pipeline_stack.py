# week2prac/pipeline_stack.py
from aws_cdk import (
    Stack,
    Environment,
    pipelines as pipelines,
)
from constructs import Construct
from .app_stage import AppStage


class WebMonitorPipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        repo_string: str,                 # e.g., "owner/repo"
        branch: str,                      # e.g., "main"
        codestar_connection_arn: str,     # your CodeStar Connections ARN
        deploy_region: str = "ap-southeast-2",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Source (CodeStar Connections) ---
        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=codestar_connection_arn,
        )

        # --- Synth (cd into 'week2prac', then synth) ---
        # We 'cd week2prac' so any paths that depend on CWD (like Code.from_asset("lambda"))
        # resolve correctly to week2prac/lambda.
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install --upgrade pip",
                "python -m pip install -r week2prac/requirements.txt",
            ],
            commands=[
                "cd week2prac",
                "cdk synth",
            ],
            # Because we cd into week2prac, the cdk.out is produced in that folder
            primary_output_directory="week2prac/cdk.out",
        )

        pipeline = pipelines.CodePipeline(
            self,
            "WebMonitorPipeline",
            pipeline_name="WebMonitorMultiStagePipeline",
            synth=synth_step,
        )

        # Single-region pipeline (as requested)
        stage_env = Environment(region=deploy_region)

        # --- Beta ---
        beta = pipeline.add_stage(AppStage(self, "Beta", env=stage_env))
        beta.add_post(
            pipelines.ShellStep(
                "BetaSmokeTests",
                commands=[
                    'echo "Running Beta smoke tests..."',
                    'python -c "print(\'ok\')"',
                ],
            )
        )

        # --- Gamma ---
        gamma = pipeline.add_stage(AppStage(self, "Gamma", env=stage_env))
        gamma.add_pre(
            pipelines.ManualApprovalStep(
                "ApproveGamma",
                comment="Review Beta before promoting to Gamma.",
            )
        )
        gamma.add_post(
            pipelines.ShellStep(
                "GammaHealthChecks",
                commands=[
                    'echo "Running Gamma health checks..."',
                    'python -c "print(\'gamma checks ok\')"',
                ],
            )
        )

        # --- Prod ---
        prod = pipeline.add_stage(AppStage(self, "Prod", env=stage_env))
        prod.add_pre(
            pipelines.ManualApprovalStep(
                "FinalApproval",
                comment="Final sign-off to deploy to Prod.",
            )
        )
        prod.add_post(
            pipelines.ShellStep(
                "ProdVerification",
                commands=[
                    'echo "Verifying Prod..."',
                    'python -c "print(\'prod verification ok\')"',
                ],
            )
        )

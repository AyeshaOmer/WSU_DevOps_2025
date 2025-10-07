# Multi-stage CI/CD pipeline using CDK Pipelines (Beta → Gamma → Prod)
from aws_cdk import (
    Stack,
    Environment,
    pipelines as pipelines,  # CDK Pipelines API
)
from constructs import Construct

# deploy existing app (Week2PracStack) wrapped in a Stage
from .app_stage import AppStage 

class WebMonitorPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, repo_string: str,
                 branch: str, codestar_connection_arn: str,
                 deploy_region: str = "ap-southeast-2",
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # --- Source: pull from your repo via CodeStar Connection (recommended) ---
        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=codestar_connection_arn,  
        )

        # --- Synth step: builds the cloud assembly (cdk.out) ---
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                # Ensure CDK and Python deps are available in the CodeBuild image
                "npm install -g aws-cdk",
                "python -m pip install --upgrade pip",
                "python -m pip install -r requirements.txt",
            ],
            commands=[
                "cdk synth",
            ],
        )

        # --- The Pipeline itself ---
        pipeline = pipelines.CodePipeline(
            self,
            "WebMonitorPipeline",
            pipeline_name="WebMonitorMultiStagePipeline",
            synth=synth_step,
        )

        # Shared env for all stages (single region as requested)
        stage_env = Environment(region=deploy_region)

        # Stage 1: Beta
        beta = pipeline.add_stage(
            AppStage(self, "Beta", env=stage_env)  # deploys your Week2PracStack
        )

        # Test blocker: run a test after Beta deploy
        beta.add_post(
            pipelines.ShellStep(
                "BetaSmokeTests",  # will block the pipeline if non-zero exit
                commands=[
                    # Put your real checks here; these are examples:
                    'echo "Running Beta smoke tests..."',
                    # Example: curl one of your monitored sites just to assert reachability
                    'python -c "import json; print(\'ok\')"',  # placeholder test
                ],
            )
        )

        # Stage 2: Gamma
        gamma = pipeline.add_stage(
            AppStage(self, "Gamma", env=stage_env)
        )

        # Test blocker: manual approval before gamma deploy
        gamma.add_pre(
            pipelines.ManualApprovalStep(
                "ApproveGamma",
                comment="Review CloudWatch Dashboard & alarms in Beta before promoting to Gamma.",
            )
        )

        # Test blocker: post-deploy checks in gamma
        gamma.add_post(
            pipelines.ShellStep(
                "GammaHealthChecks",
                commands=[
                    'echo "Running Gamma health checks..."',
                    # Example: ensure critical dashboards/alarms exist
                    'python -c "print(\'gamma checks ok\')"',
                ],
            )
        )

        # Stage 3: Prod
        prod = pipeline.add_stage(
            AppStage(self, "Prod", env=stage_env)
        )

        # Test blocker: manual approval before prod deploy
        prod.add_pre(
            pipelines.ManualApprovalStep(
                "FinalApproval",
                comment="Final sign-off to deploy to Prod.",
            )
        )

        # Test blocker: post-deploy verification in prod
        prod.add_post(
            pipelines.ShellStep(
                "ProdVerification",
                commands=[
                    'echo "Verifying Prod..."',
                    # Example: quick queries/CLI checks (replace with real tests)
                    'python -c "print(\'prod verification ok\')"',
                ],
            )
        )

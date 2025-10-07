# Multi-stage CI/CD pipeline using CDK Pipelines (Beta → Gamma → Prod)
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
        repo_string: str,
        branch: str,
        codestar_connection_arn: str,
        deploy_region: str = "ap-southeast-2",
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # --- Source: pull from your repo ---
        source = pipelines.CodePipelineSource.connection(
            repo_string,                  
            branch,                       # "main"
            connection_arn=codestar_connection_arn,
        )

        # --- Synth step: builds the cloud assembly (cdk.out) ---
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install --upgrade pip",
            ],
            commands=[
                # Show layout to help debugging in CodeBuild logs
                "echo 'PWD:' && pwd",
                "echo 'Top-level files:' && ls -la",
                "echo 'Top-level tree:' && find . -maxdepth 2 -type f -print",

                # Try repo root first, then week2prac/
                "if [ -f requirements.txt ] && [ -f cdk.json ]; then "
                "  echo '== Using repo root for CDK app =='; "
                "  python -m pip install -r requirements.txt; "
                "  cdk synth -o cdk.out; "
                "elif [ -f week2prac/requirements.txt ] && [ -f week2prac/cdk.json ]; then "
                "  echo '== Using week2prac/ for CDK app =='; "
                "  python -m pip install -r week2prac/requirements.txt; "
                "  cd week2prac && cdk synth -o ../cdk.out; "
                "else "
                "  echo 'ERROR: Could not find requirements.txt and cdk.json at repo root or week2prac/'; "
                "  exit 1; "
                "fi",
            ],
            # Force the CDK output directory so the pipeline always finds it
            primary_output_directory="cdk.out",
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
        beta = pipeline.add_stage(AppStage(self, "Beta", env=stage_env))

        # Test blocker: run a test after Beta deploy
        beta.add_post(
            pipelines.ShellStep(
                "BetaSmokeTests",
                commands=[
                    'echo "Running Beta smoke tests..."',
                    'python - <<PY\nprint("ok")\nPY',
                ],
            )
        )

        # Stage 2: Gamma
        gamma = pipeline.add_stage(AppStage(self, "Gamma", env=stage_env))

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
                    'python - <<PY\nprint("gamma checks ok")\nPY',
                ],
            )
        )

        # Stage 3: Prod
        prod = pipeline.add_stage(AppStage(self, "Prod", env=stage_env))

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
                    'python - <<PY\nprint("prod verification ok")\nPY',
                ],
            )
        )

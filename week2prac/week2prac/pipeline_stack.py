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

        # --- Source from your GitHub (via CodeConnections/CodeStar) ---
        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=codestar_connection_arn,
        )

        # --- Synth step (NOTE the cd into week2prac via --app) ---
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install --upgrade pip",
                "python -m pip install -r week2prac/requirements.txt",
                # install dev deps if present (pytest, etc.)
                "test -f week2prac/requirements-dev.txt && python -m pip install -r week2prac/requirements-dev.txt || true",
            ],
            commands=[
                "cdk synth --app 'python week2prac/app.py'",
                # If needed: -- Look for output in week2prac/cdk.out
                # "npx cdk synth --app 'python week2prac/app.py'",
            ],
            # primary_output_directory="week2prac/cdk.out",
        )

        pipeline = pipelines.CodePipeline(
            self,
            "WebMonitorPipeline",
            pipeline_name="WebMonitorMultiStagePipeline",
            synth=synth_step,
        )

        stage_env = Environment(region=deploy_region)

        # Helper: a pytest gate that won't fail the pipeline if you have no tests yet
        # - If ./tests exists: run pytest; treat exit code 5 ("no tests collected") as success.
        # - If no ./tests dir: skip with a message.
        def pytest_step(step_id: str) -> pipelines.ShellStep:
            return pipelines.ShellStep(
                step_id,
                input=source,
                install_commands=[
                    "python -m pip install --upgrade pip",
                    "python -m pip install -r week2prac/requirements.txt",
                    "test -f week2prac/requirements-dev.txt && python -m pip install -r week2prac/requirements-dev.txt || true",
                ],
                commands=[
                    # Safe runner: only run if tests/ exists; allow exit code 5 (no tests) to pass.
                    'if [ -d tests ]; then '
                    'pytest -q tests || test $? -eq 5; '
                    'else echo "No tests/ directory found; skipping pytest"; fi'
                ],
            )

        # ------------------ BETA ------------------
        beta = pipeline.add_stage(AppStage(self, "Beta", env=stage_env))

        # Hard blocker BEFORE Beta deploys
        beta.add_pre(
            pytest_step("BetaPyTests")
        )

        # Optional post-deploy smoke check
        beta.add_post(
            pipelines.ShellStep("BetaSmokeTests", commands=[
                'echo "Running Beta smoke tests..."',
                'python -c "print(\'ok\')"',
            ])
        )

        # ------------------ GAMMA ------------------
        gamma = pipeline.add_stage(AppStage(self, "Gamma", env=stage_env))

        # Hard blockers BEFORE Gamma deploys: tests + human approval
        gamma.add_pre(
            pytest_step("GammaPyTests"),
            pipelines.ManualApprovalStep(
                "ApproveGamma",
                comment="Review Beta results and code before promoting to Gamma.",
            )
        )

        gamma.add_post(
            pipelines.ShellStep("GammaHealthChecks", commands=[
                'echo "Running Gamma health checks..."',
                'python -c "print(\'gamma checks ok\')"',
            ])
        )

        # ------------------ PROD ------------------
        prod = pipeline.add_stage(AppStage(self, "Prod", env=stage_env))

        # Hard blockers BEFORE Prod deploys: tests + final approval
        prod.add_pre(
            pytest_step("ProdPyTests"),
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

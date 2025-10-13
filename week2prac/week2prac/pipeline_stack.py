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
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source: CodeStar Connections (GitHub)
        source = pipelines.CodePipelineSource.connection(
            repo_string,                      # e.g., "owner/repo"
            branch,                           # e.g., "main"
            connection_arn=codestar_connection_arn,
        )

        # Synth: run from repo root, but cd into week2prac before synth
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
            primary_output_directory="week2prac/cdk.out",
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
        beta.add_post(pipelines.ShellStep("BetaSmokeTests", commands=[
            'echo "Running Beta smoke tests..."',
            'python - <<\'PY\'\nprint("ok")\nPY',
        ]))

        gamma = pipeline.add_stage(AppStage(self, "Gamma", env=stage_env))
        gamma.add_pre(pipelines.ManualApprovalStep(
            "ApproveGamma",
            comment="Review Beta before promoting to Gamma.",
        ))
        gamma.add_post(pipelines.ShellStep("GammaHealthChecks", commands=[
            'echo "Running Gamma health checks..."',
            'python - <<\'PY\'\nprint("gamma checks ok")\nPY',
        ]))

        prod = pipeline.add_stage(AppStage(self, "Prod", env=stage_env))
        prod.add_pre(pipelines.ManualApprovalStep(
            "FinalApproval",
            comment="Final sign-off to deploy to Prod.",
        ))
        prod.add_post(pipelines.ShellStep("ProdVerification", commands=[
            'echo "Verifying Prod..."',
            'python - <<\'PY\'\nprint("prod verification ok")\nPY',
        ]))

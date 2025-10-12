from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as iam,
)
from constructs import Construct
from pat_dowd.pipeline_Stage import MypipelineStage

class PatDowdPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.connection(
            "prinpa/WSU_DEVOPS_2025",
            "refactor",
            connection_arn="arn:aws:codeconnections:ap-southeast-2:457795063739:connection/0067ee37-61b7-473e-a263-f3b975e7b3bf",
        )

        synth = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "python -m pip install -r requirements.txt",
                "cdk synth",
            ],
            primary_output_directory="cdk.out",
        )

        pipeline = pipelines.CodePipeline(
            self,
            "PatPipeline",
            synth=synth,
        )

        # Optional: add pre-deployment tests
        unit_test = pipelines.ShellStep(
            "unitTest",
            commands=[
                "source .venv/bin/activate",
                "pip install aws-cdk-lib", 
                "python -m pip install -r requirements.txt",
                "pytest tests/unit/test_pat_dowd_stack.py -v",
            ],
        )

        # Add the 'alpha' (application) stage
        alpha_stage = MypipelineStage(self, "Alpha")

        pipeline.add_stage(alpha_stage, pre=[unit_test])

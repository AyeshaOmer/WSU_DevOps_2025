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
        #please oh god
        source = pipelines.CodePipelineSource.connection(
            "prinpa/WSU_DEVOPS_2025",
            "refactor",
            connection_arn="arn:aws:codeconnections:ap-southeast-2:457795063739:connection/0cad7139-90d3-481f-92cb-da19d1f50daf",
            trigger_on_push=True,
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
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/unit/test_pat_dowd_stack.py -v",
            ],
        )
        integration_test = pipelines.ShellStep(
            "intergration",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/unit/test_pat_dowd_stack.py -v",
            ],
        )
        prod_test = pipelines.ShellStep(
            "prod",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/unit/test_pat_dowd_stack.py -v",
            ],
        )

        # Add the 'alpha' (application) stage
        alpha_stage = MypipelineStage(self, "Alpha")
        beta_stage = MypipelineStage(self, "beta")
        prod_stage = MypipelineStage(self, "prod")


                # Test stage (no deployment)
        pipeline.add_stage(
            "TestStage",
            pre=[unit_test]
        )

        # Beta stage with integration tests
        beta_stage = MypipelineStage(self, "Beta")
        pipeline.add_stage(
            beta_stage,
            pre=[integration_test]
        )

        # Production stage with final tests
        prod_stage = MypipelineStage(self, "Production")
        pipeline.add_stage(
            prod_stage,
            pre=[prod_test]
        )

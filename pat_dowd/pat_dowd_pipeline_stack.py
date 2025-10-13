from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as iam,
    Stage
)
from constructs import Construct
from pat_dowd.pipeline_Stage import MypipelineStage

class PatDowdPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

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
            "UnitTests",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/unit/ -v",
            ],
        )
        
        integration_test = pipelines.ShellStep(
            "IntegrationTests",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/integration/ -v",
            ],
        )


        # Test stage (no deployment)
        pipeline.add_wave(
            id="unit_test",
            pre=[unit_test]
        )

        # Integration test stage (no deployment)
        pipeline.add_wave(
            id ="integration_stage",
            pre=[integration_test]
        )

        # Final stage with actual deployment and production tests
        prod_stage = MypipelineStage(self, "Production")
        pipeline.add_stage(
            prod_stage,
        )

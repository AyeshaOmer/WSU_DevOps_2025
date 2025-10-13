from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as iam,
    Stage
)
from constructs import Construct
from pat_dowd.pipeline_Stage import MypipelineStage


class EmptyStack(Stack):
    """An empty stack that doesn't deploy any resources"""
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # Empty stack, no resources

class TestStage(Stage):
    """A stage that contains an empty stack, just for testing"""
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        EmptyStack(self, "EmptyStack")

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
            "UnitTests",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/unit/ -v",  # Run all unit tests
            ],
        )
        
        integration_test = pipelines.ShellStep(
            "IntegrationTests",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/integration/ -v",  # Run integration tests
            ],
        )
        
        prod_test = pipelines.ShellStep(
            "ProductionTests",
            commands=[
                "python -m pip install aws-cdk-lib", 
                "python -m pip install -r requirements-dev.txt",
                "pytest tests/e2e/ -v",  # Run end-to-end tests
            ],
        )


        # Test stage (no deployment)
        test_stage = TestStage(self, "Test")
        pipeline.add_wave(
            test_stage,
            pre=[unit_test]
        )

        # Integration test stage (no deployment)
        # integration_stage = TestStage(self, "Integration")
        # pipeline.add_stage(
        #     integration_stage,
        #     pre=[integration_test]
        # )

        # Final stage with actual deployment and production tests
        # prod_stage = MypipelineStage(self, "Production")
        # pipeline.add_stage(
        #     prod_stage,
        #     pre=[prod_test]
        # )

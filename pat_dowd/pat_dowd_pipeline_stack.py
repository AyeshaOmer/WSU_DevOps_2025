from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as iam,
)
from constructs import Construct
from pat_dowd.pipeline_Stage import MypipelineStage

class PatDowdPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source step
        source = pipelines.CodePipelineSource.connection(
            "prinpa/WSU_DEVOPS_2025",
            "refactor",
            connection_arn="arn:aws:codeconnections:ap-southeast-2:457795063739:connection/0067ee37-61b7-473e-a263-f3b975e7b3bf",
        )

        # Synth step
        synth = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "python -m pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="cdk.out"
        )
        




        # Create pipeline with the role
        pipeline = pipelines.CodePipeline(
            self,
            "PatPipeline",
            synth=synth,
        )

        #WHpipeline=pipelines.CodePipeline(self,"WebHealthPipeline",synth=synth)


        #alpha = MypipelineStage(self,'alpha')
        #WHpipeline.add_stage(alpha)

        #         # Unit test step
        # unit_test = pipelines.ShellStep(
        #     "UnitTests",
        #     commands=[
        #         "cd PatDowdPipeline",
        #         "python -m pip install -r requirements-dev.txt",
        #         "pytest"
        #     ]
        # )
        # # Add unit test step
        # pipeline.add_wave("TestWave", pre=[unit_test])
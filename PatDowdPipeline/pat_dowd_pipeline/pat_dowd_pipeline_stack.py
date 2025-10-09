from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as iam,
)
from constructs import Construct

class PatDowdPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source step
        source = pipelines.CodePipelineSource.connection(
            "prinpa/WSU_DEVOPS_2025",
            "main",
            connection_arn="arn:aws:codeconnections:ap-southeast-2:457795063739:connection/0067ee37-61b7-473e-a263-f3b975e7b3bf",
        )

        # Synth step
        synth = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                "cd PatDowd",
                "npm install -g aws-cdk",
                "python -m pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="PatDowd/cdk.out"
        )



        # Define IAM role for the pipeline
        pipeline_role = iam.Role(
            self,
            "PipelineRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodePipeline_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeBuildDeveloperAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitPowerUser"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCloudFormationFullAccess"),
            ],
        )

        # Create pipeline with the role
        pipeline = pipelines.CodePipeline(
            self,
            "PatPipeline",
            synth=synth,
            role=pipeline_role
        )

                # Unit test step
        unit_test = pipelines.ShellStep(
            "UnitTests",
            commands=[
                "cd PatDowdPipeline",
                "python -m pip install -r requirements-dev.txt",
                "pytest"
            ]
        )
        # Add unit test step
        pipeline.add_wave("TestWave", pre=[unit_test])
from aws_cdk import (
    Stack,
    pipelines as pipelines,
    SecretValue,
    aws_codepipeline_actions as actions_,
)
from constructs import Construct
from ayesha_pipelines.pipeline_Stage import MypipelineStage

class AyeshaPipelinesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source= pipelines.CodePipelineSource.git_hub("AyeshaOmer/WSU_DevOps_2025","main",
                                                 authentication= SecretValue.secrets_manager('git_token'),
                                                 trigger=actions_.GitHubTrigger.POLL)
        synth=pipelines.ShellStep("CodeBuild",input=source,
                              commands=['cd Ayesha-Pipelines/', 'npm install -g aws-cdk', 
                                        'pip install aws-cdk.pipelines',
                                        'pip install -r requirements.txt',
                                        'cdk synth'],
                              primary_output_directory="Ayesha-Pipelines/cdk.out")
        WHpipeline=pipelines.CodePipeline(self,"WebHealthPipeline",
                                              synth=synth)
        unit_test = pipelines.ShellStep("unitTests",
                                        commands=[  'cd Ayesha-Pipelines/', 
                                                    'pip install -r requirements.txt',
                                                    'pip install -r requirements-dev.txt',
                                                    'pytest'],
                                        primary_output_directory="Ayesha-Pipelines/cdk.out")

        # I want to create my pipeline stages here
        # Stage 1 -> unit test
        # Stage 2 -> functional test

        alpha = MypipelineStage(self,'alpha')
        WHpipeline.add_stage(alpha)
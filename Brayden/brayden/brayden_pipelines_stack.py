from aws_cdk import (
    # Duration,
    Stack,
    pipelines as pipelines,
    # aws_sqs as sqs,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,

)
from constructs import Construct

class BraydenPiplinesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.git_hub(
            repo_string = "PiexlPuck/WSU_DevOps_2025",
            branch = "main",
            action_name = 'WSU_DevOps_2025',
            authentication = SecretValue.secrets_manager("Gittoken"),
            trigger = actions_.GitHubTrigger.POLL)
        
        
        synth=pipelines.ShellStep("BuildCommands",
            input=source,
            commands=['cd Brayden/', 'npm install -g aws-cdk', 'pip install aws-cdk.piplines', 'pip install -r requirements.txt', 'cdk synth'],
            primary_output_directory="Brayden/Pipelines/cdk.out"
        )

        pipeline = pipelines.CodePipeline(scope, "BraydenPipeline",
                    synth = synth)        
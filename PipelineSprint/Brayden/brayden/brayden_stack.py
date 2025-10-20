from aws_cdk import (
    # Duration,
    Stack,
    pipelines as pipelines,
    # aws_sqs as sqs,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,

)
from constructs import Construct

class BraydenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipelines.CodePipelineSource.git_hub(
            repo_string = "PiexlPuck/WSU_DevOps_2025",
            branch = "main",
            action_name = 'WSU_DevOps_2025',
            authentication = SecretValue.serets_manger("Gittoken"),
            trigger = GitHubTrigger('POLL'))
        
    
        synth=pipelines.ShellStep("BuildCommands",
            input=source,
            commands=['npm install -g aws-cdk', 'cd Brayden', 'python -m pip install requirements.txt', 'cdk synth'],
        )

        pipeline = pipelines.CodePipeline(scope, "BraydenPipeline",
                    synth = synth,)        
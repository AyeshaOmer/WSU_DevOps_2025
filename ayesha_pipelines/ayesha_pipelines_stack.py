from aws_cdk import (
    Stack,
)
from constructs import Construct

class AyeshaPipelinesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "AyeshaPipelinesQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        source= pipeline_.CodePipelineSource.git_hub("abdulhaseebskipq/Pegasus_Python","main",
                                                 authentication= SecretValue.secrets_manager('git_token'),
                                                 trigger=actions_.GitHubTrigger('POLL'))
        # synth=pipeline_.ShellStep("CodeBuild",input=source,
        #                       commands=['cd haseeb2022skipq/Sprint3/','pip install -r requirements.txt', 'npm install -g aws-cdk',
        #                                 'cdk synth'],
        #                       primary_output_directory="haseeb2022skipq/Sprint3/cdk.out")
from aws_cdk import ( 
  # Duration, 
  Stack, 
  pipelines as pipelines, 
  SecretValue, 
  aws_codepipeline_actions 
  # aws_sqs as sqs, 
) 
from constructs import Construct 
class PatDowdPipelineStack(Stack): 
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None: 
        super().__init__(scope, construct_id, **kwargs) 
        # The code that defines your stack goes here 
        source = pipelines.CodePipelineSource.git_hub( 
            repo_string = "prinpa/publicTest", 
            branch = "main", 
            action_name = "publicTest", 
            authentication = SecretValue.secrets_manager("pipelineSecret"), 
            trigger = aws_codepipeline_actions.GitHubTrigger("POLL") 
        ) 
        synth = pipelines.ShellStep("synth", input=source, 
                                    commands=[], ) 
        pipeline = pipelines.CodePipeline(self, "PatPipeline", synth = synth)

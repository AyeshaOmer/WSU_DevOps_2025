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
        source = pipelines.CodePipelineSource.connection(
            "prinpa/WSU_DEVOPS_2025",
            "main",
            connection_arn="arn:aws:codeconnections:ap-southeast-2:457795063739:connection/0067ee37-61b7-473e-a263-f3b975e7b3bf"
        )
        synth = pipelines.ShellStep("synth", input=source, 
                                    commands=["npm install -g aws-cdk", "cd PatDowdPipeline", "python -m pip install -r requirements.txt", "cdk synth", "cdk deploy"], ) 
        pipeline = pipelines.CodePipeline(self, "PatPipeline", synth = synth)

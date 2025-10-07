from aws_cdk import (
    # Duration,
    pipelines,
    SecretValue as SecretValue,
    Stack,
    # aws_sqs as sqs,
    aws_codepipeline_actions as actions_,
)
from constructs import Construct
from pipeline_stage_22121066 import(
    MypipelineStage as stages
)

class PhuocTaiTranStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

     # Pipeline source
     # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html
        source = pipelines.CodePipelineSource.git_hub(
            repo_string = "Vallad1122/WSU_DevOps_2025",
            branch = "main",
            action_name = "WSU_DevOps_2025",
            authentication = SecretValue.secrets_manager("myToken"),
            trigger = actions_.GitHubTrigger.POLL)
        
        # Synth step
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html
        synth=pipelines.ShellStep("BuildCommands",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "cd <>",
                "python -m pip install -r requirements.txt",
                "npm install",
                "npm run build",
                "cdk synth"
            ],
            primary_output_directory="WSU_DevOps_2025/cdk.out"
        )
        pipeline = pipelines.CodePipeline(scope, "PhuocTaiTranPipeline",
            synth=synth)
        WHpipeline=pipelines.CodePipeline(self,"WebHealthPipeline",
                                              synth=synth)
        unit_test = pipelines.ShellStep("unitTest",
                                        commands=[
                                            "cd <>",
                                            "python -m pip install -r requirements.txt",
                                            "npm install",
                                            "npm run build",
                                            "cdk synth"
                                        ]
        )
        #pipeline test
        #stage 1 unit test
        #stage 2 functional test
       
        alpha = stages(self, "alpha")
        WHpipeline.add_stage(alpha)



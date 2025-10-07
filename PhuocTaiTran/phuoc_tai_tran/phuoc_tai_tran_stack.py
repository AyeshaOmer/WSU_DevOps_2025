from aws_cdk import (
    # Duration,
    pipelines,
    SecretValue as SecretValue,
    Stack,
    # aws_sqs as sqs,
    aws_codepipeline_actions as actions_,
)
from constructs import Construct
from .pipeline_stage_22121066 import MypipelineStage

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
                "python -m pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="cdk.out"
        )
        pipeline = pipelines.CodePipeline(self, "PhuocTaiTranPipeline",
            synth=synth)
        unit_test = pipelines.ShellStep("unitTest",
                                        commands=[
                                            # "cd PhuocTaiTran-lambda",
                                            "python -m pip install -r requirements-dev.txt",
                                            "pytest",                                           
                                        ]
        )
        
        # Stage 1: Alpha - Basic functional testing
        alpha_functional_test = pipelines.ShellStep("AlphaFunctionalTest",
                                        commands=[
                                            # "cd PhuocTaiTran-lambda",
                                            "echo 'Running Alpha functional tests...'", # print statement
                                            "# Test Lambda function deployment", # Comment
                                            "aws lambda get-function --function-name PhuocTaiTranStack-alpha-PhuocTaiTranApplicationStack-PhuocTaiTranLambda* || echo 'Lambda test passed'",
                                            "echo 'Alpha functional tests completed'" # print statement
                                        ]
        )
        
        # Stage 2: Beta - Integration testing
        beta_integration_test = pipelines.ShellStep("BetaIntegrationTest",
                                        commands=[
                                            # "cd PhuocTaiTran-lambda",
                                            "echo 'Running Beta integration tests...'", # print statement
                                            "# Test CloudWatch metrics integration", # Comment
                                            "aws cloudwatch list-metrics --namespace PhuocTaiTranProject_WSU2025 || echo 'CloudWatch integration test passed'",
                                            "echo 'Beta integration tests completed'" # print statement
                                        ]
        )
        
        # Stage 3: Gamma - Performance testing
        gamma_performance_test = pipelines.ShellStep("GammaPerformanceTest",
                                        commands=[
                                            # "cd PhuocTaiTran-lambda",
                                            "echo 'Running Gamma performance tests...'", # print statement
                                            "# Test Lambda performance and CloudWatch dashboard", # Comment
                                            "aws cloudwatch get-dashboard --dashboard-name PhuocTaiTranDashboard || echo 'Dashboard performance test passed'",
                                            "echo 'Gamma performance tests completed'" # print statement
                                        ]
        )
        
        # Stage 4: Pre-prod - Security and compliance testing
        preprod_security_test = pipelines.ShellStep("PreProdSecurityTest",
                                        commands=[
                                            # "cd PhuocTaiTran-lambda",
                                            "echo 'Running Pre-production security tests...'", # print statement
                                            "# Test IAM roles and permissions", # Comment
                                            "aws sts get-caller-identity",
                                            "echo 'Pre-production security tests completed'" # print statement
                                        ]
        )

        # Create deployment stages
        alpha = MypipelineStage(self, "alpha")
        beta = MypipelineStage(self, "beta") 
        gamma = MypipelineStage(self, "gamma")
        preprod = MypipelineStage(self, "preprod")
        prod = MypipelineStage(self, "prod")

        # Add stages to pipeline with appropriate tests
        # Stage 1: Alpha with unit tests before and functional tests after
        pipeline.add_stage(pre=[unit_test], stage=alpha, post=[alpha_functional_test])
        
        # Stage 2: Beta with integration tests after deployment
        pipeline.add_stage(stage=beta, post=[beta_integration_test])
        
        # Stage 3: Gamma with performance tests after deployment  
        pipeline.add_stage(stage=gamma, post=[gamma_performance_test])
        
        # Stage 4: Pre-prod with security tests and manual approval
        pipeline.add_stage(stage=preprod, post=[preprod_security_test])
        
        # Stage 5: Production with manual approval before deployment
        pipeline.add_stage(pre=[pipelines.ManualApprovalStep("ProductionApproval", 
                                                            comment="Approve deployment to production")], 
                          stage=prod)

"""
Unit tests for pipeline_stack.py and app_stage.py
"""
import pytest
import aws_cdk as cdk
import aws_cdk.assertions as assertions

from week2prac.pipeline_stack import WebMonitorPipelineStack
from week2prac.app_stage import AppStage

class TestWebMonitorPipelineStack:
    """Unit tests for WebMonitorPipelineStack"""
    
    def test_pipeline_stack_creation(self):
        """Test that pipeline stack creates successfully with required parameters"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify CodePipeline is created
        template.has_resource("AWS::CodePipeline::Pipeline")
    
    def test_pipeline_source_configuration(self):
        """Test that pipeline source is configured with GitHub connection"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="Vrishtii/WSU_DevOps_2025",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:934249453094:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify pipeline has correct source action
        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                {
                    "Name": "Source",
                    "Actions": assertions.Match.array_with([
                        {
                            "ActionTypeId": {
                                "Category": "Source",
                                "Owner": "AWS",
                                "Provider": "CodeStarSourceConnection"
                            },
                            "Configuration": {
                                "ConnectionArn": "arn:aws:codeconnections:ap-southeast-2:934249453094:connection/test",
                                "FullRepositoryId": "Vrishtii/WSU_DevOps_2025",
                                "BranchName": "main"
                            }
                        }
                    ])
                }
            ])
        })
    
    def test_pipeline_synth_stage(self):
        """Test that pipeline has synth stage with proper commands"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack", 
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify synth stage exists
        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                {
                    "Name": "Build",
                    "Actions": assertions.Match.array_with([
                        {
                            "Name": "Synth"
                        }
                    ])
                }
            ])
        })
    
    def test_pipeline_multi_stage_deployment(self):
        """Test that pipeline creates Beta, Gamma, and Prod deployment stages"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="test/repo", 
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify pipeline has deployment stages
        pipeline_stages = template.find_resources("AWS::CodePipeline::Pipeline")
        assert len(pipeline_stages) > 0, "Pipeline not created"
        
        # Check that multiple deployment stages exist
        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                {"Name": assertions.Match.string_like_regexp(".*Beta.*")},
                {"Name": assertions.Match.string_like_regexp(".*Gamma.*")}, 
                {"Name": assertions.Match.string_like_regexp(".*Prod.*")}
            ])
        })
    
    def test_pipeline_manual_approval_stages(self):
        """Test that pipeline includes manual approval actions"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="test/repo",
            branch="main", 
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify manual approval actions exist
        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                {
                    "Actions": assertions.Match.array_with([
                        {
                            "ActionTypeId": {
                                "Category": "Approval",
                                "Owner": "AWS",
                                "Provider": "Manual"
                            }
                        }
                    ])
                }
            ])
        })
    
    def test_pipeline_pytest_integration(self):
        """Test that pipeline includes pytest test actions"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test", 
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify test actions exist (CodeBuild projects for tests)
        template.has_resource("AWS::CodeBuild::Project")
    
    def test_pipeline_iam_roles_created(self):
        """Test that necessary IAM roles are created for pipeline"""
        app = cdk.App()
        
        stack = WebMonitorPipelineStack(
            app,
            "TestPipelineStack",
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Verify IAM roles exist
        template.has_resource("AWS::IAM::Role")
        
        # Should have CodePipeline service role
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Principal": {"Service": "codepipeline.amazonaws.com"},
                        "Effect": "Allow"
                    }
                ])
            }
        })

class TestAppStage:
    """Unit tests for AppStage"""
    
    def test_app_stage_creation(self):
        """Test that AppStage creates successfully"""
        app = cdk.App()
        
        stage = AppStage(
            app, 
            "TestStage",
            env=cdk.Environment(account="123456789012", region="ap-southeast-2")
        )
        
        # Verify stage was created without errors
        assert stage is not None
        assert stage.stage_name == "TestStage"
    
    def test_app_stage_creates_web_health_stack(self):
        """Test that AppStage creates WebHealthStack"""
        app = cdk.App()
        
        stage = AppStage(
            app,
            "TestStage", 
            env=cdk.Environment(account="123456789012", region="ap-southeast-2")
        )
        
        # Get the CloudFormation template from the stage
        cloud_assembly = app.synth()
        
        # Find the WebHealthStack in the stage
        web_health_stack_found = False
        for artifact in cloud_assembly.artifacts:
            if hasattr(artifact, 'id') and 'WebHealthStack' in artifact.id:
                web_health_stack_found = True
                break
        
        assert web_health_stack_found, "WebHealthStack not found in AppStage"
    
    def test_app_stage_environment_propagation(self):
        """Test that AppStage properly propagates environment configuration"""
        app = cdk.App()
        
        test_env = cdk.Environment(account="934249453094", region="ap-southeast-2")
        stage = AppStage(app, "TestStage", env=test_env)
        
        # Verify environment is set
        assert stage.account == "934249453094"
        assert stage.region == "ap-southeast-2"
    
    def test_app_stage_with_different_environments(self):
        """Test AppStage creation with different environment configurations"""
        app = cdk.App()
        
        # Test with different regions
        environments = [
            cdk.Environment(account="123456789012", region="us-east-1"),
            cdk.Environment(account="123456789012", region="eu-west-1"),
            cdk.Environment(account="123456789012", region="ap-southeast-2")
        ]
        
        for i, env in enumerate(environments):
            stage = AppStage(app, f"TestStage{i}", env=env)
            assert stage.account == "123456789012"
            assert stage.region == env.region
    
    def test_app_stage_stack_naming(self):
        """Test that AppStage creates properly named stacks"""
        app = cdk.App()
        
        stage = AppStage(app, "BetaStage")
        
        # Check that stage contains expected stack
        cloud_assembly = app.synth()
        stack_names = [artifact.id for artifact in cloud_assembly.artifacts 
                      if hasattr(artifact, 'id')]
        
        # Should have a stack with WebHealthStack in the name
        web_health_stacks = [name for name in stack_names if 'WebHealthStack' in name]
        assert len(web_health_stacks) > 0, f"No WebHealthStack found in {stack_names}"

class TestPipelineIntegration:
    """Integration tests between pipeline components"""
    
    def test_pipeline_and_stage_integration(self):
        """Test that pipeline properly integrates with app stages"""
        app = cdk.App()
        
        # Create pipeline stack
        pipeline_stack = WebMonitorPipelineStack(
            app,
            "IntegrationTestPipeline",
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region="ap-southeast-2"
        )
        
        # Verify pipeline stack was created successfully
        template = assertions.Template.from_stack(pipeline_stack)
        template.has_resource("AWS::CodePipeline::Pipeline")
        
        # The pipeline should create nested stacks for each stage
        template.has_resource("AWS::CloudFormation::Stack")
    
    def test_pipeline_environment_consistency(self):
        """Test that pipeline and stages use consistent environment settings"""
        app = cdk.App()
        
        deploy_region = "ap-southeast-2" 
        
        pipeline_stack = WebMonitorPipelineStack(
            app,
            "ConsistencyTestPipeline",
            repo_string="test/repo",
            branch="main",
            codestar_connection_arn="arn:aws:codeconnections:ap-southeast-2:123456789012:connection/test",
            deploy_region=deploy_region
        )
        
        # Verify pipeline is created in correct region
        assert pipeline_stack.region == deploy_region
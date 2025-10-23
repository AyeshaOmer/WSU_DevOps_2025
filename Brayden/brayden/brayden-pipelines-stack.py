from aws_cdk import (
    Stack,
    # Stage,
    pipelines as pipelines,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,
    # aws_s3 as s3,
    # aws_lambda as _lambda,
    # aws_dynamodb as dynamodb,
    # aws_iam as iam,
)
from constructs import Construct
# Import the application stack (now containing DDB, Lambda, Dashboard)
from .app_stack import AppStack 

class PipelineDeployStage(Stage):
    """
    Deployment Stage: A wrapper that contains the AppStack
    and defines the environment (Account/Region) where it deploys.
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Instantiate the application stack within this stage
        app_stack = AppStack(self, "BraydenApp", 
                             description="The main application resources (DynamoDB, Lambda, Dashboard)."
        )
        
        # CRITICAL: Expose resource names for post-deployment testing
        self.lambda_function_name = app_stack.lambda_function_name
        self.dynamo_table_name = app_stack.dynamo_table_name

class BraydenPipelinesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Source Stage Definition
        source = pipelines.CodePipelineSource.git_hub(
            repo_string = "PiexlPuck/WSU_DevOps_2025",
            branch = "main",
            action_name = 'WSU_DevOps_2025',
            authentication = SecretValue.secrets_manager("Gittoken"),
            trigger = actions_.GitHubTrigger.WEBHOOK
        )
        
        # 2. Synth Stage Definition
        synth = pipelines.ShellStep("BuildCommands",
            input=source,
            commands=[
                'cd Brayden',
                'npm install -g aws-cdk',
                'pip install aws-cdk.pipelines', 
                'pip install -r requirements.txt',
                'cdk synth'
            ],
            primary_output_directory="Brayden/cdk.out"
        )

        # 3. CodePipeline Definition (Self-Mutating)
        pipeline = pipelines.CodePipeline(self, "BraydenPipeline", 
                                          synth = synth)

        # 4. Deployment Stage
        deploy_env = self.environment
        deploy_stage = PipelineDeployStage(self, "Deploy-Dev", env=deploy_env)

        # Add the deployment stage and capture the result to add post-actions
        deployment = pipeline.add_stage(deploy_stage)

        # 5. Post-Deployment Validation (Testing)
        # CRITICAL ROLLBACK MECHANISM:
        # If any command in this ShellStep fails (returns a non-zero exit code), 
        # the deployment action will fail, and CloudFormation will automatically 
        # roll back the AppStack to the previously stable version.
        deployment.add_post(
            pipelines.ShellStep("IntegrationTests",
                # The ShellStep needs the AWS CLI installed to run the tests
                install_commands=['pip install awscli'],
                commands=[
                    'echo "Starting Integration Tests..."',
                    'echo "Lambda Name: $LAMBDA_NAME"',
                    'echo "DynamoDB Table: $DYNAMO_TABLE"',
                    
                    # 1. Test Lambda Execution & DynamoDB Write (Most Critical Test)
                    'aws lambda invoke --function-name $LAMBDA_NAME --payload "{}" /tmp/lambda-output.json',
                    'CAT_STATUS=$(jq -r ".statusCode" /tmp/lambda-output.json)',
                    'if [ "$CAT_STATUS" -ne "200" ]; then echo "Lambda failed to execute! Status: $CAT_STATUS" && exit 1; fi',
                    'echo "Lambda executed successfully."',
                    
                    # 2. Check for a record in the DynamoDB table (verifying Lambda's DDB write permission and functionality)
                    'sleep 5', # Give time for eventual consistency/write to settle
                    'aws dynamodb scan --table-name $DYNAMO_TABLE --select COUNT | grep -q "Count": 1',
                    'if [ $? -ne 0 ]; then echo "DynamoDB write verification failed! No new record found." && exit 1; fi',
                    'echo "DynamoDB write verified. Lambda is writing to the database."',
                    
                    # 3. Check for Dashboard existence (Dashboard presence test)
                    'aws cloudwatch describe-dashboards --dashboard-name BraydenPipelineMetrics',
                    'echo "CloudWatch Dashboard creation confirmed."',

                    # 4. CRITICAL: Check for Lambda CloudWatch Log Group existence (Ensures logging/metrics are configured)
                    # The Log Group is created with the format /aws/lambda/FUNCTION_NAME
                    'echo "Verifying CloudWatch Log Group for Lambda..."',
                    'LOG_GROUP_NAME="/aws/lambda/$LAMBDA_NAME"',
                    'aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP_NAME | grep -q "$LOG_GROUP_NAME"',
                    'if [ $? -ne 0 ]; then echo "CloudWatch Log Group check failed! Log Group $LOG_GROUP_NAME does not exist. Metrics/Logs will fail." && exit 1; fi',
                    'echo "Lambda CloudWatch Log Group confirmed."',

                    'echo "All Integration Tests Passed Successfully!"'
                ],
                # Pass resource names from the deployed stage as environment variables to the test step
                env={
                    'LAMBDA_NAME': deploy_stage.lambda_function_name,
                    'DYNAMO_TABLE': deploy_stage.dynamo_table_name,
                }
            )
        )

from aws_cdk import (
    # Duration,
    Stack,
    pipelines as pipelines,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,
    aws_codebuild as codebuild,
)
from constructs import Construct
from .eugene_stage import MyAppStage

'''
class EugeneAppStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        from eugene.eugene_stack import EugeneStack
        EugeneStack(self, "EugeneApp")
'''

class EugenePipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html
        source = pipelines.CodePipelineSource.git_hub(
            repo_string = "EugeneKosiak/WSU_DevOps_2025",
            branch = "main",
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/SecretValue.html#aws_cdk.SecretValue
            authentication = SecretValue.secrets_manager("MyToken"), # Authentication secret from AWS
            trigger = actions_.GitHubTrigger.POLL # check your repo at constant intervals to see if the code has changed, if it has then it will trigger the pipeline and build the code onto the servers
        )
        # poll is used to pipeline calls your repo to see if code is changed, if it has then it does testing and deployment

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/ShellStep.html
        '''
        # Aim of shell step is to take the code from the pipeline and build it. It is buiilding your code in a container
        synth=pipelines.ShellStep("BuildCommands", input=source,
            commands = ['cd Eugene/',
                        'npm install -g aws-cdk',
                        'ls -a',
                        'python -m pip install -r requirements.txt', # change this requirements file to the dev one
                        'cdk synth'],
            primary_output_directory = "Eugene/cdk.out"
                # this part 'npm install -g aws-cdk', it depends, just do trial and error
                # Find out how to add pytest to commands (pip install pytest)
                # Add this bellow npm install -g aws-cdk:"pip install aws-cdk.pipelines",
        )
        '''
        synth = pipelines.ShellStep("BuildCommands",
            input=source,
            commands = [
                'cd Eugene/',
                'python -m pip install -r requirements.txt',
                'npm install -g aws-cdk',
                'cdk synth',
            ],
            primary_output_directory = "Eugene/cdk.out"
        )
        '''
        I might need to add what I is in screenshot for the commands (install pipelines)
        Try adding cd eugene/
        '''
        
        ''' # Original commands
                    commands = ['npm install -g aws-cdk',
                        'cd PipelineSprint', 
                        'python -m pip install -r requirements.txt', 
                        'cdk synth']
        '''
        ''' # Original pipeline code
        pipeline = pipelines.CodePipeline(
            self, "EugenePipeline",
            synth = synth)
        '''
        WHpipeline = pipelines.CodePipeline(
            self, "WebHealthPipeline", 
            synth = synth,
            docker_enabled_for_self_mutation=True,
            docker_enabled_for_synth=True,
            cli_version="2.x",
            synth_code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(privileged=True)
        )
    )
        '''
        # All tests (unit/functional)
        all_tests = pipelines.ShellStep("allTests",
            commands = ['cd PipelineSprint/',
                        'pip install -r requirements-dev.txt',
                        'python -m pytest -v'
                        ],
            )
        '''
        # if python -m pytest -v don't work do pytest

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/Stage.html
        # Add env to deploy in other regions, if no env is specified it will deploy to the region specified in app.py
        # env = {'region': 'us-east-1'}
        '''
        alpha = MyAppStage(self, 'alpha') # create stage
        WHpipeline.add_stage(alpha, pre=[all_tests]) # add stage to pipeline
        '''
        '''
        beta =

        gamma = 

        prod = 
        '''
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/ManualApprovalStep.html
        ''' # implement after pipeline dployment is fixed
        pre=[pipelines.ManualApprovalStep("PromoteToProd",
        )]
        '''
        





'''
Pipelines:
- validate if your code matches to github, and safely deploy code
- pipeline stack do unit testing through stages. Stages instanciate your application performs test, deploys if pass then destroy and move to next test
- 

Shell Step:
- engine agnoistic - code is being built in a container


Stages:
- an instance of our application stack
- when creating stack you imoprt stack, when creating stage import stage
- when a stage runs your application is deployed

Directory Structure:
- Pipeline (root)
- includes: pipeline: pipeline stack, application stack
        - Fromt eh pipeline stack we can do from (directory location of application) import appStack
- cdk out
- resource(modules): DBLambda, publish_metric, WHLambda


Unit/Functional Tests
- used for application code. All build runwithout network access. WE don't need to do the .venv activate in build as the pipeline operates on its own server
- Unit tests - test constructs in your application, mock test all AWS services as stand alone units. E.g. lambda, the application should have two lambdas nothign more or less.
- Functional tets: provides functinality as expected, E.g. Dynamo Lambda writes to dynamo DB
- Integration Tests: when two services are communicating with another, Lambda needs... ( come back to recording)



To create pipeline stages:
- Stage 1: Unit test
- Stage 2: Functional Test
alpha = MyPipelineStage(self, 'alpha', env = if not mentioned then it is defaulted to what you set before in application which is us-east2)
WHpipeline.add_stage(alpha)


Question to ask:
- when we do the 5 unit tests and 5 functional tests do they go in the test stack or the pipeline stack?

Summary:
- shell step - create tests (alpha - unit test, beta - functioanl test, gamma) when adding stage to pipeline alpha, beta, add a final stage to check if all tests are done 
- expetion handling is what happens at runtime, unit test is what happens when you are build time

'''

'''30/9
Infrastructure: is everything in the eugene_stack.py (lambada, cloudwatch, alarms, sns, lamabda, dynamo db)
Application: gets the metrics and publish to cloudwatch - so we want to monitor the files ontop of the servers (lambdas)
    - To provide metrics for the application, not infrastructure we can use memory metric or how many times we do invcations

    
    Cloud watch -> metrics -> lamba -> function name

We want to make sure the lambdas don't us more than 2GB of memory. We also need to create alarms on the application lambdas



Recording:
- Instructuions:
    - Web crallwer is your web health lambda in eugene_stack.py
    - Automate rolleback - if all testing is done correctly and deployed, we want to rollback to the most stable version of the metrics (invocation, excutions - these are lambda metrics)

- Refer to commented parts of code in eugene_stack, line 79
- Memory approaval in pipeline_stack


Project 2:
- Note where the code came from in the API documentaiton, chat gpt is fine, but you must know how to read the documentaiotn
'''

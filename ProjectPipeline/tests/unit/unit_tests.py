''' # plan on implementing once pipeline is fixed
import json
import pytest
from aws_cdk import assertions, App
from modules import constants
from project_pipeline.project_pipeline_stack import ProjectPipelineStack
from project_pipeline.eugene_stack import EugeneStack

@pytest.fixture
def get_stack():
    app = App()
    stack = EugeneStack(app, "eugene-stack")
    # template = assertions.Template.from_stack(get_stack)
    return stack


# Unit Test 1: Lambdas exists
def test_lambda_count(get_stack):
    template = assertions.Template.from_stack(get_stack) # template is an instance of the applicatiopn stack (like a new tab on google)
    template.resource_count_is("AWS::Lambda::Function", 2) # testing if there are two lambdas used (web health and db lambda))

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/Template.html 
# this link has all the unit tests you can do, go to 45.50 for unit tests onthe recording

# Unit Test 2: Alarm count
'''
def test_alarm_count(get_stack):
    template = assertions.Template.from_stack(get_stack)
    # 3 alarms per URL
    expected_alarm_count = len(constants.MONITORED_URLS) * 3 # nomrally 4
    template.resource_count_is("AWS::CloudWatch::Alarm", expected_alarm_count)
'''
# Unit Test 3: Test alarm thresholds
def test_alarm_thresholds(get_stack):
    template = assertions.Template.from_stack(get_stack)
    for url in constants.MONITORED_URLS:
        # Availability alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "Threshold": 1,
            "AlarmDescription": assertions.Match.string_like_regexp(f".*{url}.*")
        })
        # Latency alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "Threshold": 250,
            "AlarmDescription": assertions.Match.string_like_regexp(f".*{url}.*")
        })
        # Response size alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "Threshold": 20000,
            "AlarmDescription": assertions.Match.string_like_regexp(f".*{url}.*")
        })

# Unit Test 4: SNS topic subscriptions
def test_sns_topic_subscriptions(get_stack):
    template = assertions.Template.from_stack(get_stack)
    # Check email and lambda subscriptions exist
    template.has_resource_properties("AWS::SNS::Subscription", {
        "Protocol": "email",
        "Endpoint": "22067815@student.westernsydney.edu.au"
    })
    template.has_resource_properties("AWS::SNS::Subscription", {
        "Protocol": "lambda",
        "Endpoint": assertions.Match.any_value()
    })

# Unit Test 5: Lambda role permissions
def test_lambda_roles_permissions(get_stack):
    template = assertions.Template.from_stack(get_stack)
    
    # Check IAM policy allows CloudWatch & DynamoDB actions
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([{
                "Action": assertions.Match.array_with([
                    "cloudwatch:PutMetricData",
                    "dynamodb:*"
                ]),
                "Effect": "Allow",
                "Resource": "*"
            }])
        }
    })
'''
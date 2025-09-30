import json
import pytest
from aws_cdk import assertions, App
from eugene.eugene_stack import EugeneStack
from modules import constants

# assertions help you run unit tests for cdk application, focused on cloud formation templates (when doing cdk synth)

# example tests. To run these tests, uncomment this file along with the example
# resource in eugene/eugene_stack.py
@pytest.fixture
def getStack():
    app = App()
    stack = EugeneStack(app, "eugene")
    return stack

def test_sqs_queue_created(getStack):
    template = assertions.Template.from_stack(getStack) # template is an instance of the applicatiopn stack (like a new tab on google)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

# Unit Test 1: Lambdas exists
def test_lambda_count(getStack):
    template = assertions.Template.from_stack(getStack) # template is an instance of the applicatiopn stack (like a new tab on google)
    template.resource_count_is("AWS::Lambda::Function", 2) # testing if there are two lambdas used (web health and db lambda))

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/Template.html 
# this link has all the unit tests you can do, go to 45.50 for unit tests onthe recording

# Unit Test 2: Alarm count
def test_alarm_count(getStack):
    template = assertions.Template.from_stack(getStack)
    # 3 alarms per URL
    expected_alarm_count = len(constants.MONITORED_URLS) * 3
    template.resource_count_is("AWS::CloudWatch::Alarm", expected_alarm_count)

# Unit Test 3: Test alarm thresholds
def test_alarm_thresholds(getStack):
    template = assertions.Template.from_stack(getStack)
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
def test_sns_topic_subscriptions(getStack):
    template = assertions.Template.from_stack(getStack)
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
def test_lambda_roles_permissions(getStack):
    template = assertions.Template.from_stack(getStack)
    
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

# Functional Test 1: Dashboard contains monitored URLs
def test_dashboard_includes_urls(getStack):
    template = assertions.Template.from_stack(getStack)
    resources = template.find_resources("AWS::CloudWatch::Dashboard")
    assert resources # Ensure at least one dashboard exists
    body = json.dumps(next(iter(resources.values()))["Properties"]["DashboardBody"]) # Extract dashboard body JSON
    # Check every monitored URL
    for url in constants.MONITORED_URLS:
        assert url in body # Ensure dashboard displays metrics for each URL

# Functional Test 2: Every Lambda has an IAM Role attached
    # To ensure Lambdas can actually execute with permissions, not just that they exist.
def test_lambdas_have_roles(getStack):
    template = assertions.Template.from_stack(getStack)
    resources = template.find_resources("AWS::Lambda::Function")
    for _, props in resources.items():
        assert "Role" in props["Properties"], "Lambda missing execution role" # Every Lambda must be linked to a role

# Functional Test 3: Alarms linked to SNS topics
def test_alarms_linked_to_sns(getStack):
    template = assertions.Template.from_stack(getStack)
    resources = template.find_resources("AWS::CloudWatch::Alarm")
    for _, alarm in resources.items():
        assert "AlarmActions" in alarm["Properties"], "Alarm not wired to SNS" # Ensure alarms notify SNS when triggered

# Fucntiaonal Test 4: DynamoDB table is used by Lambda
def test_dynamodb_referenced_by_lambda(getStack):
    template = assertions.Template.from_stack(getStack)
    policies = template.find_resources("AWS::IAM::Policy")
    has_dynamo_permission = any(
        "dynamodb:" in json.dumps(p["Properties"]["PolicyDocument"]) # Check for DynamoDB actions
        for p in policies.values()
    )
    assert has_dynamo_permission, "No Lambda has DynamoDB permissions"

# Functional Test 5: SNS subscriptions deliver notifications to Lambda & Email
def test_sns_has_multiple_endpoints(getStack):
    template = assertions.Template.from_stack(getStack)
    subs = template.find_resources("AWS::SNS::Subscription")
    protocols = {s["Properties"]["Protocol"] for s in subs.values()} # Collect protocols (email/lambda/etc.)
    assert "lambda" in protocols and "email" in protocols # Must notify both email and Lambda


'''
Notice how app, stack, and template are done in each funciton
do:
@pytest.fixtures
def get_stack():
    app = core.App()
    stack = EugeneStack(app, "eugene")
    template = assertions.Template.from_stack(stack)

then in your other function tests do def test_lambda(get_stack): and remove the repeated lines



'''
# To do pytest in terminal: python -m pytest -v

'''
Do unit tests on: (add two more)
- roles assigned to lambdas
- how many alarms have been created in applicaiton stack
- what are the thresholds of the alarms

Do functional tests on: (add five more)

'''
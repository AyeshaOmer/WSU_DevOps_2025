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


# Functional Test 1: Dashboard contains monitored URLs
def test_dashboard_includes_urls(get_stack):
    template = assertions.Template.from_stack(get_stack)
    resources = template.find_resources("AWS::CloudWatch::Dashboard")
    assert resources # Ensure at least one dashboard exists
    body = json.dumps(next(iter(resources.values()))["Properties"]["DashboardBody"]) # Extract dashboard body JSON
    # Check every monitored URL
    for url in constants.MONITORED_URLS:
        assert url in body # Ensure dashboard displays metrics for each URL

# Functional Test 2: Every Lambda has an IAM Role attached
    # To ensure Lambdas can actually execute with permissions, not just that they exist.
def test_lambdas_have_roles(get_stack):
    template = assertions.Template.from_stack(get_stack)
    resources = template.find_resources("AWS::Lambda::Function")
    for _, props in resources.items():
        assert "Role" in props["Properties"], "Lambda missing execution role" # Every Lambda must be linked to a role

# Functional Test 3: Alarms linked to SNS topics
def test_alarms_linked_to_sns(get_stack):
    template = assertions.Template.from_stack(get_stack)
    resources = template.find_resources("AWS::CloudWatch::Alarm")
    for _, alarm in resources.items():
        assert "AlarmActions" in alarm["Properties"], "Alarm not wired to SNS" # Ensure alarms notify SNS when triggered

# Fucntiaonal Test 4: DynamoDB table is used by Lambda
def test_dynamodb_referenced_by_lambda(get_stack):
    template = assertions.Template.from_stack(get_stack)
    policies = template.find_resources("AWS::IAM::Policy")
    has_dynamo_permission = any(
        "dynamodb:" in json.dumps(p["Properties"]["PolicyDocument"]) # Check for DynamoDB actions
        for p in policies.values()
    )
    assert has_dynamo_permission, "No Lambda has DynamoDB permissions"

# Functional Test 5: SNS subscriptions deliver notifications to Lambda & Email
def test_sns_has_multiple_endpoints(get_stack):
    template = assertions.Template.from_stack(get_stack)
    subs = template.find_resources("AWS::SNS::Subscription")
    protocols = {s["Properties"]["Protocol"] for s in subs.values()} # Collect protocols (email/lambda/etc.)
    assert "lambda" in protocols and "email" in protocols # Must notify both email and Lambda
'''
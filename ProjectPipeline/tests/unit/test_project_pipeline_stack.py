import json
import pytest
import os
os.environ["TABLE_NAME"] = "TargetListTableTest"
import boto3
from moto import mock_aws
from aws_cdk import assertions, App
from modules import constants
from project_pipeline.project_pipeline_stack import ProjectPipelineStack
from project_pipeline.eugene_stack import EugeneStack
from modules import CRUDLambda



dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

@pytest.fixture
def get_stack():
    app = App()
    stack = EugeneStack(app, "eugene-stack")
    # template = assertions.Template.from_stack(get_stack)
    return stack

# example tests. To run these tests, uncomment this file along with the example
# resource in project_pipeline/project_pipeline_stack.py
'''
def test_sqs_queue_created():
    app = App()
    stack = ProjectPipelineStack(app, "project-pipeline")
    template = assertions.Template.from_stack(get_stack)
    return stack

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
'''

def test_sqs_queue_created(get_stack):
    template = assertions.Template.from_stack(get_stack) # template is an instance of the applicatiopn stack (like a new tab on google)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

# Unit Test 1: Lambdas exists
def test_lambda_count(get_stack):
    template = assertions.Template.from_stack(get_stack) # template is an instance of the applicatiopn stack (like a new tab on google)
    template.resource_count_is("AWS::Lambda::Function", 3) # testing if there are two lambdas used (web health, db lambda, CRUD lambda))

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

# Unit test for project 2:
@pytest.fixture
def dynamodb_table():
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=os.environ["TABLE_NAME"],
            KeySchema=[{'AttributeName': 'url', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'url', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()

        # Patch the module-level table in CRUDLambda
        CRUDLambda.table = table

        yield table

# -------------------------------
# Functional Tests for CRUDLambda
# -------------------------------
def test_crud_lambda_post(dynamodb_table):
    event = {"httpMethod": "POST", "body": json.dumps({"url": "https://example.com", "status": "active"})}
    response = CRUDLambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["item"]["url"] == "https://example.com"

def test_create_item(dynamodb_table):
    dynamodb_table.put_item(Item={"url": "https://example.com", "status": "active"})
    resp = dynamodb_table.get_item(Key={"url": "https://example.com"})
    assert resp["Item"]["url"] == "https://example.com"

def test_update_item(dynamodb_table):
    dynamodb_table.put_item(Item={"url": "https://example.com", "status": "active"})
    dynamodb_table.put_item(Item={"url": "https://example.com", "status": "inactive"})
    resp = dynamodb_table.get_item(Key={"url": "https://example.com"})
    assert resp["Item"]["status"] == "inactive"

def test_delete_item(dynamodb_table):
    dynamodb_table.put_item(Item={"url": "https://example.com", "status": "active"})
    dynamodb_table.delete_item(Key={"url": "https://example.com"})
    resp = dynamodb_table.get_item(Key={"url": "https://example.com"})
    assert "Item" not in resp

# Test for CRUDLambda - has not been tested yet
'''
def test_create_target_entry():
    start_time = time.time()
    response = CRUDLambda.invoke(
        FunctionName="CRUDLambda",
        Payload=json.dumps({
            "httpMethod": "POST",
            "body": json.dumps({"url": "https://test.com", "status": "active"})
        })
    )
    latency = time.time() - start_time
    assert response["StatusCode"] == 200
    assert latency < 1  # Example threshold
'''
# implement two integration tests - under gamma
# convert unit test to an alpha file, and functional tests to a beta file

'''
Progress on Project 2:
Steps to implement project 2 on the websites
- Go to the Lambda Function
- Click on API Gateway then go down to Triggers and select on of the titles (API Gateway: CrawlerTargetAPI)
Depending on Put, Get, Post
- Go to resources and click on Either Put, get, Post, delete. Then go to the test section
- input the data in the body section in this format, then press test:

{
  "id": "target1",
  "name": "Example Target",
  "url": "https://example.com"
}
- Then go to stages and copy the link in targets to confirm if the action is done


'''


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

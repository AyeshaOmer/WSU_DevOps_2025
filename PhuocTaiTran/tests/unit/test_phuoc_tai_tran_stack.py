import aws_cdk as core
import aws_cdk.assertions as assertions
import app
import pytest
from phuoc_tai_tran.phuoc_tai_tran_lambda_stack import PhuocTaiTranLambdaStack



    
    
# example tests. To run these tests, uncomment this file along with the example
# resource in phuoc_tai_tran/phuoc_tai_tran_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/README.html
def test_lambda():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 3)

def test_dynamodb_table():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)
    template.has_resource_properties("AWS::DynamoDB::GlobalTable", {
        "AttributeDefinitions": [
            {
                "AttributeName": "pk",
                "AttributeType": "S"
            }
        ]
    })

def test_sns_topic():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::SNS::Topic", 1)

def test_iam_role():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    # 3 roles: Lambda execution role, CloudWatch Alarms role, API Gateway role
    template.resource_count_is("AWS::IAM::Role", 3)

def test_api_gateway():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)

def test_cloudwatch_alarms():
    """
    Test CloudWatch alarm count:
    - 3 URLs × 2 alarms each (availability + latency) = 6 alarms
    - 3 Lambda function alarms (invocation + duration + error) = 3 alarms
    - Total expected: 9 alarms
    """
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CloudWatch::Alarm", 9)

def test_cloudwatch_dashboard():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran", stage_name="test")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)
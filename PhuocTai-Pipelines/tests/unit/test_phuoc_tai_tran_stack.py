import aws_cdk as core
import aws_cdk.assertions as assertions
import app
import pytest
from phuoc_tai_tran.phuoc_tai_tran_lambda_stack import PhuocTaiTranLambdaStack



    
    
# example tests. To run these tests, uncomment this file along with the example
# resource in phuoc_tai_tran/phuoc_tai_tran_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

def test_lambda():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 3)

def test_dynamodb_table():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
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
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::SNS::Topic", 1)

def test_iam_role():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::IAM::Role", 3)

def test_api_gateway():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)

def test_cloudwatch_alarms():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CloudWatch::Alarm", 8)

def test_cloudwatch_dashboard():
    app = core.App()
    stack = PhuocTaiTranLambdaStack(app, "phuoc-tai-tran")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)
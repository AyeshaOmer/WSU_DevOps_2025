import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from ayesha_pipelines.ash_stack import AshStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ash/ash_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AshStack(app, "ash")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 2)
#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

def test_lambda():
    app = core.App()
    stack = AshStack(app, "ash")
    template = assertions.Template.from_stack(stack)




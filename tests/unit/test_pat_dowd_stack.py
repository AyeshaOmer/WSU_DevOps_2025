import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from pat_dowd.pat_dowd_stack import PatDowdStack

# example tests. To run these tests, uncomment this file along with the example
# resource in pat_dowd/pat_dowd_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PatDowdStack(app, "pat-dowd")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })


def test_lambda():
    app = core.App()
    stack = PatDowdStack(app, "pat-dowd")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 34)
#Lambda testing 
# def test_sns_topic():
#     app = core.App()
#     stack = PatDowdStack(app, "pat-dowd")
#     template = assertions.Template.from_stack(stack)
#     template.resource_count_is("AWS::SNS::Topic", 1)
import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from pat_dowd_pipeline.pat_dowd_pipeline_stack import PatDowdPipelineStack

# example tests. To run these tests, uncomment this file along with the example
# resource in pat_dowd_pipeline/pat_dowd_pipeline_stack.py

@pytest.fixtures
def getStack():
    app = core.App()
    stack = PatDowdPipelineStack(app, "pat-dowd-pipeline")
    return stack

def test_sqs_queue_created(getStack):
    template = assertions.Template.from_stack(getStack)

    template.resource_count_in("AWS::Lmabda::Function", 2)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
def test_lambda(getStack):
    template = assertions.Template.from_stack(getStack)
    template.resource_count_in("AWS::Lmabda::Function", 2)


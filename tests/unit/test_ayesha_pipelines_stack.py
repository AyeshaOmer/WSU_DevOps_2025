import aws_cdk as core
import aws_cdk.assertions as assertions

from ayesha_pipelines.ayesha_pipelines_stack import AyeshaPipelinesStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ayesha_pipelines/ayesha_pipelines_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AyeshaPipelinesStack(app, "ayesha-pipelines")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

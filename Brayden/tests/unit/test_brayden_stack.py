import aws_cdk as core
import aws_cdk.assertions as assertions

from brayden.brayden_stack import BraydenStack

# example tests. To run these tests, uncomment this file along with the example
# resource in brayden/brayden_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BraydenStack(app, "brayden")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

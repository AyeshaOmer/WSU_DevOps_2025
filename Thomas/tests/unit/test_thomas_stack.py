import aws_cdk as core
import aws_cdk.assertions as assertions

from thomas.thomas_stack import ThomasStack

# example tests. To run these tests, uncomment this file along with the example
# resource in thomas/thomas_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ThomasStack(app, "thomas")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

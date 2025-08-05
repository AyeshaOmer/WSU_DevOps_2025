import aws_cdk as core
import aws_cdk.assertions as assertions

from week2prac.week2prac_stack import Week2PracStack

# example tests. To run these tests, uncomment this file along with the example
# resource in week2prac/week2prac_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Week2PracStack(app, "week2prac")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

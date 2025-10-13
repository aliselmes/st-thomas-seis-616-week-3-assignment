import aws_cdk as core
import aws_cdk.assertions as assertions

from assignment_3.assignment_3_stack import Assignment3Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in assignment_3/assignment_3_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Assignment3Stack(app, "assignment-3")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

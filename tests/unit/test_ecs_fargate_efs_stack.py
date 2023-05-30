import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_fargate_efs.ecs_fargate_efs_stack import EcsFargateEfsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ecs_fargate_efs/ecs_fargate_efs_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsFargateEfsStack(app, "ecs-fargate-efs")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ecs_fargate_efs.ecs_fargate_efs_stack import EcsFargateEfsStack


app = cdk.App()

EcsFargateEfsStack(app, "EcsFargateEfsStack",

    env=cdk.Environment(account="123456789012",region="ap-southeast-2"),
    )

app.synth()

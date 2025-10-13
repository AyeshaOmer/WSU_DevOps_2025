#!/usr/bin/env python3
import os
import aws_cdk as cdk
from week2prac.pipeline_stack import WebMonitorPipelineStack

app = cdk.App()

WebMonitorPipelineStack(
    app,
    "WebMonitorPipelineStack",
    repo_string="Vrishtii/WSU_DevOps_2025",          
    codestar_connection_arn="arn:aws:codestar-connections:ap-southeast-2:934249453094:connection/c2c2afe8-69c0-4078-8ac2-328a9f626f66",
    branch="main",
    env=cdk.Environment(
        account="934249453094", 
        region="ap-southeast-2"
    ),
)

app.synth()

#!/usr/bin/env python3
import os

import aws_cdk as cdk

from week2prac.pipeline_stack import WebMonitorPipelineStack 


app = cdk.App()
WebMonitorPipelineStack(
    app,
    "WebMonitorPipelineStack",
    repo_string="https://github.com/Vrishtii/WSU_DevOps_2025#", 
    branch="main",                        
    codestar_connection_arn="arn:aws:codestar-connections:ap-southeast-2:123456789012:connection/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # <-- CHANGE
    deploy_region="ap-southeast-2",
                env=cdk.Environment(account="934249453094", region="ap-southeast-2")

    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()

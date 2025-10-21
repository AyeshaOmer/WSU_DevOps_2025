#!/usr/bin/env python3
import os

import aws_cdk as cdk

from manh_dev_ops_project.monitor import MonitorStack
from manh_dev_ops_project.api import ApiStack


app = cdk.App()

# Create monitoring stack first to get access to its config table
monitoring_stack = MonitorStack(app, "monitorWeb",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)


# Pass the config table from monitoring stack to API stack
ApiStack(app, "ApiStack",
    config_table=monitoring_stack.web_table,
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

app.synth()

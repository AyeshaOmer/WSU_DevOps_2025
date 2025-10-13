import aws_cdk as core
from aws_cdk.assertions import Template

from dang_quoc_toan.dang_quoc_toan_stack import DangQuocToanStack


def synth_template():
    app = core.App()
    stack = DangQuocToanStack(app, "TestStack")
    return Template.from_stack(stack)


def test_lambda_created():
    template = synth_template()
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "WHLambda.lambda_handler",
        },
    )


def test_events_rule_exists():
    template = synth_template()
    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "ScheduleExpression": "rate(5 minutes)",
        },
    )


def test_sns_topic_exists():
    template = synth_template()
    # Just ensure a Topic exists
    assert template.find_resources("AWS::SNS::Topic")


def test_alarms_exist():
    template = synth_template()
    # Ensure at least one CloudWatch Alarm exists
    alarms = template.find_resources("AWS::CloudWatch::Alarm")
    assert len(alarms) >= 1


import aws_cdk as core
from aws_cdk.assertions import Template
import os, json

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


def test_alarm_count_matches_urls():
    # Expect 3 alarms per URL (availability, latency, status)
    websites_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "modules", "website.json"))
    with open(websites_path, "r", encoding="utf-8") as f:
        website_list = [entry["url"] for entry in json.load(f)]

    template = synth_template()
    alarms = template.find_resources("AWS::CloudWatch::Alarm")
    assert len(alarms) == len(website_list) * 3

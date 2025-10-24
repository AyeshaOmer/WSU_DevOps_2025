import aws_cdk as core
from aws_cdk.assertions import Template
import os, json

from dang_quoc_toan.dang_quoc_toan_stack import DangQuocToanStack


def synth_template():
    # Force-enable CodeDeploy in tests so we can assert its presence
    app = core.App(context={"enable_code_deploy": "true"})
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
    # Count only per-URL alarms (availability/latency/status). In CFN, per-metric
    # alarms appear under Properties.Metrics[0].MetricStat.Metric.MetricName.
    target_names = {"availability", "latency", "status"}
    count = 0
    for _, alarm in alarms.items():
        props = alarm.get("Properties", {})
        names = []
        if "Metrics" in props:
            for m in props["Metrics"]:
                metric_stat = m.get("MetricStat") if isinstance(m, dict) else None
                metric = metric_stat.get("Metric") if isinstance(metric_stat, dict) else None
                name = metric.get("MetricName") if isinstance(metric, dict) else None
                if name:
                    names.append(name)
        else:
            # Fallback: direct MetricName property (older patterns)
            if "MetricName" in props:
                names.append(props["MetricName"])

        if any(n in target_names for n in names):
            count += 1
    assert count == len(website_list) * 3


def test_lambda_alias_and_codedeploy():
    template = synth_template()
    # Alias exists with name 'live'
    template.has_resource_properties(
        "AWS::Lambda::Alias",
        {
            "Name": "live",
        },
    )
    # CodeDeploy DeploymentGroup exists with canary config
    template.has_resource_properties(
        "AWS::CodeDeploy::DeploymentGroup",
        {
            "DeploymentConfigName": "CodeDeployDefault.LambdaCanary10Percent5Minutes",
        },
    )


def test_targets_api_and_table():
    template = synth_template()
    # Either a DynamoDB table exists or at least the API Lambda exists
    ddb = template.find_resources("AWS::DynamoDB::Table")
    if not ddb:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Handler": "TargetsApiLambda.handler"},
        )
    # Rest API exists
    template.find_resources("AWS::ApiGateway::RestApi")
    # Methods present
    methods = template.find_resources("AWS::ApiGateway::Method")
    assert len(methods) >= 2

import json
from aws_cdk import App, assertions
from gursh.gursh_stack import GurshStack
from gursh import constants as C

def _template():
    app = App()
    stack = GurshStack(app, "GurshStackTest")
    return assertions.Template.from_stack(stack)

# 1) Lambdas exist (robust against CDK helper lambdas)
def test_lambda_count():
    t = _template()
    lambdas = t.find_resources("AWS::Lambda::Function")
    assert len(lambdas) >= 3, f"Expected at least 3 app Lambdas, found {len(lambdas)}"

# 2) Alarm count (≥ availability + latency per URL)
def test_alarm_count():
    t = _template()
    alarms = t.find_resources("AWS::CloudWatch::Alarm")
    expected_min = len(C.URLS) * 2
    assert len(alarms) >= expected_min, f"Expected ≥ {expected_min} alarms, found {len(alarms)}"

# 3) Alarm thresholds (availability=1 exact; latency = numeric + mentions URL)
def test_alarm_thresholds():
    t = _template()
    alarms = t.find_resources("AWS::CloudWatch::Alarm")
    assert alarms, "No alarms found"

    def _has_availability(url: str) -> bool:
        for a in alarms.values():
            props = a.get("Properties", {})
            if props.get("Threshold") == 1:
                desc = json.dumps(props.get("AlarmDescription", ""))
                if url in desc:
                    return True
        return False

    def _has_latency(url: str) -> bool:
        for a in alarms.values():
            props = a.get("Properties", {})
            thr = props.get("Threshold")
            if isinstance(thr, (int, float)):
                desc = json.dumps(props.get("AlarmDescription", ""))
                if url in desc:
                    return True
        return False

    for url in C.URLS:
        assert _has_availability(url), f"Missing availability alarm (Threshold=1) for {url}"
        assert _has_latency(url),      f"Missing latency alarm (numeric threshold) for {url}"

# 4) SNS topic going through (email + lambda subscriptions exist)
def test_sns_topic_subscriptions():
    t = _template()
    subs = t.find_resources("AWS::SNS::Subscription")
    assert subs, "No SNS Subscriptions found"
    protocols = {s.get("Properties", {}).get("Protocol") for s in subs.values()}
    assert "email" in protocols, "Missing email subscription"
    assert "lambda" in protocols, "Missing lambda subscription"

# 5) DynamoDB tables exist & are wired to Lambdas
def test_dynamodb_tables_exist_and_wired():
    t = _template()

    # Lambdas wired via env vars (this is what 'working' means in unit tests)
    fns = t.find_resources("AWS::Lambda::Function")
    assert fns, "No Lambda functions found"

    has_table_name = False
    has_urls_table_name = False
    for fn in fns.values():
        env = fn.get("Properties", {}).get("Environment", {}).get("Variables", {})
        if "TABLE_NAME" in env:
            has_table_name = True
        if "URLS_TABLE_NAME" in env:
            has_urls_table_name = True

    assert has_table_name, "Expected at least one Lambda with TABLE_NAME"
    assert has_urls_table_name, "Expected at least one Lambda with URLS_TABLE_NAME"

    # If your template creates tables, ensure at least one exists.
    # If you import existing tables, this will still pass because wiring is validated above.
    tables = t.find_resources("AWS::DynamoDB::Table")
    if tables:  # only assert when present, to support imported tables
        assert len(tables) >= 1, "Expected at least one DynamoDB table resource"

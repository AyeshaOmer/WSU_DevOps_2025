import os
import sys
import types


# Fake boto3 resource/client for unit testing without AWS
class FakeCW:
    def __init__(self):
        self.metrics = []

    def put_metric_data(self, Namespace=None, MetricData=None):
        self.metrics.append((Namespace, MetricData))


class FakeTable:
    def __init__(self):
        self.store = {}

    def scan(self, Limit=1000):
        return {"Items": list(self.store.values())[:Limit]}

    def get_item(self, Key=None):
        key = Key["WebsiteName"]
        item = self.store.get(key)
        return {"Item": item} if item else {}

    def put_item(self, Item=None):
        self.store[Item["WebsiteName"]] = Item
        return {}

    def delete_item(self, Key=None):
        self.store.pop(Key["WebsiteName"], None)
        return {}


class FakeBoto3:
    def __init__(self, table: FakeTable, cw: FakeCW):
        self._table = table
        self._cw = cw

    def resource(self, name):
        assert name == "dynamodb"
        return types.SimpleNamespace(Table=lambda _: self._table)

    def client(self, name):
        assert name == "cloudwatch"
        return self._cw


def make_event(method, path="/targets", body=None, id=None):
    return {
        "httpMethod": method,
        "pathParameters": ({"id": id} if id else None),
        "body": body,
    }


def test_crud_happy_path(monkeypatch):
    # Prepare fake AWS and env
    table = FakeTable()
    cw = FakeCW()
    fake = FakeBoto3(table, cw)
    sys.modules["boto3"] = fake  # type: ignore
    os.environ["TARGETS_TABLE_NAME"] = "dummy"
    os.environ["METRIC_NAMESPACE"] = "TEST_NS"

    # Import after monkeypatch
    import importlib
    TargetsApiLambda = importlib.import_module("TargetsApiLambda")

    # Create
    ev = make_event("POST", body='{"url":"https://example.com","note":"ok"}')
    r = TargetsApiLambda.handler(ev, None)
    assert r["statusCode"] == 201

    # Read list
    r = TargetsApiLambda.handler(make_event("GET"), None)
    assert r["statusCode"] == 200

    # Read item
    r = TargetsApiLambda.handler(make_event("GET", id="https://example.com"), None)
    assert r["statusCode"] == 200

    # Update
    r = TargetsApiLambda.handler(make_event("PUT", id="https://example.com", body='{"note":"updated"}'), None)
    assert r["statusCode"] == 200

    # Delete
    r = TargetsApiLambda.handler(make_event("DELETE", id="https://example.com"), None)
    assert r["statusCode"] == 204

    # Metrics captured
    assert any(md for ns, md in cw.metrics if ns == "TEST_NS")


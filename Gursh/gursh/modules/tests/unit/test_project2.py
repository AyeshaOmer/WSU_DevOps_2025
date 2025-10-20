# Ensure env is set BEFORE importing the module
import os
os.environ.setdefault("TABLE_NAME", "UrlsTableTest")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-2")

import json
import pytest
from moto import mock_aws
import boto3

# Import your CRUD Lambda module
from gursh.modules import APIgateway

# Use the correct handler name from your file
has_handler = hasattr(APIgateway, "lambda_handler")
pytestmark = pytest.mark.skipif(not has_handler, reason="CRUD Lambda handler not implemented")

def _event(method, path="/urls", query=None, body=None):
    return {
        "httpMethod": method,
        "path": path,
        "queryStringParameters": query or None,
        "body": json.dumps(body) if isinstance(body, dict) else body,
        "headers": {"Content-Type": "application/json"},
    }

@pytest.fixture
def moto_table(monkeypatch):
    # Create a fake DynamoDB table and attach it to the module under test
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name=os.environ["AWS_DEFAULT_REGION"])
        table = ddb.create_table(
            TableName=os.environ["TABLE_NAME"],
            KeySchema=[{"AttributeName": "url", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "url", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        # Point APIgateway.table to moto table so all ops go here
        monkeypatch.setattr(APIgateway, "table", table, raising=False)
        yield table

# POST -> returns 200 with {"message":"added","item":{...}}
def test_post_creates_item(moto_table):
    url = "https://example.com"
    r = APIgateway.lambda_handler(_event("POST", body={"url": url}), None)
    assert r["statusCode"] == 200
    body = json.loads(r["body"])
    assert body.get("message") == "added"
    assert body.get("item", {}).get("url") == url
    # verify in table
    item = moto_table.get_item(Key={"url": url}).get("Item")
    assert item and item["url"] == url

# GET (list) -> returns 200 with an array of urls
def test_get_lists_items(moto_table):
    urls = ["https://a.com", "https://b.com"]
    for u in urls:
        APIgateway.lambda_handler(_event("POST", body={"url": u}), None)

    r = APIgateway.lambda_handler(_event("GET"), None)
    assert r["statusCode"] == 200
    body = json.loads(r["body"])
    assert isinstance(body, list)
    for u in urls:
        assert u in body

# PUT -> returns 200 with {"message":"updated","item":{...}}
def test_put_updates_item(moto_table):
    url = "https://update.me"
    APIgateway.lambda_handler(_event("POST", body={"url": url}), None)

    r = APIgateway.lambda_handler(_event("PUT", body={"url": url, "note": "x"}), None)
    assert r["statusCode"] == 200
    b = json.loads(r["body"])
    assert b.get("message") == "updated"
    # still present (and overwritten/updated)
    item = moto_table.get_item(Key={"url": url}).get("Item")
    assert item and item["url"] == url

# DELETE -> returns 200 with {"message": "deleted <url>"}
def test_delete_removes_item(moto_table):
    url = "https://delete.me"
    APIgateway.lambda_handler(_event("POST", body={"url": url}), None)

    r = APIgateway.lambda_handler(_event("DELETE", query={"url": url}), None)
    assert r["statusCode"] == 200
    body = json.loads(r["body"])
    assert "deleted" in body.get("message", "")

    # list should no longer include it
    r2 = APIgateway.lambda_handler(_event("GET"), None)
    listed = json.loads(r2["body"])
    assert url not in listed

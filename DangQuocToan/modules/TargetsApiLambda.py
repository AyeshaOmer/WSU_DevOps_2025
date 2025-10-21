import os
import json
import time
import boto3


TABLE_NAME = os.environ.get("TARGETS_TABLE_NAME", "")
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "WSU_CRAWLER")

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(TABLE_NAME) if TABLE_NAME else None
_cw = boto3.client("cloudwatch")


def _response(status_code: int, body: dict | list | str, headers: dict | None = None):
    base_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }
    if headers:
        base_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": base_headers,
        "body": json.dumps(body),
    }


def _put_metric(name: str, value: float):
    try:
        _cw.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[
                {
                    "MetricName": name,
                    "Value": float(value),
                    "Unit": "Milliseconds",
                }
            ],
        )
    except Exception:
        # Metrics are best-effort; do not fail the API on metric error
        pass


def handler(event, context):
    # Lambda proxy integration event
    method = (event.get("httpMethod") or "").upper()
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("id")

    if method == "OPTIONS":
        return _response(200, {"ok": True})

    if _table is None:
        return _response(500, {"error": "Targets table not configured"})

    # Parse body if present
    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        except json.JSONDecodeError:
            return _response(400, {"error": "Invalid JSON body"})

    # Routes
    # GET /targets or GET /targets/{id}
    if method == "GET" and not item_id:
        start = time.time()
        resp = _table.scan(Limit=1000)
        items = resp.get("Items", [])
        elapsed_ms = (time.time() - start) * 1000.0
        _put_metric("crud_read_time_ms", elapsed_ms)
        return _response(200, {"items": items}, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})

    if method == "GET" and item_id:
        start = time.time()
        resp = _table.get_item(Key={"WebsiteName": item_id})
        item = resp.get("Item")
        elapsed_ms = (time.time() - start) * 1000.0
        _put_metric("crud_read_time_ms", elapsed_ms)
        if not item:
            return _response(404, {"error": "Not found"}, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})
        return _response(200, item, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})

    # POST /targets { url, ... }
    if method == "POST" and not item_id:
        url = body.get("url")
        if not url:
            return _response(400, {"error": "Missing 'url'"})
        item = {"WebsiteName": url}
        # include any other fields
        for k, v in body.items():
            if k != "url":
                item[k] = v
        start = time.time()
        _table.put_item(Item=item)
        elapsed_ms = (time.time() - start) * 1000.0
        _put_metric("crud_write_time_ms", elapsed_ms)
        return _response(201, item, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})

    # PUT /targets/{id} { ...attributes }
    if method == "PUT" and item_id:
        # simple replace/merge using put_item for brevity
        item = {"WebsiteName": item_id, **body}
        start = time.time()
        _table.put_item(Item=item)
        elapsed_ms = (time.time() - start) * 1000.0
        _put_metric("crud_write_time_ms", elapsed_ms)
        return _response(200, item, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})

    # DELETE /targets/{id}
    if method == "DELETE" and item_id:
        start = time.time()
        _table.delete_item(Key={"WebsiteName": item_id})
        elapsed_ms = (time.time() - start) * 1000.0
        _put_metric("crud_write_time_ms", elapsed_ms)
        return _response(204, {"deleted": item_id}, headers={"x-operation-time-ms": f"{elapsed_ms:.2f}"})

    return _response(405, {"error": "Method not allowed"})


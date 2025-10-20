# gursh/modules/WHlambda.py
import os
import time
import urllib.request
import boto3
from datetime import datetime, timezone
from decimal import Decimal

URL_NAMESPACE  = os.environ.get("URL_NAMESPACE", "WebsiteMonitoring")
RESULTS_TBL    = os.environ.get("TABLE_NAME", "UnitTestResults")
URLS_TBL_NAME  = os.environ.get("URLS_TABLE_NAME", "UnitTestUrls")
DIMENSION_NAME = os.environ.get("DIMENSION_NAME", "URL")

cw  = boto3.client("cloudwatch")
ddb = boto3.resource("dynamodb")

# Monkeypatch-friendly handles (tests can set these directly)
resT = None
urlsT = None

def _get_results_table():
    global resT
    if resT is not None:
        return resT
    return ddb.Table(RESULTS_TBL)

def _get_urls_table():
    global urlsT
    if urlsT is not None:
        return urlsT
    return ddb.Table(URLS_TBL_NAME)

def _get_urls():
    t = _get_urls_table()
    urls, resp = [], t.scan(ProjectionExpression="#u", ExpressionAttributeNames={"#u": "url"})
    while True:
        urls += [i["url"] for i in resp.get("Items", []) if i.get("url")]
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        resp = t.scan(
            ProjectionExpression="#u",
            ExpressionAttributeNames={"#u": "url"},
            ExclusiveStartKey=lek,
        )
    # de-dup preserve order
    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered

def _publish(namespace, name, dim_val, value, unit):
    cw.put_metric_data(
        Namespace=namespace,
        MetricData=[{
            "MetricName": name,
            "Dimensions": [{"Name": DIMENSION_NAME, "Value": dim_val}],
            "Value": float(value),
            "Unit": unit,
        }]
    )

def _check(url: str):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.getcode()
        latency_ms = (time.time() - start) * 1000.0
        avail = 1 if status == 200 else 0
    except Exception as e:
        print(f"[{url}] error: {e}")
        latency_ms, avail = 0.0, 0
    return avail, latency_ms

def _write(url: str, avail: int, lat_ms: float):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    _get_results_table().put_item(Item={
        "pk": f"{url}#{ts}",
        "url": url,
        "availability": Decimal(str(int(avail))),
        "latency_ms": Decimal(str(round(lat_ms, 2))),
        "timestamp": ts,
    })

def lambda_handler(event, context):
    urls = _get_urls()
    if not urls:
        print("No URLs to check.")
        return {"statusCode": 200, "checked": 0}

    checked = 0
    for url in urls:
        avail, lat_ms = _check(url)
        _publish(URL_NAMESPACE, "URL_MONITOR_AVAILABILITY", url, avail, "Count")
        _publish(URL_NAMESPACE, "URL_MONITOR_LATENCY", url, lat_ms, "Milliseconds")
        _write(url, avail, lat_ms)
        print(f"[{url}] availability={avail}, latency_ms={lat_ms:.2f}")
        checked += 1

    return {"statusCode": 200, "checked": checked}

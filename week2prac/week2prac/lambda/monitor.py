import time
import json
import os
import boto3
import urllib.request

cloudwatch = boto3.client("cloudwatch")
NAMESPACE = os.getenv("METRIC_NAMESPACE", "NYTMonitor")

def _put_metrics(site: str, latency_ms: float | None, status_code: int | None, available: int):
    data = [{
        "MetricName": "Availability",
        "Dimensions": [{"Name": "Site", "Value": site}],
        "Value": available,
        "Unit": "Count",
    }]
    if latency_ms is not None:
        data.append({
            "MetricName": "Latency",
            "Dimensions": [{"Name": "Site", "Value": site}],
            "Value": latency_ms,
            "Unit": "Milliseconds",
        })
    if status_code is not None:
        data.append({
            "MetricName": "StatusCode",
            "Dimensions": [{"Name": "Site", "Value": site}, {"Name": "Code", "Value": str(status_code)}],
            "Value": 1,
            "Unit": "Count",
        })
    cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=data)

def lambda_handler(event, context):
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    with open(sites_path, "r", encoding="utf-8") as f:
        sites = json.load(f)

    for site in sites:
        start = time.time()
        latency_ms = None
        status_code = None
        available = 0
        try:
            req = urllib.request.Request(site, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.status
                latency_ms = (time.time() - start) * 1000.0
                available = 1 if status_code == 200 else 0
        except Exception:
            available = 0

        _put_metrics(site, latency_ms, status_code, available)

    return {"ok": True, "sites_checked": len(sites)}

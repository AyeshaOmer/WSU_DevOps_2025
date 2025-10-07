import urllib3
import time
import json
import os
import boto3

# CloudWatch client
cloudwatch = boto3.client("cloudwatch")

# Namespace from environment
NAMESPACE = os.getenv("METRIC_NAMESPACE", "NYTMonitor")

def _put_metrics(site: str, latency_ms: float | None, status_code: int | None, available: int):
    """
    Publish metrics to CloudWatch for a single website.
    """
    metric_data = [
        {
            "MetricName": "Availability",
            "Dimensions": [{"Name": "Site", "Value": site}],
            "Value": available,
            "Unit": "Count",
        }
    ]

    if latency_ms is not None:
        metric_data.append({
            "MetricName": "Latency",
            "Dimensions": [{"Name": "Site", "Value": site}],
            "Value": latency_ms,
            "Unit": "Milliseconds",
        })

    if status_code is not None:
        metric_data.append({
            "MetricName": "StatusCode",
            "Dimensions": [{"Name": "Site", "Value": site}, {"Name": "Code", "Value": str(status_code)}],
            "Value": 1,
            "Unit": "Count",
        })

    cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metric_data)

def lambda_handler(event, context):
    """
    Lambda handler to crawl multiple websites and publish metrics.
    """
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    with open(sites_path, "r", encoding="utf-8") as f:
        sites = json.load(f)

    http = urllib3.PoolManager()

    for site in sites:
        start = time.time()
        latency_ms = None
        status_code = None
        available = 0

        try:
            resp = http.request(
                "GET",
                site,
                timeout=urllib3.Timeout(connect=3.0, read=10.0),
                retries=False
            )
            latency_ms = (time.time() - start) * 1000
            status_code = resp.status
            available = 1 if status_code == 200 else 0
        except Exception:
            available = 0

        _put_metrics(site, latency_ms, status_code, available)

    return {"ok": True, "sites_checked": len(sites)}

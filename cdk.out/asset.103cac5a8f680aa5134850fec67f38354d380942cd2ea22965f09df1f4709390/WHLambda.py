from Publish_metric import publish_metric
import urllib.request
import urllib.error
import time
import boto3
import os
import json

with open(os.path.join(os.path.dirname(__file__), "website.json")) as f:
    URL_LIST = [entry["url"] for entry in json.load(f)]

URL_NAMESPACE = "THOMASPROJECT_WSU2025"
METRIC_AVAIL = "availability"
METRIC_LAT = "latency"
METRIC_STATUS = "status"


def crawl_url(url: str):
    print(f"Crawling {url}")
    start = time.time()
    try:
        req = urllib.request.Request(url, headers = {"User-Agent": "url-canary/1.0"})
        with urllib.request.urlopen(req, timeout = 5 ) as resp: 
             latency = (time.time() - start) * 1000.0 # convert sencond to millisecond
             status = resp.getcode() or 0
             availability = 1 if 200 <= status < 400 else 0
             return availability, latency, status
    except (urllib.error.HTTPError) as e:
            latency = (time.time() - start) * 1000.0 # convert sencond to millisecond
            status = e.code or 0
            availability = 1 if 200 <= status < 400 else 0
            return availability, latency, status
    except Exception:
            # timeout, DNS errors, connection failures, etc.
            return 0, 0.0, 0

def lambda_handler(event, context):
    for URL in URL_LIST:
        availability, latency, status = crawl_url(URL)
        print(f"Availability: {availability}, Latency: {latency} ms, Status: {status}")
        dimension = [{'Name': 'WebsiteName', 'Value': URL}]
        publish_metric(URL_NAMESPACE, METRIC_AVAIL, availability, dimension)
        publish_metric(URL_NAMESPACE, METRIC_LAT, latency, dimension)
        publish_metric(URL_NAMESPACE, METRIC_STATUS, status, dimension)
    
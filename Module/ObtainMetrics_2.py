import requests
import time
import publish_metric

URL_NAMESPACE = "PhuocTaiTranProject_WSU2025"
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"

def handler(event, context):
    urls = [
        "https://www.google.com",
        "https://www.github.com",
        "www.skipq.org"
    ]

    report = []
    for url in urls:
        entry = {"url": url}
        try:
            # Attempt to fetch the URL
            start = time.time()
            resp = requests.get(url, timeout=5)
            latency = time.time() - start

            # Log the latency
            entry["latency"] = latency
            entry["status_code"] = resp.status_code

            # Check if the URL is reachable
            entry["result"] = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"

            # Publish latency metric
            dimension = [{"Name": "URL", "Value": url}]
            publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_LATENCY, dimension, latency)

            # Publish availability metric (1 for OK, 0 for not OK)
            avail = 1 if resp.status_code == 200 else 0
            publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimension, avail)

        # If the URL is not reachable, log the error
        except requests.RequestException as e:
            entry["status_code"] = None
            entry["latency"] = None
            entry["result"] = f"Error: {e}"

            # Publish availability metric as 0 for error
            dimension = [{"Name": "URL", "Value": url}]
            publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimension, 0)

        report.append(entry)

    # Build a plain-text body with one "<URL> <status> <latency" per line
    lines = [f"{e['url']} {e['result']} {e['latency']} \n" for e in report]


    return {
        "statusCode": 200,
        "body": "".join(lines)
    }






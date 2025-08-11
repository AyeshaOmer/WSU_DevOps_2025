import requests
import time
# import boto3
# import ObtainMetrics as metrics


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
            entry["result"]      = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}" 

        # If the URL is not reachable, log the error
        except requests.RequestException as e:
            entry["status_code"] = None
            entry["latency"] = None
            entry["result"]      = f"Error: {e}"
        report.append(entry)

    # Build a plain-text body with one "<URL> <status> <latency" per line
    lines = [f"{e['url']} {e['result']} {e['latency']} \n" for e in report]


    return {
        "statusCode": 200,
        "body": "".join(lines)
    }




   

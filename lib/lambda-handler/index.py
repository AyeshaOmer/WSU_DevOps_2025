import requests

def handler(event, context):
    urls = [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.microsoft.com"
    ]

    report = []
    for url in urls:
        entry = {"url": url}
        try:
            resp = requests.get(url, timeout=5)
            entry["status_code"] = resp.status_code
            entry["result"]      = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            entry["status_code"] = None
            entry["result"]      = f"Error: {e}"
        report.append(entry)

    # Build a plain-text body with one "<URL> <status>" per line
    lines = [f"{e['url']} {e['result']}" for e in report]
    body_text = "\n".join(lines)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": body_text
    }
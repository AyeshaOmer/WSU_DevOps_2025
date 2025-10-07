import urllib.request
from time import time
import publish_metric
from constantSource import URL_MONITOR_AVAILABILITY, URL_MONITOR_LATENCY, URL_NAMESPACE, URLS

def handler(event, context):
    print(f"Monitoring {len(URLS)} URLs")
    
    for url in URLS:
        avail, latency = 0, 5.0
        try:
            start = time()
            response = urllib.request.urlopen(url, timeout=5)
            latency = time() - start
            avail = 1 if 200 <= response.getcode() < 300 else 0
            print(f" Get data success {url}: {response.getcode()}, {latency:.3f}s")
        except Exception as e:
            print(f"Get data unsuccessful {url}: {type(e).__name__}")
        # Publish metrics
        dimensions = [{"Name": "URL", "Value": url}]
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimensions, avail)
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_LATENCY, dimensions, latency)







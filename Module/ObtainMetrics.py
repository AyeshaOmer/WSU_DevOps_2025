import urllib.request
from time import time
import publish_metric
from constantSource import(
    URL_MONITOR_AVAILABILITY,
    URL_MONITOR_LATENCY,
    URL_NAMESPACE,
    URLS 
)


def handler(event, context):
    print(f"Processing {len(URLS)} URLs: {URLS}")
    
    for i, url in enumerate(URLS):
        print(f"Processing URL {i+1}/{len(URLS)}: {url}")
        avail = 0  # Default values
        latency = 5.0
        
        try:
            start = time()
            response = urllib.request.urlopen(url, timeout=5)
            latency = time() - start
            # Get status code using getcode() method
            status_code = response.getcode()
            # Availability based on successful response (status 200-299)
            avail = 1 if 200 <= status_code < 300 else 0
            print(f"SUCCESS: {url} - Status: {status_code}, Latency: {latency:.3f}s, Available: {avail}")
        except urllib.error.HTTPError as e:
            latency = 5.0
            avail = 0
            print(f"HTTP ERROR: {url} - Status: {e.code}, Reason: {e.reason}")
        except urllib.error.URLError as e:
            latency = 5.0
            avail = 0
            print(f"URL ERROR: {url} - Reason: {e.reason}")
        except Exception as e:
            latency = 5.0
            avail = 0
            print(f"GENERAL ERROR: {url} - Exception: {str(e)}, Type: {type(e).__name__}")
        
        # Always publish metrics, regardless of success or failure
        print(f"About to publish metrics for {url}: Availability={avail}, Latency={latency}")
        try:
            dimension = [{"Name": "URL", "Value": url}]
            publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimension, avail)
            print(f"Published availability metric for {url}: {avail}")
            
            publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_LATENCY, dimension, latency)
            print(f"Published latency metric for {url}: {latency}")
            
            print(f"METRICS PUBLISHED for {url}: Availability={avail}, Latency={latency}")
        except Exception as e:
            print(f"METRIC PUBLISH ERROR for {url}: {str(e)}")
    
    print("Finished processing all URLs")







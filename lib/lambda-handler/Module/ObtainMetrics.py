import publish_metric
from constantSource import(
    URL_MONITOR_AVAILABILITY,
    URL_MONITOR_LATENCY,
    URL_NAMESPACE,
    URLS 
)


def handler(event, context):
    avail = 1
    latency = 0.02
    for url in URLS:
        dimension = [{"Name": "URL", "Value": url}]
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimension, avail)
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_LATENCY, dimension, latency)


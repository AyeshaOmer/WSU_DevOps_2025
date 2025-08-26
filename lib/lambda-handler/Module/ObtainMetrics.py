import publish_metric 


URL = ['www.skipq.org', 'www.bbc.com', 'www.truckersmp.com']
URL_MONITOR_AVAILABILITY    = "Availability"
URL_MONITOR_LATENCY         = "Latency"
URL_NAMESPACE               = "PhuocTaiTranProject_WSU2025"


def handler(event, context):
    

    # compute the availability for my URL
    avail = 1

    # compute the latency for my URL
    latency = 0.02

    for url in URL:
        dimension = [{"Name": "URL", "Value": url}]
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, dimension, avail)
        publish_metric.publish_metric(URL_NAMESPACE, URL_MONITOR_LATENCY, dimension, latency)


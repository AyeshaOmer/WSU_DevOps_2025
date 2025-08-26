import json
import logging
import urllib3
import time
import publish_metric

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

URLS=["www.google.com", "www.youtube.com", "www.coolmathgames.com"]
url_latency = []
url_avail = []
url_size=[]
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "WebHelperDashboard"
URL_MONITOR_SIZE = "ResponseSize"


def lambda_handler(event, context):
    
    # Take in a url and output the status code and latency
    #url = event['url']
    for i in range(len(URLS)):
        startTime = time.time()
        httpResponse = http.request('GET', URLS[i])
        endTime = time.time()
        if httpResponse.status == 200:
            url_avail.append(1)
        else:
            url_avail.append(0)
        url_latency.append(endTime - startTime)
        url_size.append(len(httpResponse.data))
        
        #data being published
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, URLS[i], url_avail[i])
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_LATENCY, URLS[i], url_latency[i])
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_SIZE, URLS[i], url_size[i])
        data = {"url": URLS[i], "body": url_avail[i], "latency": url_latency[i]}

        
    #logger.info(f"CloudWatch logs group: {context.log_group_name}")


    # return the calculated area as a JSON string
    return json.dumps(data)


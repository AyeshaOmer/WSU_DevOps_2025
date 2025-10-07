## Web Health Lambda Function
# This Lambda function is designed to monitor the health of a web resource.

import json
import time
import urllib.request
from publish_metric import publish
import constants

URLS = constants.MONITORED_URLS
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_MONITOR_MEMORY = "Memory" # user package, pre defined names spaces include lambda, it calculculates how much power it consumes
URL_MONITOR_SIZE = "ResponseSize"
URL_NAMESPACE = "EUGENEPROJECT_WSU2025"

def lambda_handler(event, context):
    print("Hello from Lambda!")
    results = []
    
    for URL in URLS:
        try:
            start_time = time.time() # records request duration
            response = urllib.request.urlopen(URL, timeout = 5) # request fails if no response in 5 sec
            latency_ms = (time.time() - start_time) * 1000 # calculate latency in ms
        
            if response.status == 200: # check if website is available, 200 means success
                avail = 1 
            else:
                avail = 0

            latency = latency_ms
            
            # Read response body to get actual size
            body = response.read()
            size_bytes = len(body)

            # Get current memory usage (in MB)
            memory_mb = float(context.memory_limit_in_mb) + (size_bytes / (1024 * 1024))

            message = {
                "url": URL,
                "availability": avail,
                "latency_ms": latency,
                "status_code": response.status,
                "response_size": size_bytes,
                "memory_mb": memory_mb
            }
        except Exception as e:
            availability = 0
            latency = 0
            memory_mb = float(context.memory_limit_in_mb)
            message = {
                "availability": 0, # prints that website is not available
                "latency_ms": 0, # prints latency is 0, as no user input
                "status_code": None,
                "response_size": None,
                "memory_mb": memory_mb,
                "error": str(e)
            }
        print(f"Health check for {URL}: {message}")
        results.append(message)
        # defines dimension for cloud watch
        dimension = [{"Name": "URL", "Value": URL}]

        # Send metric
        response1 = publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY,dimension, avail)
        response2 = publish(URL_NAMESPACE, URL_MONITOR_LATENCY,dimension, latency)
        response3 = publish(URL_NAMESPACE, URL_MONITOR_SIZE, dimension, size_bytes)
        response4 = publish(URL_NAMESPACE, URL_MONITOR_MEMORY, dimension, memory_mb)



    return {
        "statusCode": 200,
        "body": results
    }
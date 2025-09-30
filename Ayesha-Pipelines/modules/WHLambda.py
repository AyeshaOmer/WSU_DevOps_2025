import datetime
import urllib3

import constants as constants

from CloudWatch_putMetric import cloudWatchPutMetric 

def lambda_handler(event, context):
    values = dict()
    cw = cloudWatchPutMetric()
    
    dimensions = [
                    {'Name': 'url', 'Value': constants.URL_TO_MONITOR}
                 ]
    avail = get_availability()
    cw.put_data(constants.URL_MONITOR_NAMESPACE, constants.URL_MONITOR_METRIC_NAME_AVAILABILITY, dimensions, avail)
    
    latency = get_latency()
    cw.put_data(constants.URL_MONITOR_NAMESPACE, constants.URL_MONITOR_METRIC_NAME_LATENCY, dimensions, latency)
    
    values.update({"avaiability":avail, "Latency":latency})
    return values

    
def get_availability():
    http = urllib3.PoolManager()
    response = http.request("GET", constants.URL_TO_MONITOR)
    if response.status==200 or response.status==201:
        return 1.0
    else: 
        return 0.0
        
def get_latency():
    http = urllib3.PoolManager()        # Creating a PoolManager instance for sending requests.
    start = datetime.datetime.now()
    response = http.request("GET", constants.URL_TO_MONITOR) #  Sending a GET request and getting back response as HTTPResponse object.
    end = datetime.datetime.now()       # check time after getting the website contents
    delta = end - start                 #take time difference
    latencySec = round(delta.microseconds * .000001, 6) 
    return latencySec
import json
import logging
import urllib3
import time
import modules.publish_metric
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table("UrlTable")

def get_urls():
    # Get URLs from DynamoDB
    response = table.query(
        KeyConditionExpression='#type = :type',
        ExpressionAttributeNames={'#type': 'type'},
        ExpressionAttributeValues={':type': 'url'}
    )
    urls = [item['id'] for item in response['Items']]
    return urls # Fallback URLs

url_latency = []
url_avail = []
url_size=[]
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "WebHelperDashboard"
URL_MONITOR_SIZE = "ResponseSize"


def lambda_handler(event, context):
    
    # Get URLs from DynamoDB or fallback to defaults
    urls = get_urls()
    
    # Take in a url and output the status code and latency
    for i in range(len(urls)):
        startTime = time.time()
        try:
            httpResponse = http.request('GET', f'https://{urls[i]}')
            endTime = time.time()
            if httpResponse.status == 200:
                url_avail.append(1)
            else:
                url_avail.append(0)
            url_latency.append(endTime - startTime)
            url_size.append(len(httpResponse.data)/100000)
        except:
            url_avail.append(0)
            url_latency.append(0)
            url_size.append(0)
            logger.error(f"Failed to fetch {urls[i]}")
        
        #data being published
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, urls[i], url_avail[i])
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_LATENCY, urls[i], url_latency[i])
        publish_metric.publish(URL_NAMESPACE, URL_MONITOR_SIZE, urls[i], url_size[i])
        data = {"url": urls[i], "body": url_avail[i], "latency": url_latency[i]}

        
    #logger.info(f"CloudWatch logs group: {context.log_group_name}")


    # return the calculated area as a JSON string
    return json.dumps(data)
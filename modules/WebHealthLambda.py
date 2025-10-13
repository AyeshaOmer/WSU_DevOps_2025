import json
import logging
import urllib3
import time
from publish_metric import publish
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "WebHelperDashboard"
URL_MONITOR_SIZE = "ResponseSize"

def get_urls():
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        response = table.query(
            KeyConditionExpression='#type = :type',
            ExpressionAttributeNames={'#type': 'type'},
            ExpressionAttributeValues={':type': 'url'}
        )
        urls = [item['id'] for item in response['Items']]
        logger.info(f"Retrieved URLs from DynamoDB: {urls}")
        return urls
    except Exception as e:
        logger.error(f"Error retrieving URLs from DynamoDB: {str(e)}")
        return []

def lambda_handler(event, context):
    # Reset lists for each invocation
    url_latency = []
    url_avail = []
    url_size = []
    results = []
    
    urls = get_urls()
    if not urls:
        logger.warning("No URLs found in DynamoDB")
        return json.dumps({"message": "No URLs to monitor"})

    for url in urls:
        startTime = time.time()
        try:
            httpResponse = http.request('GET', f'https://{url}')
            endTime = time.time()
            
            availability = 1 if httpResponse.status == 200 else 0
            latency = endTime - startTime
            size = len(httpResponse.data)/100000
            
            url_avail.append(availability)
            url_latency.append(latency)
            url_size.append(size)
            
            # Publish metrics
            publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, url, availability)
            publish(URL_NAMESPACE, URL_MONITOR_LATENCY, url, latency)
            publish(URL_NAMESPACE, URL_MONITOR_SIZE, url, size)
            
            results.append({
                "url": url,
                "availability": availability,
                "latency": latency,
                "size": size
            })
            
        except Exception as e:
            logger.error(f"Error monitoring URL {url}: {str(e)}")
            url_avail.append(0)
            url_latency.append(0)
            url_size.append(0)
            
            publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY, url, 0)
            publish(URL_NAMESPACE, URL_MONITOR_LATENCY, url, 0)
            publish(URL_NAMESPACE, URL_MONITOR_SIZE, url, 0)
            
            results.append({
                "url": url,
                "availability": 0,
                "latency": 0,
                "size": 0,
                "error": str(e)
            })

    return json.dumps({
        "timestamp": time.time(),
        "results": results
    })
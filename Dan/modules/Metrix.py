import boto3
import time
import urllib3
import logging

def lambda_handler(event, context):
    websites = [
        {"name": "Google", "url": "https://www.google.com"},
        {"name": "Facebook", "url": "https://www.facebook.com"},
        {"name": "YouTube", "url": "https://www.youtube.com"}
    ]
    http = urllib3.PoolManager()
    metric_data_avail = []
    metric_data_lat = []
    metric_data_code = []

    for site in websites:
        start_time = time.time()
        try:
            response = http.request('GET', site["url"], timeout=10)
            latency = (time.time() - start_time) * 1000
            availability = 1 if 200 <= response.status < 400 else 0
            code = response.status

        except Exception:
            latency = (time.time() - start_time) * 1000
            availability = 0
            code = 0
        metric_data_avail.append({
            'MetricName': 'Availability',
            'Dimensions': [
                {'Name': 'Website', 'Value': site['name']},
                {'Name': 'URL', 'Value': site['url']}
            ],
            'Value': availability,
            'Unit': 'None'
        })
        metric_data_lat.append({
            'MetricName': 'Latency',
            'Dimensions': [
                {'Name': 'Website', 'Value': site['name']},
                {'Name': 'URL', 'Value': site['url']}
            ],
            'Value': latency,
            'Unit': 'Milliseconds'
        })
        metric_data_code.append({
            'MetricName': 'StatusCode',
            'Dimensions': [
                {'Name': 'Website', 'Value': site['name']},
                {'Name': 'URL', 'Value': site['url']}
            ],
            'Value': code,
            'Unit': 'None'
        })
        
    cloudwatch = boto3.client('cloudwatch')
    # Combine all metric data into a single call
    metric_data_all = metric_data_avail + metric_data_lat + metric_data_code
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        response = cloudwatch.put_metric_data(
            Namespace='WebTest',
            MetricData=metric_data_all
        )
        logger.info('put_metric_data response: %s', response)
    except Exception as e:
        logger.exception('Failed to publish metrics: %s', e)
    return {'statusCode': 200, 'body': 'Metrics published'}
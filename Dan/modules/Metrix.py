import boto3
import time
import urllib3

def lambda_handler(event, context):
    websites = [
        {"name": "Google", "url": "https://www.google.com"},
        {"name": "Facebook", "url": "https://www.facebook.com"},
        {"name": "YouTube", "url": "https://www.youtube.com"}
    ]
    http = urllib3.PoolManager()
    metric_data = []
    for site in websites:
        start_time = time.time()
        try:
            response = http.request('GET', site["url"], timeout=10)
            latency = (time.time() - start_time) * 1000
            availability = 1 if 200 <= response.status < 400 else 0
        except Exception:
            latency = (time.time() - start_time) * 1000
            availability = 0
        metric_data.append({
            'MetricName': 'Availability',
            'Dimensions': [
                {'Name': 'Website', 'Value': site['name']},
                {'Name': 'URL', 'Value': site['url']}
            ],
            'Value': availability,
            'Unit': 'None'
        })
        metric_data.append({
            'MetricName': 'Latency',
            'Dimensions': [
                {'Name': 'Website', 'Value': site['name']},
                {'Name': 'URL', 'Value': site['url']}
            ],
            'Value': latency,
            'Unit': 'Milliseconds'
        })
        
    cloudwatch = boto3.client('cloudwatch')
    # Send all metrics in one call (as a list)
    cloudwatch.put_metric_data(
        Namespace='WebsiteMonitoring',
        MetricData=metric_data
    )
    return {'statusCode': 200, 'body': 'Metrics published'}
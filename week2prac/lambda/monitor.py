import urllib3
import time
import boto3

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    url = 'https://www.nytimes.com'
    http = urllib3.PoolManager()

    start_time = time.time()
    try:
        response = http.request('GET', url)
        latency = (time.time() - start_time) * 1000 
        status_code = response.status

        cloudwatch.put_metric_data(
            Namespace='NYTMonitor',
            MetricData=[
                {
                    'MetricName': 'Latency',
                    'Value': latency,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'Availability',
                    'Value': 1 if status_code == 200 else 0,
                    'Unit': 'Count'
                },
                {
                    'MetricName': f'StatusCode_{status_code}',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
    except Exception as e:
        cloudwatch.put_metric_data(
            Namespace='NYTMonitor',
            MetricData=[
                {
                    'MetricName': 'Availability',
                    'Value': 0,
                    'Unit': 'Count'
                }
            ]
        )
        raise e

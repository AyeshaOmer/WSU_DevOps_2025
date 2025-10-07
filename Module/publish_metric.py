import boto3
from datetime import datetime

def publish_metric(namespace, metric_name, dimensions, value):
    url = dimensions[0]['Value'] if dimensions else 'Unknown'
    
    boto3.client('cloudwatch').put_metric_data(
        Namespace=namespace,
        MetricData=[{
            'MetricName': metric_name,
            'Dimensions': dimensions,
            'Value': value,
            'Timestamp': datetime.utcnow()
        }]
    )
    
    print(f"📊 {metric_name}: {value} → {url}") 
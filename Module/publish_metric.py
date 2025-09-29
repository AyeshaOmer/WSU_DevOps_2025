import boto3
from datetime import datetime

def publish_metric(URL_NAMESPACE, metricName, dimension, value):
    client = boto3.client('cloudwatch')

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/put_metric_data.html
    client.put_metric_data(
        Namespace=URL_NAMESPACE,
        MetricData=[
            {
                'MetricName': metricName,
                'Dimensions': dimension,
                'Value': value,
                'Timestamp': datetime.utcnow()
            }
        ]    
    ) 
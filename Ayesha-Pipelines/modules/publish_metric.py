import boto3

def publish(NS, metricname, dimension, value)
    client = boto3.client('cloudwatch')
    
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/put_metric_data.html
    client.put_metric_data(
        Namespace=NS,
        MetricData=[
        {
            'MetricName': metricname,
            'Dimensions': dimension,
            'Value': value
        }
        ]
    )
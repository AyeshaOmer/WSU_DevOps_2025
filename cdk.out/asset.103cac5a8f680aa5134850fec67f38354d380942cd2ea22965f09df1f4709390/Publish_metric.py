import boto3

def publish_metric(namespace, metric_name, value, dimension):
    client = boto3.client('cloudwatch')

    unit = "None"
    if metric_name == "availability":
        unit = "Count"
    elif metric_name == "latency":
        unit = "Milliseconds"
    elif metric_name == "status":
        unit = "Count"

    client.put_metric_data(
        Namespace = namespace,
        MetricData = [
            {
                'MetricName': metric_name,
                'Dimensions': dimension,
                'Value': value,
                'Unit': unit
            }
        ]
    )

import boto3
def publish(NS, metric_name, dimension, value):

    client = boto3.client('cloudwatch')
    unit = 'Count'
    # Adjust unit based on metric type
    if metric_name == "Latency": 
        unit = 'Milliseconds'
    elif metric_name == "ResponseSize":
        unit = 'Bytes'
    elif metric_name == "Memory":
        unit = 'Megabytes'


    # Put metric data function: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/put_metric_data.html
    client.put_metric_data(
        Namespace=NS,
        MetricData=[ # data about availability metric data
            {
                'MetricName': metric_name, # name of metric (availability, latency, response size)
                'Dimensions': dimension, # website being monitored
                'Value': value, # Numeric value of the metric being reported
                'Unit': unit # Unit of the metric i.e milliseconds, bytes
            }
        ]
    )

'''
    client.put_metric_data(
        Namespace=URL_NAMESPACE,
        MetricData=[ # data about latency
            {
                'MetricName': URL_MONITOR_LATENCY,
                'Dimensions': [
                    {
                        'Name': 'URL',
                        'Value': 'https://www.youtube.com'
                    }
                ],
                'Unit': 'Seconds',
                'Value': latency
            }
        ]
    )
    '''
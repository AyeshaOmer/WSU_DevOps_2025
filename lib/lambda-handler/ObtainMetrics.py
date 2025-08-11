import boto3 

URL = "www.skipq.org"
URL_MONITOR_AVAILABILITY    = "Availability"
URL_MONITOR_LATENCY         = "Latency"
URL_NAMESPACE               = "PhuocTaiTranProject_WSU2025"


def lambda_handler(event, context):
    client = boto3.client('cloudwatch')

    # compute the availability for my URL
    avail = 1

    # compute the latency for my URL
    latency = 0.02

    response = client.put_metric_data(
        Namespace=URL_NAMESPACE,
        MetricData=[
            {
                'MetricName': URL_MONITOR_AVAILABILITY,
                'Dimensions': [
                    {
                        'Name': 'URL',
                        'Value': URL
                    }
                ],
                'Value': avail
            }
        ]    
    )
import boto3
import requests
import time

cloudwatch = boto3.client('cloudwatch')

WEBSITE = "https://www.bom.gov.au/nsw/"
WAN_MON_AVAILABILITY = "Availability"
WAN_MON_LATENCY  = "Ping"
WAN_MON_PACKETLOSS = "PacketLoss"
WAN_MANESPACE = "DevOps_22140027"

def lambda_handler(event, context):
    try:
        # Checks Ping timeing and latency
        start_time = time.time()
        response = requests.get(WEBSITE, timeout=10) # 10-second timeout
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000  

        # availability = 1 for success or 0 for failure
        # Checks for code 200
        availability_status = 1 if response.status_code == 200 else 0

        # Subbmit to CloudWatch

        #AVAILABILITY metric
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': WAN_MON_AVAILABILITY,
                    'Dimensions': [{'Name': 'URL', 'Value': WEBSITE}],
                    'Value': availability_status,
                    'Unit': 'None'
                },
            ],
            Namespace=WAN_MANESPACE
        )

        # Publish Latency metric
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': WAN_MON_LATENCY,
                    'Dimensions': [{'Name': 'URL', 'Value': WEBSITE}],
                    'Value': latency_ms,
                    'Unit': 'Milliseconds'
                },
            ],
            Namespace=WAN_MANESPACE
        )

        return {
            'statusCode': 200,
            'body': 'Metrics published to CloudWatch'
        }

    except requests.exceptions.RequestException as e:
        # If the request fails, the site is unavailable. Publish 0 for availability.
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': WAN_MON_AVAILABILITY,
                    'Dimensions': [{'Name': 'URL', 'Value': WEBSITE}],
                    'Value': 0,
                    'Unit': 'None'
                },
            ],
            Namespace=WAN_MANESPACE
        )
        # You could also publish a latency value indicating failure, e.g., -1
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': WAN_MON_LATENCY,
                    'Dimensions': [{'Name': 'URL', 'Value': WEBSITE}],
                    'Value': -1,
                    'Unit': 'Milliseconds'
                },
            ],
            Namespace=WAN_MANESPACE
        )
        return {
            'statusCode': 500,
            'body': f'Failed to monitor website: {e}'
        }

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': f'An unexpected error occurred: {e}'
        }
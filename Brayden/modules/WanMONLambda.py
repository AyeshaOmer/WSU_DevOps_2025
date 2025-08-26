import boto3
import requests
import time
import logging

# User created files
import constants
import push_to_cloudwatch

# Configure logging for better error visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    try:
        # Check ping timing and latency
        start_time = time.time()
        # 10-second timeout for the request to prevent long-running calls
        response = requests.get(constants.WEBSITE, timeout=10)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Determine availability: 1 for success (status code 200), 0 for failure
        availability_status = 1 if response.status_code == 200 else 0

        # Use the reusable push_metric function to send data to CloudWatch
        # Push the availability metric
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_MANESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=availability_status,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # Push the latency metric
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_MANESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=latency_ms,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        logger.info(f"Successfully published metrics for {constants.WEBSITE}.")

        return {
            'statusCode': 200,
            'body': 'Metrics published to CloudWatch'
        }

    except requests.exceptions.RequestException as e:
        # If the request fails, push a failure metric for both availability and latency
        logger.error(f"Failed to reach {constants.WEBSITE}: {e}")

        # Push an availability status of 0
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_MANESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=0,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # Push a latency value of -1 to indicate a failure
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_MANESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=-1,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        return {
            'statusCode': 500,
            'body': f'Failed to monitor website: {e}'
        }

    except Exception as e:
        # Catch-all for any other unexpected errors
        logger.error(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': f'An unexpected error occurred: {e}'
        }

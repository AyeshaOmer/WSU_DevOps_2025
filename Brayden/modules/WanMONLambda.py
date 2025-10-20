import boto3
import urllib3
import time
import logging

# User created files
import constants
import push_to_cloudwatch

# Configure logging for better error visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


http = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=10.0, read=10.0),
    retries=urllib3.Retry(total=False) # Disable retries to match original behavior
)

def lambda_handler(event, context):
    try:
        # Check ping timing and latency
        start_time = time.time()
        
        # 10-second timeout for the request to prevent long-running calls
        response = http.request('GET', constants.WEBSITE)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Determine availability: 1 for success (status code 200), 0 for failure
        availability_status = 1 if response.status == 200 else 0

        # Use the reusable push_metric function to send data to CloudWatch
        # Push the availability metric
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=availability_status,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # Push the latency metric
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=latency_ms,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )
        
        # Check and push SSL certificate expiry metric
        push_to_cloudwatch.check_ssl_expiration_and_push_metric(
            website=constants.WEBSITE,
            namespace=constants.WAN_NAMESPACE
        )

        logger.info(f"Successfully published metrics for {constants.WEBSITE}.")

        return {
            'statusCode': 200,
            'body': 'Metrics published to CloudWatch'
        }

    except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.TimeoutError) as e:
        # If the request fails due to a network or timeout issue, push a failure metric for both availability and latency
        logger.error(f"Failed to reach {constants.WEBSITE}: {e}")

        # Push an availability status of 0
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=0,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # Push a latency value of -1 to indicate a failure
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=-1,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )
        
        # submit a SSL failure.
        logger.warning(f"Skipping SSL certificate check due to request failure for {constants.WEBSITE}.")

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

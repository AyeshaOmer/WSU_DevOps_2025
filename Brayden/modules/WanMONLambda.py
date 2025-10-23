# lambda_function.py
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
    # Set a combined 10-second timeout for connection and read
    timeout=urllib3.Timeout(connect=10.0, read=10.0), 
    # Disable retries as we want a fast failure/success signal
    retries=urllib3.Retry(total=False) 
)

def lambda_handler(event, context):
    """
    The main handler for the Lambda function. Pings a target URL, calculates 
    latency and availability, and pushes custom metrics to CloudWatch.
    """
    try:
        # --- 1. Perform HTTP Request and Measure Latency ---
        start_time = time.time()
        
        # Use the URL defined in constants
        response = http.request('GET', constants.WEBSITE)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Determine availability: 1 for success (status code 200), 0 for other status codes
        availability_status = 1 if response.status == 200 else 0
        
        # Log the outcome
        logger.info(f"Ping successful. Status: {response.status}, Latency: {latency_ms:.2f}ms")

        # --- 2. Push Availability Metric ---
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=availability_status,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # --- 3. Push Latency Metric ---
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=latency_ms,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )
        
        # --- 4. Check and push SSL certificate expiry metric ---
        push_to_cloudwatch.check_ssl_expiration_and_push_metric(
            website=constants.WEBSITE,
            namespace=constants.WAN_NAMESPACE
        )

        logger.info(f"Successfully published all metrics for {constants.WEBSITE}.")

        return {
            'statusCode': 200,
            'body': 'Metrics published to CloudWatch'
        }

    except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.TimeoutError) as e:
        # --- Handle Network/Timeout Failures ---
        logger.error(f"Failed to reach {constants.WEBSITE} (Network/Timeout): {e}")

        # Push a failure metric for availability (0)
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_AVAILABILITY,
            value=0,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )

        # Push a latency value of -1 to explicitly indicate a failure/timeout in the graph
        push_to_cloudwatch.push_metric(
            namespace=constants.WAN_NAMESPACE,
            metric_name=constants.WAN_MON_LATENCY,
            value=-1,
            unit='Milliseconds',
            dimensions=[{'Name': 'URL', 'Value': constants.WEBSITE}]
        )
        
        logger.warning(f"Skipping SSL certificate check due to request failure for {constants.WEBSITE}.")

        return {
            'statusCode': 500,
            'body': f'Failed to monitor website due to network error: {e}'
        }

    except Exception as e:
        # --- Catch-all for any other unexpected errors ---
        logger.error(f"An unexpected error occurred during monitoring: {e}")
        return {
            'statusCode': 500,
            'body': f'An unexpected error occurred: {e}'
        }

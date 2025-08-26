import boto3
import logging
from datetime import datetime, timedelta
import ssl
import socket

#User created files
import constants

# Pyhton error handleing 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conects to clodwatch
try:
    cloudwatch_client = boto3.client('cloudwatch')
except Exception as e:
    logger.error(f"Failed to create CloudWatch client: {e}")
    cloudwatch_client = None

def push_metric(
    namespace: str,
    metric_name: str,
    value: float,
    unit: str,
    dimensions: list = None
) -> bool:
    # If the client failed to initialize, we cannot proceed.
    if cloudwatch_client is None:
        logger.error("CloudWatch client is not available. Cannot push metric.")
        return False

    # Set dimensions to an empty list if not provided, to prevent errors
    if dimensions is None:
        dimensions = []

    # Construct the metric data payload.
    # The Timestamp is automatically handled by CloudWatch if not provided,
    # but explicitly including it can be useful for debugging.
    metric_data = [
        {
            'MetricName': metric_name,
            'Dimensions': dimensions,
            'Timestamp': datetime.utcnow(),
            'Value': value,
            'Unit': unit,
        },
    ]

    try:
        logger.info(f"Attempting to push metric: {metric_name} with value: {value} to namespace: {namespace}")
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )
        logger.info("Metric successfully pushed.")
        return True
    except Exception as e:
        logger.error(f"Failed to push metric to CloudWatch: {e}")
        return False

def check_ssl_expiration_and_push_metric(website: str, namespace: str) -> bool:
    # Define thresholds for the metric value
    # 0 = OK (more than 15 days)
    # 15 = WARNING (5-15 days remaining)
    # 5 = CRITICAL (less than 5 days remaining)
    CRITICAL_THRESHOLD = 5
    WARNING_THRESHOLD = 15
    SSL_EXPIRY_METRIC = "SSLCertificateExpiry"

    # If the client failed to initialize, we cannot proceed.
    if cloudwatch_client is None:
        logger.error("CloudWatch client is not available. Cannot check SSL expiry.")
        return False

    # Strip the protocol from the URL to get the hostname
    hostname = website.replace('https://', '').replace('http://', '').split('/')[0]

    try:
        # Connect to the website and get the SSL certificate
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        
        # Get the expiration date from the certificate
        expiry_date_str = cert['notAfter']
        expiry_date = datetime.strptime(expiry_date_str, '%b %d %H:%M:%S %Y %Z')

        # Calculate remaining days until expiration
        remaining_days = (expiry_date - datetime.utcnow()).days

        # Determine the metric value based on remaining days
        metric_value = 0
        if remaining_days < CRITICAL_THRESHOLD:
            metric_value = CRITICAL_THRESHOLD
        elif remaining_days < WARNING_THRESHOLD:
            metric_value = WARNING_THRESHOLD

        # Push the metric to CloudWatch
        logger.info(f"SSL certificate for {hostname} expires in {remaining_days} days. Pushing metric with value: {metric_value}")
        return push_metric(
            namespace=namespace,
            metric_name=SSL_EXPIRY_METRIC,
            value=metric_value,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': hostname}]
        )

    except Exception as e:
        logger.error(f"Failed to check SSL certificate for {hostname}: {e}")
        # Push a critical metric value to indicate a failure
        return push_metric(
            namespace=namespace,
            metric_name=SSL_EXPIRY_METRIC,
            value=CRITICAL_THRESHOLD,
            unit='None',
            dimensions=[{'Name': 'URL', 'Value': hostname}]
        )

# You can also define a function to push multiple metrics at once for efficiency.
def push_multiple_metrics(namespace: str, metric_data: list) -> bool:
    if cloudwatch_client is None:
        logger.error("CloudWatch client is not available. Cannot push metrics.")
        return False

    try:
        logger.info(f"Attempting to push {len(metric_data)} metrics to namespace: {namespace}")
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )
        logger.info("Metrics successfully pushed.")
        return True
    except Exception as e:
        logger.error(f"Failed to push metrics to CloudWatch: {e}")
        return False

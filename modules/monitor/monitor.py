import boto3
import requests
import time
import logging
import os
import json
from typing import Dict, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

class WebsiteMonitor:
    def __init__(self):
        self.websites_table = dynamodb.Table(os.environ['WEBSITES_TABLE'])
        self.cloudwatch = cloudwatch

    def get_websites(self) -> List[Dict]:
        """Get all websites to monitor from Websites_Table"""
        try:
            response = self.websites_table.scan()
            websites = response.get('Items', [])

            # Filter for enabled websites
            enabled_websites = []
            for website in websites:
                if website.get('enabled', True):  # Default to enabled
                    enabled_websites.append(website)

            logger.info(f"Retrieved {len(enabled_websites)} websites to monitor")
            return enabled_websites
        except Exception as e:
            logger.error(f"Failed to retrieve websites: {str(e)}")
            return []

    def check_website_availability(self, website: Dict) -> Optional[Dict]:
        """Check website availability and latency"""
        url = website['url']
        website_id = website['id']
        website_name = website.get('name', website_id)

        try:
            logger.info(f"Checking availability of {url}")

            # Make HTTP request
            start_time = time.time()
            response = requests.get(url, timeout=30, allow_redirects=True)
            response_time = time.time() - start_time

            # Calculate metrics
            availability = 1 if 200 <= response.status_code < 400 else 0
            latency_ms = round(response_time * 1000, 2)

            # Send metrics to CloudWatch
            self._send_metrics_to_cloudwatch(website_id, website_name, availability, latency_ms, response.status_code)

            # Create alarms for this website
            self._create_website_alarms(website)

            result = {
                'website_id': website_id,
                'website_name': website_name,
                'url': url,
                'status_code': response.status_code,
                'response_time': latency_ms,
                'availability': availability,
                'timestamp': str(int(time.time()))
            }

            logger.info(f"Successfully checked {url}: {response.status_code} in {latency_ms}ms")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check {url}: {str(e)}")

            # Send failure metrics to CloudWatch
            self._send_metrics_to_cloudwatch(website_id, website_name, 0, 0, 0)

            return {
                'website_id': website_id,
                'website_name': website_name,
                'url': url,
                'status_code': 0,
                'response_time': 0,
                'availability': 0,
                'error': str(e),
                'timestamp': str(int(time.time()))
            }

    def _send_metrics_to_cloudwatch(self, website_id: str, website_name: str, availability: int, latency: float, status_code: int):
        """Send availability metrics to CloudWatch"""
        try:
            metrics_data = [
                {
                    'MetricName': 'Availability',
                    'Dimensions': [
                        {'Name': 'WebsiteId', 'Value': website_id},
                        {'Name': 'WebsiteName', 'Value': website_name}
                    ],
                    'Value': availability,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Latency',
                    'Dimensions': [
                        {'Name': 'WebsiteId', 'Value': website_id},
                        {'Name': 'WebsiteName', 'Value': website_name}
                    ],
                    'Value': latency,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'StatusCode',
                    'Dimensions': [
                        {'Name': 'WebsiteId', 'Value': website_id},
                        {'Name': 'WebsiteName', 'Value': website_name}
                    ],
                    'Value': status_code,
                    'Unit': 'Count'
                }
            ]

            self.cloudwatch.put_metric_data(
                Namespace='WebsiteMonitoring',
                MetricData=metrics_data
            )

            logger.info(f"Sent metrics to CloudWatch for {website_name}")

        except Exception as e:
            logger.error(f"Failed to send metrics to CloudWatch: {str(e)}")

    def _create_website_alarms(self, website: Dict):
        """Create CloudWatch alarms for a specific website"""
        website_id = website['id']
        website_name = website.get('name', website_id)

        try:
            # Check if alarms already exist for this website
            existing_alarms = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f"{website_name}-"
            )

            if existing_alarms['MetricAlarms']:
                logger.info(f"Alarms already exist for {website_name}")
                return

            # Create availability alarm: triggers when availability = 0
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"{website_name}-Availability",
                AlarmDescription=f"Alert when {website_name} is not available (availability = 0)",
                ActionsEnabled=True,
                AlarmActions=[os.environ.get('ALARM_SNS_TOPIC_ARN', '')],
                MetricName='Availability',
                Namespace='WebsiteMonitoring',
                Statistic='Minimum',
                Dimensions=[
                    {'Name': 'WebsiteId', 'Value': website_id},
                    {'Name': 'WebsiteName', 'Value': website_name}
                ],
                Period=300,  # 5 minutes
                EvaluationPeriods=1,
                DatapointsToAlarm=1,
                Threshold=1,
                ComparisonOperator='LessThanThreshold'
            )

            # Create latency alarm: triggers when latency > 400ms
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"{website_name}-Latency",
                AlarmDescription=f"Alert when {website_name} latency exceeds 400ms",
                ActionsEnabled=True,
                AlarmActions=[os.environ.get('ALARM_SNS_TOPIC_ARN', '')],
                MetricName='Latency',
                Namespace='WebsiteMonitoring',
                Statistic='Average',
                Dimensions=[
                    {'Name': 'WebsiteId', 'Value': website_id},
                    {'Name': 'WebsiteName', 'Value': website_name}
                ],
                Period=300,  # 5 minutes
                EvaluationPeriods=1,
                DatapointsToAlarm=1,
                Threshold=400,
                ComparisonOperator='GreaterThanThreshold'
            )

            logger.info(f"Created CloudWatch alarms for {website_name}")

        except Exception as e:
            logger.error(f"Failed to create alarms for {website_name}: {str(e)}")


def lambda_handler(event, context):
    """Main Lambda handler for website monitoring"""
    logger.info("Starting website monitoring execution")

    monitor = WebsiteMonitor()
    websites = monitor.get_websites()

    if not websites:
        logger.warning("No websites found to monitor")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No websites to monitor'})
        }

    results = []

    for website in websites:
        # Check website availability and send metrics
        result = monitor.check_website_availability(website)
        if result:
            results.append(result)

    logger.info(f"Successfully monitored {len(results)} websites")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully monitored {len(results)} websites',
            'results_count': len(results),
            'timestamp': str(int(time.time()))
        })
    }


# for testing
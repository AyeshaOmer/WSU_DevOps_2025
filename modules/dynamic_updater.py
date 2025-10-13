import boto3
import os
import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Handle DynamoDB Stream events to update CloudWatch dashboard and alarms
    """
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    try:
        # Process DynamoDB Stream records
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'REMOVE']:
                # Update dashboard and alarms based on URL changes
                update_dashboard_and_alarms()
                
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed URL changes')
        }
        
    except Exception as e:
        print(f"Error processing stream record: {str(e)}")
        raise e

def update_dashboard_and_alarms():
    # Get current URLs from DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['URL_TABLE_NAME'])
    
    response = table.query(
        KeyConditionExpression='#type = :type',
        ExpressionAttributeNames={'#type': 'type'},
        ExpressionAttributeValues={':type': 'url'}
    )
    
    urls = [item['id'] for item in response['Items']]
    
    # Update dashboard with current URLs
    update_dashboard(urls)
    
    # Update alarms for each URL
    update_alarms(urls)

def update_dashboard(urls):
    cloudwatch = boto3.client('cloudwatch')
    
    widgets = []
    for url in urls:
        widget = {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['WebHelperDashboard', 'Availability', 'URL', url],
                    ['WebHelperDashboard', 'Latency', 'URL', url],
                    ['WebHelperDashboard', 'ResponseSize', 'URL', url]
                ],
                'period': 60,
                'stat': 'Average',
                'region': os.environ.get('AWS_REGION', 'ap-southeast-2'),
                'title': f'Metrics for {url}'
            }
        }
        widgets.append(widget)
    
    dashboard_body = {
        'widgets': widgets
    }
    
    cloudwatch.put_dashboard(
        DashboardName=os.environ['DASHBOARD_NAME'],
        DashboardBody=json.dumps(dashboard_body)
    )

def update_alarms(urls):
    cloudwatch = boto3.client('cloudwatch')
    
    # Create or update alarms for each URL
    for url in urls:
        alarm_name = f"AvailabilityAlarm-{url}"
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=1,
            MetricName='Availability',
            Namespace='WebHelperDashboard',
            Period=60,
            Statistic='Average',
            Threshold=1.0,
            ActionsEnabled=True,
            AlarmDescription=f'Availability alarm for {url}',
            Dimensions=[
                {'Name': 'URL', 'Value': url}
            ]
        )
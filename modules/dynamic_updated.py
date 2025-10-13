
import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

url_table = dynamodb.Table(os.environ['URL_TABLE_NAME'])
dashboard_name = os.environ['DASHBOARD_NAME']
email_sub = os.environ['EMAIL_SUB']

def lambda_handler(event, context):
    # Step 1: Query current URLs (only type='url')
    response = url_table.query(
        KeyConditionExpression=Key('type').eq('url'),
        ExpressionAttributeNames={'#type': 'type'}  # If 'type' is reserved
    )
    current_urls = [item['id'] for item in response['Items']]

    # Step 2: Delete old alarms (prefix-based)
    old_alarm_prefixes = set()  # Collect from current + assume some buffer
    for url in current_urls:  # But to clean orphans, list all with prefix
        for metric_type in ['Availability', 'Latency', 'Size']:
            old_alarm_prefixes.add(f"{url} {metric_type} Alarm")
    # List and delete
    alarms_response = cloudwatch.describe_alarms(AlarmNamePrefix='')  # Or filter by namespace
    for alarm in alarms_response['MetricAlarms']:
        if any(alarm['AlarmName'].startswith(prefix) for prefix in old_alarm_prefixes) or alarm['AlarmName'].startswith(tuple(f"{u} " for u in current_urls)):  # Broader cleanup
            cloudwatch.delete_alarms(AlarmNames=[alarm['AlarmName']])

    # Step 3: Delete old SNS topics (list and match prefix)
    topics_response = sns.list_topics()
    for topic in topics_response['Topics']:
        topic_arn = topic['TopicArn']
        topic_name = topic_arn.split(':')[-1]
        if any(topic_name.startswith(f"{url}-alarm-topic") for url in current_urls + ['old-urls']):  # Cleanup logic
            # Unsubscribe all
            subs_response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            for sub in subs_response['Subscriptions']:
                if sub['Endpoint'] == email_sub:
                    sns.unsubscribe(SubscriptionArn=sub['SubscriptionArn'])
            sns.delete_topic(TopicArn=topic_arn)

    # Step 4: Create new alarms and SNS topics for each URL
    alarm_arns = {}  # For dashboard reference
    for url in current_urls:
        topic_arn = _create_sns_topic(url)
        _create_subscriptions(topic_arn)

        # Create alarms (match your thresholds)
        avail_alarm = _create_alarm(url, 'Availability', threshold=0, op='LessThanOrEqualToThreshold', topic_arn=topic_arn)
        latency_alarm = _create_alarm(url, 'Latency', threshold=1, op='GreaterThanThreshold', topic_arn=topic_arn)
        size_alarm = _create_alarm(url, 'Size', threshold=1, op='LessThanThreshold', topic_arn=topic_arn)

        alarm_arns[url] = {
            'Availability': avail_alarm,
            'Latency': latency_alarm,
            'Size': size_alarm
        }

    # Step 5: Build and put dashboard JSON
    dashboard_body = _build_dashboard_json(current_urls, alarm_arns)
    cloudwatch.put_dashboard(DashboardName=dashboard_name, DashboardBody=json.dumps(dashboard_body))

    return {'statusCode': 200, 'body': json.dumps({'updated_urls': current_urls})}

def _create_sns_topic(url):
    response = sns.create_topic(Name=f"{url}-alarm-topic", DisplayName=f"Web Health Alarms for {url}")
    return response['TopicArn']

def _create_subscriptions(topic_arn):
    # Email sub
    sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email_sub
    )
    # Alarm logger sub
    # Assume alarm_logger ARN is passed or hardcoded; or use single shared logger
    # sns.subscribe(TopicArn=topic_arn, Protocol='lambda', Endpoint=alarm_logger_arn)
    # For simplicity, use shared alarm_logger if ARN is env var

def _create_alarm(url, metric_name, threshold, op, topic_arn):
    alarm_name = f"{url} {metric_name} Alarm"
    alarm_arn = cloudwatch.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription=f"Alarm for {url} {metric_name}",
        Namespace="WebHelperDashboard",
        MetricName=metric_name,
        Dimensions=[{'Name': 'URL', 'Value': url}],
        Statistic='Average',
        Period=60,
        EvaluationPeriods=1,
        Threshold=threshold,
        ComparisonOperator=op,
        AlarmActions=[topic_arn],
    )['AlarmArn']
    return alarm_arn

def _build_dashboard_json(urls, alarm_arns):
    widgets = []
    for url in urls:
        # Alarm widgets (as in your original)
        for metric in ['Availability', 'Latency', 'Size']:
            widgets.append({
                "type": "alarm",
                "properties": {
                    "title": f"{url} {metric}",
                    "alarms": [alarm_arns[url][metric]]
                }
            })
        # Optional: Add graph widgets for metrics
        widgets.append({
            "type": "graph",
            "properties": {
                "title": f"{url} Metrics",
                "metrics": [
                    [f"WebHelperDashboard", "Availability", "URL", url],
                    [".", "Latency", ".", url],
                    [".", "ResponseSize", ".", url]
                ],
                "view": "timeSeries",
                "stacked": False
            }
        })
    # Full dashboard JSON structure (rows of 3 widgets, etc.)
    return {
        "widgets": widgets,
        "rows": 1 + (len(widgets) // 3),  # Auto-layout
        "columns": 24,
        "version": "2024-01-01"  # Current as of 2025
    }
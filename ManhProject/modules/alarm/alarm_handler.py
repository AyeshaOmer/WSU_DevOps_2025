import os
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table_name = os.environ.get('ALARM_HISTORY_TABLE')
    table = dynamodb.Table(table_name)

    # SNS can batch records; handle all
    for record in event.get('Records', []):
        try:
            sns = record.get('Sns', {})
            message = sns.get('Message')
            subject = sns.get('Subject')
            timestamp = sns.get('Timestamp')

            # Parse alarm details from message
            alarm_data = json.loads(message) if message else {}

            # Extract metric information for tagging
            metric_name = alarm_data.get('AlarmName', 'Unknown')
            metric_type = 'latency' if 'Latency' in metric_name else 'availability' if 'Availability' in metric_name else 'unknown'

            # Parse website name from alarm name (format: "AvailabilityAlarm-Google" or "LatencyAlarm-Google")
            website_name = "Unknown"
            if '-' in metric_name:
                parts = metric_name.split('-')
                if len(parts) > 1:
                    website_name = parts[-1]

            item = {
                'timestamp': timestamp or datetime.utcnow().isoformat(),  # Partition key
                'website': website_name,  # Sort key
                'alarm_id': str(uuid.uuid4()),
                'subject': subject or 'CloudWatch Alarm',
                'message': message or json.dumps(sns),
                'metric_type': metric_type,  # Tag for filtering
                'alarm_name': alarm_data.get('AlarmName', ''),
                'alarm_description': alarm_data.get('AlarmDescription', ''),
                'state': alarm_data.get('NewStateValue', ''),
                'reason': alarm_data.get('NewStateReason', ''),
                'region': alarm_data.get('Region', ''),
                'processed_at': datetime.utcnow().isoformat()
            }

            table.put_item(Item=item)
            print(f"Logged alarm: {metric_name} for {website_name}")

        except Exception as e:
            print(f'Failed to write alarm to DynamoDB: {str(e)}')
            print(f'Event record: {json.dumps(record)}')

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Alarm processing complete'})
    }
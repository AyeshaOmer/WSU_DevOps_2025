import os
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table_name = os.environ.get('ALARM_TABLE_NAME')
    table = dynamodb.Table(table_name)

    # SNS can batch records; handle all
    for record in event.get('Records', []):
        try:
            sns = record.get('Sns', {})
            message = sns.get('Message')
            subject = sns.get('Subject')
            timestamp = sns.get('Timestamp')

            item = {
                'AlarmId': str(uuid.uuid4()),
                'Timestamp': timestamp or datetime.utcnow().isoformat(),
                'Subject': subject or 'CloudWatch Alarm',
                'Message': message or json.dumps(sns)
            }

            table.put_item(Item=item)
        except Exception as e:
            print('Failed to write alarm to DynamoDB:', e)
    return {
        'statusCode': 200,
        'body': 'ok'
    }

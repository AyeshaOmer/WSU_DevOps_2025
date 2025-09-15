import json
import os
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """
    Lambda function to log CloudWatch Alarms to DynamoDB
    """
    try:
        # Parse the SNS message
        message = json.loads(event['Records'][0]['Sns']['Message'])
        
        # Create a unique ID for the alarm entry
        alarm_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare the alarm data
        alarm_data = {
            'id': alarm_id,
            'timestamp': timestamp,
            'alarmName': message['AlarmName'],
            'alarmDescription': message.get('AlarmDescription', ''),
            'newStateValue': message['NewStateValue'],
            'oldStateValue': message['OldStateValue'],
            'reason': message['NewStateReason'],
            'region': message['Region'],
            'threshold': message['Trigger']['Threshold'],
            'metricName': message['Trigger']['MetricName']
        }
        
        # Store in DynamoDB
        table.put_item(Item=alarm_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully logged alarm {alarm_id}')
        }
        
    except Exception as e:
        print(f'Error logging alarm: {str(e)}')
        raise e

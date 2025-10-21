import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def db_lambda_handler(event, context):
    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])

        item = {
            'pk': f"{sns_message.get('AlarmName')}#{datetime.utcnow().isoformat()}", # primary key
            'AlarmName': sns_message.get('AlarmName'), # name of the CloudWatch alarm that triggered the SNS notification.
            'AlarmDescription': sns_message.get('AlarmDescription'),
            'NewStateReason': sns_message.get('NewStateReason'), # why the alarm state was changed
            'MetricName': sns_message.get('Trigger', {}).get('MetricName'), # specific metric triggered
            'Dimensions': json.dumps(sns_message.get('Trigger', {}).get('Dimensions', [])), # URLs
            'Timestamp': datetime.utcnow().isoformat()
        }
        table.put_item(Item=item)
        print(f"Inserted item into DynamoDB: {item}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Alarm metrics written to DynamoDB')
    }
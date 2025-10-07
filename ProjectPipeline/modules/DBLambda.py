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
            'pk': f"{sns_message.get('AlarmName')}#{datetime.utcnow().isoformat()}",
            'AlarmName': sns_message.get('AlarmName'),
            'AlarmDescription': sns_message.get('AlarmDescription'),
            'NewStateReason': sns_message.get('NewStateReason'),
            'MetricName': sns_message.get('Trigger', {}).get('MetricName'),
            'Dimensions': json.dumps(sns_message.get('Trigger', {}).get('Dimensions', [])),
            'Timestamp': datetime.utcnow().isoformat()
        }
        table.put_item(Item=item)
        print(f"Inserted item into DynamoDB: {item}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Alarm metrics written to DynamoDB')
    }


    '''
    To do list:
    - Create a new SNS topic using information from alarms
    SNS triggers email subscription and lambda subscription (both found in SNS subscription construct)
    Write alarm information into Dynamo DB using lambda function (DBLambda.py)
    
    Whats in stack:
        alarms, SNS topic
    '''
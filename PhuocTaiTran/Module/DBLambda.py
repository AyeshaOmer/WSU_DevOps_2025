import boto3 
import os
import json
from datetime import datetime

# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
# program flow: CloudWatch Alarm -> SNS Topic -> Lambda function (this code) -> DynamoDB
def lambda_handler(event, context):
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE', 'PhuocTaiTranLambdaStack-Table')
        table = dynamodb.Table(table_name)
        
        print(f"Processing alarm event: {json.dumps(event)}")
        
        # Parse CloudWatch Alarm event
        if 'Records' in event and event['Records']:
            # SNS message from CloudWatch Alarm
            sns_message = json.loads(event['Records'][0]['Sns']['Message'])
            alarm_name = sns_message.get('AlarmName', 'unknown')
            new_state = sns_message.get('NewStateValue', 'unknown')
            reason = sns_message.get('NewStateReason', 'No reason provided')
            
            # Extract URL from alarm name (format: "AvailabilityAlarm-https://www.example.com")
            website = alarm_name.split('-', 1)[1] if '-' in alarm_name else 'unknown'
            
            print(f"Alarm: {alarm_name}, State: {new_state}, Website: {website}")
            
            # Only log when site goes down (ALARM state)
            if new_state == 'ALARM':
                # Insert alarm info into DynamoDB
                item = {
                    'pk': f"{website}#{datetime.utcnow().isoformat()}",  # Unique partition key
                    'website': website,
                    'alarm_name': alarm_name,
                    'state': new_state,
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat(),
                    'ttl': int((datetime.utcnow().timestamp()) + 30*24*3600)  # 30 days TTL
                }
                
                table.put_item(Item=item)
                print(f"Successfully recorded alarm for {website}")
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Successfully recorded alarm for {website}')
                }
            else:
                print(f"Ignoring non-ALARM state: {new_state}")
                return {
                    'statusCode': 200,
                    'body': json.dumps('Ignored non-alarm state')
                }
        else:
            # Direct invocation for testing
            website = event.get('website', 'test-website')
            downtime_minutes = event.get('downtime_minutes', 0)
            
            item = {
                'pk': f"{website}#{datetime.utcnow().isoformat()}",
                'website': website,
                'downtime_minutes': downtime_minutes,
                'timestamp': datetime.utcnow().isoformat(),
                'test_event': True
            }
            
            table.put_item(Item=item)
            print(f"Test event recorded for {website}")
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'Test event recorded for {website}')
            }
            
    except Exception as e:
        print(f"Error processing alarm: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

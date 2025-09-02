import boto3
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'Alarm_Website_Down')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Example event from CloudWatch Alarm
    website = event.get('website', 'unknown')
    downtime_minutes = event.get('downtime_minutes', 0)
    timestamp = event.get('timestamp', context.aws_request_id)

    print(f"Website {website} is down for {downtime_minutes} minutes.")

    # Insert alarm info into DynamoDB
    table.put_item(
        Item={
            'website': website,
            'downtime_minutes': downtime_minutes,
            'timestamp': timestamp
        }
    )

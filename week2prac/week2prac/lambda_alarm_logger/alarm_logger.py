import json
import os
import boto3
from datetime import datetime

TABLE_NAME = os.getenv("TABLE_NAME")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda function to log CloudWatch alarm notifications into DynamoDB
    """
    for record in event["Records"]:
        sns_message = json.loads(record["Sns"]["Message"])
        alarm_name = sns_message.get("AlarmName", "UnknownAlarm")
        new_state = sns_message.get("NewStateValue", "UNKNOWN")
        reason = sns_message.get("NewStateReason", "")

        timestamp = datetime.utcnow().isoformat()

        table.put_item(Item={
            "alarm_name": alarm_name,
            "timestamp": timestamp,
            "new_state": new_state,
            "reason": reason
        })

    return {"status": "success", "records_logged": len(event["Records"])}
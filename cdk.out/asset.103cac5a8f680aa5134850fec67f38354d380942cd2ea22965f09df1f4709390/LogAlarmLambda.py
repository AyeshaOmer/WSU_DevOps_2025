import boto3
import os
import json
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    for record in event.get("Records", []):
        sns = record.get("Sns", {})
        raw = sns.get("Message", "{}")

        try: 
            msg = json.loads(raw) if raw and raw.strip().startswith("{") else {}
        except json.JSONDecodeError:
            msg = {}

        alarm_name = msg.get("AlarmName") or "UnknownAlarm"
        new_state = msg.get("NewStateValue") or "UnknownState"
        reason = msg.get("NewStateReason") or raw or "No reason provided"
        timestamp = datetime.now(timezone.utc).isoformat()

        table.put_item(
            Item={
                "AlarmName": alarm_name,
                "Timestamp": timestamp,
                "NewState": new_state,
                "Reason": reason
            }
        )
    return {"status" : "ok"}
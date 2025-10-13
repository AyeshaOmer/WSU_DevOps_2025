import os
import json
import boto3
from datetime import datetime, timezone

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    # SNS → Lambda subscription receives an SNS event
    for record in event.get("Records", []):
        if record.get("EventSource") != "aws:sns":
            continue
        message = record["Sns"]["Message"]
        try:
            payload = json.loads(message)
        except Exception:
            payload = {"raw": message}

        alarm_name = (payload.get("AlarmName")
                      or payload.get("AlarmDescription")
                      or "UnknownAlarm")

        ts = datetime.now(timezone.utc).isoformat()

        item = {
            "alarm_name": str(alarm_name),
            "timestamp": ts,
            "payload": json.dumps(payload)[:350000],  # guard size
        }
        table.put_item(Item=item)

    return {"ok": True}

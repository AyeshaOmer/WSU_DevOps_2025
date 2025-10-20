import json
import os
import boto3
import re
from datetime import datetime

TABLE_NAME = os.getenv("TABLE_NAME", "DefaultTestTable")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

def parse_alarm_tags(alarm_description):
    """
    Parse tags from alarm description.
    Expected format: [METRIC_TYPE:value][SEVERITY:value][SITE:value] Description
    """
    tags = {}
    
    # Extract tags using regex
    tag_pattern = r'\[([A-Z_]+):([^\]]+)\]'
    matches = re.findall(tag_pattern, alarm_description)
    
    for key, value in matches:
        tags[key.lower()] = value
    
    return tags

def lambda_handler(event, context):
    """
    Lambda function to log CloudWatch alarm notifications into DynamoDB
    """
    for record in event["Records"]:
        sns_message = json.loads(record["Sns"]["Message"])
        alarm_name = sns_message.get("AlarmName", "UnknownAlarm")
        new_state = sns_message.get("NewStateValue", "UNKNOWN")
        reason = sns_message.get("NewStateReason", "")
        alarm_description = sns_message.get("AlarmDescription", "")

        timestamp = datetime.utcnow().isoformat()
        
        # Parse tags from alarm description
        tags = parse_alarm_tags(alarm_description)

        # Create DynamoDB item with tags
        item = {
            "alarm_name": alarm_name,
            "timestamp": timestamp,
            "new_state": new_state,
            "reason": reason,
            "alarm_description": alarm_description
        }
        
        # Add tags as separate attributes for easy filtering
        if tags:
            item.update({
                "metric_type": tags.get("metric_type", "unknown"),
                "severity": tags.get("severity", "unknown"),
                "site": tags.get("site", "unknown"),
                "tags": json.dumps(tags)  # Store all tags as JSON for flexibility
            })

        table.put_item(Item=item)

    return {"status": "success", "records_logged": len(event["Records"])}
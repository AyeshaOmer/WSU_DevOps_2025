import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TargetListTable")

def lambda_handler(event, context):
    http_method = event.get("httpMethod")
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    url = event.get("queryStringParameters", {}).get("url") if event.get("queryStringParameters") else None

    try:
        if http_method == "POST":  # Create
            table.put_item(Item=body)
            return _response(200, {"message": "Target added", "item": body})

        elif http_method == "GET":  # Read
            if url:
                response = table.get_item(Key={"url": url})
                return _response(200, response.get("Item", {}))
            else:
                scan_result = table.scan()
                return _response(200, scan_result.get("Items", []))

        elif http_method == "PUT":  # Update
            table.put_item(Item=body)
            return _response(200, {"message": "Target updated", "item": body})

        elif http_method == "DELETE":  # Delete
            if not url:
                return _response(400, {"error": "URL required for deletion"})
            table.delete_item(Key={"url": url})
            return _response(200, {"message": f"Deleted {url}"})

        else:
            return _response(405, {"error": "Method not allowed"})

    except Exception as e:
        return _response(500, {"error": str(e)})

def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}

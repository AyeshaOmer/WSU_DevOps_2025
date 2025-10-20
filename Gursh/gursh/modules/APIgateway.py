# gursh/modules/APIgateway.py
import json, os, boto3

# Fallback for local/unit tests; stack sets TABLE_NAME in AWS
if "TABLE_NAME" not in os.environ:
    os.environ["TABLE_NAME"] = "UrlsTableTest"

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])  # set in stack

def resp(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body),
    }

def lambda_handler(event, context):
    method = event.get("httpMethod")
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    qs   = event.get("queryStringParameters") or {}
    url  = (body.get("url") or qs.get("url") or "").strip()

    # CREATE
    if method == "POST":
        if not url:
            return resp(400, {"error": "Missing 'url'"})
        item = {"url": url, **{k: v for k, v in body.items() if k != "url"}}
        table.put_item(Item=item)
        return resp(200, {"message": "added", "item": item})

    # READ.
    if method == "GET":
        if url:
            res = table.get_item(Key={"url": url})
            return resp(200, res.get("Item") or {})
        
        res = table.scan(
            ProjectionExpression="#u",
            ExpressionAttributeNames={"#u": "url"}
        )
        items = [i["url"] for i in res.get("Items", []) if "url" in i]
        return resp(200, items)

    # UPDATE
    if method == "PUT":
        if not url:
            return resp(400, {"error": "Missing 'url'"})
        item = {"url": url, **{k: v for k, v in body.items() if k != "url"}}
        table.put_item(Item=item)
        return resp(200, {"message": "updated", "item": item})

    # DELETE
    if method == "DELETE":
        if not url:
            return resp(400, {"error": "Missing 'url'"})
        table.delete_item(Key={"url": url})
        return resp(200, {"message": f"deleted {url}"})


    if method == "OPTIONS":
        return resp(200, {"ok": True})

    return resp(405, {"error": "Method not allowed"})

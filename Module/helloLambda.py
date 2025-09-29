def handler(event, context):
    print("Hello from Lambda!")  # This logs to CloudWatch
    return {
        "statusCode": 200,
        "body": "Hello from Lambda!"
    }
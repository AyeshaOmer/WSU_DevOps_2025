import json
import boto3
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Sample Lambda function that demonstrates basic AWS operations
    """
    print(f"Event: {json.dumps(event)}")
    
    # Get environment variables
    bucket_name = os.environ.get('BUCKET_NAME', 'default-bucket')
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    try:
        # Get HTTP method
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        if http_method == 'GET':
            if path == '/':
                response_body = {
                    'message': 'Welcome to Project 2!',
                    'timestamp': datetime.now().isoformat(),
                    'bucket': bucket_name,
                    'path': path
                }
            elif path == '/items':
                # List objects in S3 bucket (example)
                try:
                    response = s3_client.list_objects_v2(Bucket=bucket_name)
                    objects = response.get('Contents', [])
                    response_body = {
                        'message': 'Items retrieved successfully',
                        'count': len(objects),
                        'items': [obj['Key'] for obj in objects[:10]]  # First 10 items
                    }
                except Exception as e:
                    response_body = {
                        'message': 'Error retrieving items',
                        'error': str(e)
                    }
            else:
                response_body = {
                    'message': 'Path not found',
                    'path': path
                }
        
        elif http_method == 'POST':
            # Handle POST request
            body = json.loads(event.get('body', '{}'))
            
            # Example: Create a file in S3
            file_name = f"item-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            file_content = json.dumps({
                'created_at': datetime.now().isoformat(),
                'data': body
            })
            
            try:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=file_name,
                    Body=file_content,
                    ContentType='application/json'
                )
                
                response_body = {
                    'message': 'Item created successfully',
                    'file_name': file_name,
                    'bucket': bucket_name
                }
            except Exception as e:
                response_body = {
                    'message': 'Error creating item',
                    'error': str(e)
                }
        
        else:
            response_body = {
                'message': f'HTTP method {http_method} not supported'
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
import boto3
import json
import os
from urllib.parse import unquote

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['URL_TABLE_NAME'])



def lambda_handler(event, context):
    http_method = event['httpMethod']
    
    if http_method == 'GET':
        # List all URLs
        response = table.query(
            KeyConditionExpression='#type = :type',
            ExpressionAttributeNames={'#type': 'type'},
            ExpressionAttributeValues={':type': 'url'}
        )
        return {
            'statusCode': 200,
            'body': json.dumps([item['id'] for item in response['Items']])
        }
        
    elif http_method == 'POST':
        # Add new URL
        url = json.loads(event['body'])['url']
        table.put_item(
            Item={
                'type': 'url',
                'id': url
            }
        )
        return {
            'statusCode': 201,
            'body': json.dumps({'message': f'URL {url} added successfully'})
        }
        
    elif http_method == 'DELETE':
        # Delete URL
        url = unquote(event['pathParameters']['url'])
        table.delete_item(
            Key={
                'type': 'url',
                'id': url
            }
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'URL {url} deleted successfully'})
        }
import json
import os
import boto3
import uuid
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

def get_config_table():
    """Get the config table with lazy initialization"""
    return dynamodb.Table(os.environ['CONFIG_TABLE'])

def create_response(status_code: int, body: Any) -> Dict:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def validate_website(website: Dict) -> Optional[str]:
    required_fields = ['name', 'url']
    for field in required_fields:
        if field not in website:
            return f"Missing required field: {field}"

    if not website['url'].startswith(('http://', 'https://')):
        return "URL must start with http:// or https://"

    return None

def create_website(event):
    try:
        website = json.loads(event['body'])

        # Validate input
        error = validate_website(website)
        if error:
            return create_response(400, {'error': error})

        # Add metadata and defaults
        website['id'] = str(uuid.uuid4())
        website['enabled'] = website.get('enabled', True)  # Default to enabled
        website['createdAt'] = datetime.utcnow().isoformat()
        website['updatedAt'] = website['createdAt']

        # Save to DynamoDB
        get_config_table().put_item(Item=website)

        return create_response(201, website)

    except Exception as e:
        logger.error(f"Error creating website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_website(event):
    try:
        website_id = event['pathParameters']['websiteId']

        response = get_config_table().get_item(Key={'id': website_id})

        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        return create_response(200, response['Item'])

    except Exception as e:
        logger.error(f"Error getting website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def list_websites(event):
    """List all websites"""
    try:
        response = get_config_table().scan()
        return create_response(200, response.get('Items', []))

    except Exception as e:
        logger.error(f"Error listing websites: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def update_website(event):
    """Update existing website entry"""
    try:
        website_id = event['pathParameters']['websiteId']
        website = json.loads(event['body'])

        # Validate input
        error = validate_website(website)
        if error:
            return create_response(400, {'error': error})

        # Check if website exists
        response = get_config_table().get_item(Key={'id': website_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        # Update metadata and preserve enabled field if not provided
        website['updatedAt'] = datetime.utcnow().isoformat()
        if 'enabled' not in website:
            website['enabled'] = response['Item'].get('enabled', True)

        # Update in DynamoDB
        get_config_table().put_item(Item={**response['Item'], **website})

        return create_response(200, {**response['Item'], **website})

    except Exception as e:
        logger.error(f"Error updating website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def delete_website(event):
    """Delete website by ID"""
    try:
        website_id = event['pathParameters']['websiteId']

        # Check if website exists
        response = get_config_table().get_item(Key={'id': website_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        # Delete from DynamoDB
        get_config_table().delete_item(Key={'id': website_id})

        return create_response(204, {})

    except Exception as e:
        logger.error(f"Error deleting website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")

    method = event['httpMethod']
    path = event.get('resource', event.get('path', ''))
    has_id = event.get('pathParameters', {}) and 'websiteId' in event['pathParameters']

    # Route request to appropriate handler
    if path.startswith('/websites'):
        if method == 'POST' and not has_id:
            return create_website(event)
        elif method == 'GET' and has_id:
            return get_website(event)
        elif method == 'GET' and not has_id:
            return list_websites(event)
        elif method == 'PUT' and has_id:
            return update_website(event)
        elif method == 'DELETE' and has_id:
            return delete_website(event)

    # Default fallback
    return create_response(400, {'error': 'Invalid request'})
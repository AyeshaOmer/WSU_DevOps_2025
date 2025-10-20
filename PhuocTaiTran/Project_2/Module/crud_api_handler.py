"""
Main Lambda handler for Project 2 Web Crawler CRUD API
This module serves as the entry point for all API Gateway requests.

https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
"""

import json
import logging
import os
from typing import Dict, Any
from dynamodb_manager import DynamoDBManager
from validators import (
    validate_create_target_request,
    validate_update_target_request,
    validate_query_parameters,
    validate_target_id,
    sanitize_target_data
)
from constants import HTTP_STATUS, CORS_HEADERS, ERROR_MESSAGES

# Configure logging
# why logging? Logging is essential for monitoring and debugging Lambda functions.
# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/README.html
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DynamoDB manager
# why here? Initializing outside the handler to reuse connections across invocations.
db_manager = DynamoDBManager(os.environ.get('DYNAMODB_TABLE_NAME'))

# Main Lambda handler
# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function.handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for API Gateway requests.
    
    Args:
        event (Dict[str, Any]): API Gateway event
        context: Lambda context object
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function.handler
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Handle CORS preflight requests
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Cors.html
        if http_method == 'OPTIONS':
            return create_response(HTTP_STATUS["OK"], {"message": "CORS preflight"})
        
        # Route to appropriate handler based on HTTP method and path
        # purpose: Handle collection-level operations
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html
        if path == '/targets':
            if http_method == 'GET':
                return handle_list_targets(query_parameters)
            elif http_method == 'POST':
                return handle_create_target(event.get('body', ''))
        # /targets/{target_id} resource with target_id parameter
        # purpse: Handle individual target operations
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html
        elif path.startswith('/targets/'):
            target_id = path_parameters.get('target_id')
            if not target_id:
                return create_error_response(
                    HTTP_STATUS["BAD_REQUEST"],
                    ERROR_MESSAGES["MISSING_REQUIRED_FIELD"] + ": target_id"
                )
            # Handle methods for specific target
            if http_method == 'GET':
                return handle_get_target(target_id)
            elif http_method == 'PUT':
                return handle_update_target(target_id, event.get('body', ''))
            elif http_method == 'DELETE':
                return handle_delete_target(target_id)
        
        # Route not found
        return create_error_response(
            HTTP_STATUS["NOT_FOUND"],
            f"Route not found: {http_method} {path}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# CRUD operation handlers
# Each handler validates input, interacts with DynamoDB, and returns a response
def handle_create_target(body: str) -> Dict[str, Any]:
    """
    Handle POST /targets - Create a new crawler target.
    
    Args:
        body (str): Request body JSON string
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Method.html
    """
    try:
        # Parse request body
        if not body:
            return create_error_response(
                HTTP_STATUS["BAD_REQUEST"],
                "Request body is required"
            )
        
        request_data = json.loads(body)
        
        # Validate request data
        is_valid, error_message = validate_create_target_request(request_data)
        if not is_valid:
            return create_error_response(HTTP_STATUS["BAD_REQUEST"], error_message)
        
        # Sanitize and prepare data
        target_data = sanitize_target_data(request_data)
        
        # Create target in database
        result = db_manager.create_target(target_data)
        
        return create_response(result["statusCode"], result["body"])
        
    except json.JSONDecodeError:
        return create_error_response(
            HTTP_STATUS["BAD_REQUEST"],
            "Invalid JSON in request body"
        )
    except Exception as e:
        logger.error(f"Error in handle_create_target: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# Handler for GET /targets/{target_id}
def handle_get_target(target_id: str) -> Dict[str, Any]:
    """
    Handle GET /targets/{target_id} - Retrieve a specific crawler target.
    
    Args:
        target_id (str): ID of the target to retrieve
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html
    """
    try:
        # Validate target ID
        if not validate_target_id(target_id):
            return create_error_response(
                HTTP_STATUS["BAD_REQUEST"],
                ERROR_MESSAGES["INVALID_TARGET_ID"]
            )
        
        # Get target from database
        result = db_manager.get_target(target_id)
        
        return create_response(result["statusCode"], result["body"])
        
    except Exception as e:
        logger.error(f"Error in handle_get_target: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# Handler for PUT /targets/{target_id}
def handle_update_target(target_id: str, body: str) -> Dict[str, Any]:
    """
    Handle PUT /targets/{target_id} - Update a crawler target.
    
    Args:
        target_id (str): ID of the target to update
        body (str): Request body JSON string
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Method.html
    """
    try:
        # Validate target ID
        if not validate_target_id(target_id):
            return create_error_response(
                HTTP_STATUS["BAD_REQUEST"],
                ERROR_MESSAGES["INVALID_TARGET_ID"]
            )
        
        # Parse request body
        if not body:
            return create_error_response(
                HTTP_STATUS["BAD_REQUEST"],
                "Request body is required"
            )
        
        request_data = json.loads(body)
        
        # Validate request data
        is_valid, error_message = validate_update_target_request(request_data)
        if not is_valid:
            return create_error_response(HTTP_STATUS["BAD_REQUEST"], error_message)
        
        # Sanitize and prepare data
        update_data = sanitize_target_data(request_data)
        
        # Remove target_id from update data if present (can't update primary key)
        update_data.pop('target_id', None)
        
        # Update target in database
        result = db_manager.update_target(target_id, update_data)
        
        return create_response(result["statusCode"], result["body"])
        
    except json.JSONDecodeError:
        return create_error_response(
            HTTP_STATUS["BAD_REQUEST"],
            "Invalid JSON in request body"
        )
    except Exception as e:
        logger.error(f"Error in handle_update_target: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# Handler for DELETE /targets/{target_id}
def handle_delete_target(target_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /targets/{target_id} - Delete a crawler target.
    
    Args:
        target_id (str): ID of the target to delete
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Method.html
    """
    try:
        # Validate target ID
        if not validate_target_id(target_id):
            return create_error_response(
                HTTP_STATUS["BAD_REQUEST"],
                ERROR_MESSAGES["INVALID_TARGET_ID"]
            )
        
        # Delete target from database
        result = db_manager.delete_target(target_id)
        
        return create_response(result["statusCode"], result["body"])
        
    except Exception as e:
        logger.error(f"Error in handle_delete_target: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# Handler for GET /targets with optional query parameters
def handle_list_targets(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /targets - List crawler targets with optional filtering.
    
    Args:
        query_parameters (Dict[str, str]): Query string parameters
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
    """
    try:
        # Validate query parameters
        is_valid, error_message = validate_query_parameters(query_parameters)
        if not is_valid:
            return create_error_response(HTTP_STATUS["BAD_REQUEST"], error_message)
        
        # Extract parameters
        status_filter = query_parameters.get('status')
        limit = int(query_parameters.get('limit', 50))
        
        # List targets from database
        result = db_manager.list_targets(status_filter, limit)
        
        return create_response(result["statusCode"], result["body"])
        
    except Exception as e:
        logger.error(f"Error in handle_list_targets: {e}")
        return create_error_response(
            HTTP_STATUS["INTERNAL_ERROR"],
            "Internal server error"
        )

# Response creation helpers
def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.
    
    Args:
        status_code (int): HTTP status code
        body (Dict[str, Any]): Response body
        
    Returns:
        Dict[str, Any]: API Gateway response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
    """
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str)
    }

# Error response creation helper
def create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code (int): HTTP status code
        error_message (str): Error message
        
    Returns:
        Dict[str, Any]: API Gateway error response
        
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/ResponseType.html
    """
    return create_response(status_code, {"error": error_message})
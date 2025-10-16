"""
Unit tests for Web Crawler CRUD API Lambda handlers
Tests all CRUD operations, validation, and error handling.

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import boto3
from moto import mock_dynamodb
from crud_api_handler import (
    lambda_handler,
    handle_create_target,
    handle_get_target,
    handle_update_target,
    handle_delete_target,
    handle_list_targets,
    create_response,
    create_error_response
)
from constants import TABLE_NAME, HTTP_STATUS, TARGET_STATUS


class TestCrudApiHandler(unittest.TestCase):
    """
    Test cases for CRUD API Lambda handler.
    
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
    """
    
    def setUp(self):
        """Set up test environment."""
        self.sample_target = {
            "url": "https://example.com",
            "title": "Example Site",
            "description": "Test website",
            "status": TARGET_STATUS["ACTIVE"],
            "priority": 1
        }
        
        self.sample_event = {
            "httpMethod": "GET",
            "path": "/targets",
            "pathParameters": None,
            "queryStringParameters": None,
            "body": None
        }
        
        self.lambda_context = Mock()
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_lambda_handler_cors_preflight(self):
        """
        Test CORS preflight handling.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Cors.html
        """
        event = {
            "httpMethod": "OPTIONS",
            "path": "/targets"
        }
        
        response = lambda_handler(event, self.lambda_context)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["OK"])
        self.assertIn("Access-Control-Allow-Origin", response["headers"])
        self.assertIn("Access-Control-Allow-Methods", response["headers"])
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_lambda_handler_invalid_route(self):
        """
        Test handling of invalid routes.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Method.html
        """
        event = {
            "httpMethod": "GET",
            "path": "/invalid"
        }
        
        response = lambda_handler(event, self.lambda_context)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["NOT_FOUND"])
        body = json.loads(response["body"])
        self.assertIn("error", body)
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_handle_create_target_success(self):
        """
        Test successful target creation.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        table.wait_until_exists()
        
        body = json.dumps(self.sample_target)
        response = handle_create_target(body)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["CREATED"])
        body_data = json.loads(response["body"])
        self.assertIn("target_id", body_data)
        self.assertEqual(body_data["url"], self.sample_target["url"])
    
    @mock_dynamodb
    def test_handle_create_target_invalid_json(self):
        """
        Test target creation with invalid JSON.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
        """
        invalid_body = "{ invalid json }"
        response = handle_create_target(invalid_body)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["BAD_REQUEST"])
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertIn("Invalid JSON", body["error"])
    
    @mock_dynamodb
    def test_handle_create_target_missing_url(self):
        """
        Test target creation with missing required URL field.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
        """
        invalid_target = {
            "title": "Test Site",
            "description": "Missing URL"
        }
        
        body = json.dumps(invalid_target)
        response = handle_create_target(body)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["BAD_REQUEST"])
        body_data = json.loads(response["body"])
        self.assertIn("error", body_data)
        self.assertIn("url", body_data["error"])
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_handle_get_target_success(self):
        """
        Test successful target retrieval.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Insert test data
        target_id = "test-target-123"
        table.put_item(
            Item={
                'target_id': target_id,
                'url': 'https://example.com',
                'title': 'Test Site',
                'status': TARGET_STATUS["ACTIVE"]
            }
        )
        
        response = handle_get_target(target_id)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["OK"])
        body = json.loads(response["body"])
        self.assertEqual(body["target_id"], target_id)
        self.assertEqual(body["url"], "https://example.com")
    
    @mock_dynamodb
    def test_handle_get_target_invalid_id(self):
        """
        Test target retrieval with invalid ID format.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
        """
        invalid_id = "invalid-id-!@#"
        response = handle_get_target(invalid_id)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["BAD_REQUEST"])
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertIn("Invalid target ID", body["error"])
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_handle_update_target_success(self):
        """
        Test successful target update.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Insert test data
        target_id = "test-target-123"
        table.put_item(
            Item={
                'target_id': target_id,
                'url': 'https://example.com',
                'title': 'Old Title',
                'status': TARGET_STATUS["ACTIVE"]
            }
        )
        
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        body = json.dumps(update_data)
        response = handle_update_target(target_id, body)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["OK"])
        body_data = json.loads(response["body"])
        self.assertEqual(body_data["title"], "Updated Title")
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_handle_delete_target_success(self):
        """
        Test successful target deletion.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Insert test data
        target_id = "test-target-123"
        table.put_item(
            Item={
                'target_id': target_id,
                'url': 'https://example.com',
                'title': 'Test Site'
            }
        )
        
        response = handle_delete_target(target_id)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["NO_CONTENT"])
    
    @mock_dynamodb
    @patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': TABLE_NAME})
    def test_handle_list_targets_success(self):
        """
        Test successful target listing.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        table.wait_until_exists()
        
        # Insert test data
        table.put_item(
            Item={
                'target_id': 'target-1',
                'url': 'https://example1.com',
                'status': TARGET_STATUS["ACTIVE"]
            }
        )
        table.put_item(
            Item={
                'target_id': 'target-2',
                'url': 'https://example2.com',
                'status': TARGET_STATUS["INACTIVE"]
            }
        )
        
        response = handle_list_targets({})
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["OK"])
        body = json.loads(response["body"])
        self.assertIn("targets", body)
        self.assertIsInstance(body["targets"], list)
    
    def test_handle_list_targets_invalid_status(self):
        """
        Test target listing with invalid status filter.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
        """
        query_params = {"status": "invalid_status"}
        response = handle_list_targets(query_params)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["BAD_REQUEST"])
        body = json.loads(response["body"])
        self.assertIn("error", body)
    
    def test_create_response(self):
        """
        Test response creation utility.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
        """
        body_data = {"message": "success"}
        response = create_response(HTTP_STATUS["OK"], body_data)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["OK"])
        self.assertIn("headers", response)
        self.assertIn("body", response)
        
        parsed_body = json.loads(response["body"])
        self.assertEqual(parsed_body["message"], "success")
    
    def test_create_error_response(self):
        """
        Test error response creation utility.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/ResponseType.html
        """
        error_message = "Test error"
        response = create_error_response(HTTP_STATUS["BAD_REQUEST"], error_message)
        
        self.assertEqual(response["statusCode"], HTTP_STATUS["BAD_REQUEST"])
        self.assertIn("headers", response)
        
        body = json.loads(response["body"])
        self.assertEqual(body["error"], error_message)


if __name__ == '__main__':
    unittest.main()
"""
Test cases for DynamoDB CRUD operations
Tests all database operations, error handling, and data validation.

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
"""

import unittest
from unittest.mock import Mock, patch
import boto3
from moto import mock_dynamodb
from decimal import Decimal
from dynamodb_manager import DynamoDBManager
from constants import TABLE_NAME, TARGET_STATUS, HTTP_STATUS


class TestDynamoDBManager(unittest.TestCase):
    """
    Test cases for DynamoDB manager operations.
    
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html
    """
    
    def setUp(self):
        """Set up test environment with mocked DynamoDB."""
        self.table_name = TABLE_NAME
        
        self.sample_target = {
            "url": "https://example.com",
            "title": "Example Site",
            "description": "Test website",
            "status": TARGET_STATUS["ACTIVE"],
            "priority": 1,
            "tags": ["test", "example"],
            "crawl_frequency": 24
        }
    
    @mock_dynamodb
    def test_create_target_success(self):
        """
        Test successful target creation.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.add_global_secondary_index
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
        
        # Initialize manager
        db_manager = DynamoDBManager(self.table_name)
        
        # Test create operation
        result = db_manager.create_target(self.sample_target)
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["CREATED"])
        self.assertIn("target_id", result["body"])
        self.assertEqual(result["body"]["url"], self.sample_target["url"])
        self.assertEqual(result["body"]["status"], TARGET_STATUS["PENDING"])
        self.assertIn("created_at", result["body"])
        self.assertIn("updated_at", result["body"])
    
    @mock_dynamodb
    def test_get_target_success(self):
        """
        Test successful target retrieval.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
                'status': TARGET_STATUS["ACTIVE"],
                'priority': Decimal('1'),
                'created_at': '2024-01-15T10:30:00Z'
            }
        )
        
        # Initialize manager and test
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.get_target(target_id)
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["OK"])
        self.assertEqual(result["body"]["target_id"], target_id)
        self.assertEqual(result["body"]["url"], "https://example.com")
        self.assertEqual(result["body"]["priority"], 1)  # Converted from Decimal
    
    @mock_dynamodb
    def test_get_target_not_found(self):
        """
        Test target retrieval when target doesn't exist.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Initialize manager and test
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.get_target("nonexistent-target")
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["NOT_FOUND"])
        self.assertIn("error", result["body"])
    
    @mock_dynamodb
    def test_update_target_success(self):
        """
        Test successful target update.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
                'status': TARGET_STATUS["ACTIVE"],
                'created_at': '2024-01-15T10:30:00Z'
            }
        )
        
        # Initialize manager and test update
        db_manager = DynamoDBManager(self.table_name)
        update_data = {
            "title": "Updated Title",
            "description": "New description",
            "priority": 2
        }
        
        result = db_manager.update_target(target_id, update_data)
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["OK"])
        self.assertEqual(result["body"]["title"], "Updated Title")
        self.assertEqual(result["body"]["description"], "New description")
        self.assertEqual(result["body"]["priority"], 2)
        self.assertIn("updated_at", result["body"])
    
    @mock_dynamodb
    def test_update_target_not_found(self):
        """
        Test target update when target doesn't exist.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Initialize manager and test
        db_manager = DynamoDBManager(self.table_name)
        update_data = {"title": "Updated Title"}
        
        result = db_manager.update_target("nonexistent-target", update_data)
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["NOT_FOUND"])
        self.assertIn("error", result["body"])
    
    @mock_dynamodb
    def test_delete_target_success(self):
        """
        Test successful target deletion.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
        
        # Initialize manager and test
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.delete_target(target_id)
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["NO_CONTENT"])
        
        # Verify target is deleted
        response = table.get_item(Key={'target_id': target_id})
        self.assertNotIn('Item', response)
    
    @mock_dynamodb
    def test_delete_target_not_found(self):
        """
        Test target deletion when target doesn't exist.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Initialize manager and test
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.delete_target("nonexistent-target")
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["NOT_FOUND"])
        self.assertIn("error", result["body"])
    
    @mock_dynamodb
    def test_list_targets_success(self):
        """
        Test successful target listing.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/GlobalSecondaryIndex.html
        """
        # Setup DynamoDB mock
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
        targets = [
            {
                'target_id': 'target-1',
                'url': 'https://example1.com',
                'title': 'Site 1',
                'status': TARGET_STATUS["ACTIVE"],
                'priority': Decimal('1')
            },
            {
                'target_id': 'target-2',
                'url': 'https://example2.com',
                'title': 'Site 2',
                'status': TARGET_STATUS["INACTIVE"],
                'priority': Decimal('2')
            },
            {
                'target_id': 'target-3',
                'url': 'https://example3.com',
                'title': 'Site 3',
                'status': TARGET_STATUS["ACTIVE"],
                'priority': Decimal('1')
            }
        ]
        
        for target in targets:
            table.put_item(Item=target)
        
        # Initialize manager and test list all
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.list_targets()
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["OK"])
        self.assertIn("targets", result["body"])
        self.assertIn("count", result["body"])
        self.assertGreaterEqual(result["body"]["count"], 3)
    
    @mock_dynamodb
    def test_list_targets_with_status_filter(self):
        """
        Test target listing with status filter.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/GlobalSecondaryIndex.html
        """
        # Setup DynamoDB mock with GSI
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=self.table_name,
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
        
        # Insert test data with different statuses
        targets = [
            {
                'target_id': 'active-1',
                'url': 'https://active1.com',
                'status': TARGET_STATUS["ACTIVE"]
            },
            {
                'target_id': 'active-2',
                'url': 'https://active2.com',
                'status': TARGET_STATUS["ACTIVE"]
            },
            {
                'target_id': 'inactive-1',
                'url': 'https://inactive1.com',
                'status': TARGET_STATUS["INACTIVE"]
            }
        ]
        
        for target in targets:
            table.put_item(Item=target)
        
        # Initialize manager and test filtered list
        db_manager = DynamoDBManager(self.table_name)
        result = db_manager.list_targets(status_filter=TARGET_STATUS["ACTIVE"])
        
        self.assertEqual(result["statusCode"], HTTP_STATUS["OK"])
        self.assertIn("targets", result["body"])
        
        # All returned targets should have active status
        for target in result["body"]["targets"]:
            self.assertEqual(target["status"], TARGET_STATUS["ACTIVE"])
    
    def test_convert_decimals_to_numbers(self):
        """
        Test Decimal to number conversion utility.
        
        Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/AttributeType.html
        """
        from dynamodb_manager import convert_decimals_to_numbers
        
        # Test data with Decimals
        data = {
            'string_field': 'test',
            'decimal_field': Decimal('123.45'),
            'int_decimal': Decimal('10'),
            'nested': {
                'decimal_nested': Decimal('67.89'),
                'string_nested': 'nested_test'
            },
            'list_field': [Decimal('1.1'), 'string', Decimal('2.2')],
            'normal_int': 42,
            'normal_float': 3.14
        }
        
        result = convert_decimals_to_numbers(data)
        
        # Check conversions
        self.assertEqual(result['string_field'], 'test')
        self.assertEqual(result['decimal_field'], 123.45)
        self.assertEqual(result['int_decimal'], 10)
        self.assertEqual(result['nested']['decimal_nested'], 67.89)
        self.assertEqual(result['nested']['string_nested'], 'nested_test')
        self.assertEqual(result['list_field'], [1.1, 'string', 2.2])
        self.assertEqual(result['normal_int'], 42)
        self.assertEqual(result['normal_float'], 3.14)


if __name__ == '__main__':
    unittest.main()
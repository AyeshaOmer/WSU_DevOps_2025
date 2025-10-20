import json
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

# Import the lambda function
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../week2prac/crud_api'))

import sites_crud


class TestSitesCrud:
    """Test class for Sites CRUD Lambda function"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test"""
        self.mock_table = Mock()
        self.original_table = sites_crud.table
        sites_crud.table = self.mock_table
        
        # Setup common test data
        self.sample_site = {
            'site_id': str(uuid.uuid4()),
            'url': 'https://example.com',
            'name': 'Example Site',
            'description': 'Test site',
            'tags': ['test', 'example'],
            'enabled': True,
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z'
        }
        
    def teardown_method(self):
        """Cleanup after each test"""
        sites_crud.table = self.original_table

    def test_lambda_handler_get_single_site(self):
        """Test GET request for a single site"""
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'site_id': self.sample_site['site_id']}
        }
        
        # Mock DynamoDB response
        self.mock_table.get_item.return_value = {'Item': self.sample_site}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['site_id'] == self.sample_site['site_id']
        assert body['url'] == self.sample_site['url']
        
    def test_lambda_handler_get_single_site_not_found(self):
        """Test GET request for non-existent site"""
        site_id = str(uuid.uuid4())
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'site_id': site_id}
        }
        
        # Mock DynamoDB response - no item found
        self.mock_table.get_item.return_value = {}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']
        
    def test_lambda_handler_list_sites(self):
        """Test GET request to list all sites"""
        event = {
            'httpMethod': 'GET',
            'pathParameters': None
        }
        
        # Mock DynamoDB response
        sites_list = [self.sample_site, {**self.sample_site, 'site_id': str(uuid.uuid4())}]
        self.mock_table.scan.return_value = {'Items': sites_list}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['sites']) == 2
        
    def test_lambda_handler_create_site(self):
        """Test POST request to create a new site"""
        new_site_data = {
            'url': 'https://newsite.com',
            'name': 'New Site',
            'description': 'A new test site'
        }
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(new_site_data)
        }
        
        # Mock DynamoDB responses
        self.mock_table.scan.return_value = {'Items': []}  # No existing sites
        self.mock_table.put_item.return_value = {}
        
        with patch('sites_crud.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = 'test-uuid'
            with patch('sites_crud.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T00:00:00'
                
                response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['url'] == new_site_data['url']
        assert body['name'] == new_site_data['name']
        assert body['site_id'] == 'test-uuid'
        
    def test_lambda_handler_create_site_missing_url(self):
        """Test POST request with missing URL"""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'name': 'Site without URL'})
        }
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'url is required' in body['error']
        
    def test_lambda_handler_create_site_invalid_url(self):
        """Test POST request with invalid URL format"""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'url': 'invalid-url'})
        }
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'must start with http' in body['error']
        
    def test_lambda_handler_create_site_duplicate_url(self):
        """Test POST request with URL that already exists"""
        duplicate_url = 'https://existing.com'
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'url': duplicate_url})
        }
        
        # Mock DynamoDB response - URL already exists
        self.mock_table.scan.return_value = {'Items': [{'url': duplicate_url}]}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert 'already exists' in body['error']
        
    def test_lambda_handler_update_site(self):
        """Test PUT request to update a site"""
        site_id = self.sample_site['site_id']
        update_data = {'name': 'Updated Site Name', 'enabled': False}
        
        event = {
            'httpMethod': 'PUT',
            'pathParameters': {'site_id': site_id},
            'body': json.dumps(update_data)
        }
        
        # Mock DynamoDB responses
        self.mock_table.get_item.return_value = {'Item': self.sample_site}
        updated_site = {**self.sample_site, **update_data}
        self.mock_table.update_item.return_value = {'Attributes': updated_site}
        
        with patch('sites_crud.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = '2025-01-01T01:00:00'
            
            response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['name'] == update_data['name']
        assert body['enabled'] == update_data['enabled']
        
    def test_lambda_handler_update_site_not_found(self):
        """Test PUT request for non-existent site"""
        site_id = str(uuid.uuid4())
        event = {
            'httpMethod': 'PUT',
            'pathParameters': {'site_id': site_id},
            'body': json.dumps({'name': 'New Name'})
        }
        
        # Mock DynamoDB response - no item found
        self.mock_table.get_item.return_value = {}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']
        
    def test_lambda_handler_update_site_duplicate_url(self):
        """Test PUT request with URL that conflicts with another site"""
        site_id = self.sample_site['site_id']
        conflicting_url = 'https://conflict.com'
        
        event = {
            'httpMethod': 'PUT',
            'pathParameters': {'site_id': site_id},
            'body': json.dumps({'url': conflicting_url})
        }
        
        # Mock DynamoDB responses
        self.mock_table.get_item.return_value = {'Item': self.sample_site}
        self.mock_table.scan.return_value = {'Items': [{'url': conflicting_url, 'site_id': 'other-id'}]}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert 'already exists' in body['error']
        
    def test_lambda_handler_delete_site(self):
        """Test DELETE request to delete a site"""
        site_id = self.sample_site['site_id']
        event = {
            'httpMethod': 'DELETE',
            'pathParameters': {'site_id': site_id}
        }
        
        # Mock DynamoDB responses
        self.mock_table.get_item.return_value = {'Item': self.sample_site}
        self.mock_table.delete_item.return_value = {}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'deleted successfully' in body['message']
        assert body['site_id'] == site_id
        
    def test_lambda_handler_delete_site_not_found(self):
        """Test DELETE request for non-existent site"""
        site_id = str(uuid.uuid4())
        event = {
            'httpMethod': 'DELETE',
            'pathParameters': {'site_id': site_id}
        }
        
        # Mock DynamoDB response - no item found
        self.mock_table.get_item.return_value = {}
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']
        
    def test_lambda_handler_unsupported_method(self):
        """Test unsupported HTTP method"""
        event = {
            'httpMethod': 'PATCH',
            'pathParameters': None
        }
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert 'not allowed' in body['error']
        
    def test_lambda_handler_invalid_json(self):
        """Test request with invalid JSON body"""
        event = {
            'httpMethod': 'POST',
            'body': 'invalid json'
        }
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['error']
        
    def test_lambda_handler_dynamodb_error(self):
        """Test handling of DynamoDB errors"""
        event = {
            'httpMethod': 'GET',
            'pathParameters': None
        }
        
        # Mock DynamoDB client error
        error_response = {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}}
        self.mock_table.scan.side_effect = ClientError(error_response, 'Scan')
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to retrieve sites' in body['error']
        
    def test_lambda_handler_unexpected_error(self):
        """Test handling of unexpected errors"""
        event = {
            'httpMethod': 'GET',
            'pathParameters': None
        }
        
        # Mock unexpected error
        self.mock_table.scan.side_effect = Exception('Unexpected error')
        
        response = sites_crud.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Internal server error' in body['error']
        
    def test_success_response(self):
        """Test success response helper function"""
        data = {'test': 'data'}
        response = sites_crud.success_response(data, 201)
        
        assert response['statusCode'] == 201
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert json.loads(response['body']) == data
        
    def test_error_response(self):
        """Test error response helper function"""
        response = sites_crud.error_response(400, 'Test error')
        
        assert response['statusCode'] == 400
        assert 'Access-Control-Allow-Origin' in response['headers']
        body = json.loads(response['body'])
        assert body['error'] == 'Test error'
        assert body['statusCode'] == 400
        
    def test_get_site_function(self):
        """Test get_site helper function directly"""
        site_id = self.sample_site['site_id']
        self.mock_table.get_item.return_value = {'Item': self.sample_site}
        
        response = sites_crud.get_site(site_id)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['site_id'] == site_id
        
    def test_list_sites_function(self):
        """Test list_sites helper function directly"""
        sites_list = [self.sample_site]
        self.mock_table.scan.return_value = {'Items': sites_list}
        
        response = sites_crud.list_sites()
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert len(body['sites']) == 1

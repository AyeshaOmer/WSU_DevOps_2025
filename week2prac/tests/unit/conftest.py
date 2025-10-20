"""
Unit test fixtures and mocking setup
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test data directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

@pytest.fixture
def mock_cloudwatch():
    """Mock CloudWatch client for unit tests"""
    with patch('boto3.client') as mock_client:
        mock_cw = Mock()
        mock_client.return_value = mock_cw
        
        # Mock put_metric_data response
        mock_cw.put_metric_data.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        yield mock_cw

@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB resource for unit tests"""
    with patch('boto3.resource') as mock_resource:
        mock_dynamo = Mock()
        mock_table = Mock()
        
        mock_resource.return_value = mock_dynamo
        mock_dynamo.Table.return_value = mock_table
        
        # Mock put_item response
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        yield mock_table

@pytest.fixture
def mock_urllib3_response():
    """Mock urllib3 HTTP response"""
    mock_response = Mock()
    mock_response.status = 200
    mock_response.data = b"OK"
    return mock_response

@pytest.fixture
def mock_http_pool():
    """Mock urllib3 PoolManager"""
    with patch('urllib3.PoolManager') as mock_pool_class:
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        yield mock_pool

@pytest.fixture
def sample_eventbridge_event():
    """Load sample EventBridge event from fixture"""
    with open(FIXTURES_DIR / "test_cloudwatch_event.json", 'r') as f:
        return json.load(f)

@pytest.fixture
def sample_sns_event():
    """Load sample SNS event from fixture"""
    with open(FIXTURES_DIR / "test_sns_message.json", 'r') as f:
        return json.load(f)

@pytest.fixture
def sample_sites():
    """Load sample sites from fixture"""
    with open(FIXTURES_DIR / "test_sites.json", 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_sites_file(sample_sites, tmp_path):
    """Create temporary sites.json file for testing"""
    sites_file = tmp_path / "sites.json"
    with open(sites_file, 'w') as f:
        json.dump(sample_sites, f)
    return str(sites_file)

@pytest.fixture
def mock_environment_vars():
    """Mock environment variables"""
    test_env = {
        'METRIC_NAMESPACE': 'TestMonitor',
        'TABLE_NAME': 'TestTable',
        'AWS_REGION': 'ap-southeast-2'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env

@pytest.fixture
def lambda_context():
    """Mock AWS Lambda context object"""
    context = Mock()
    context.function_name = "TestFunction"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:ap-southeast-2:934249453094:function:TestFunction"
    context.memory_limit_in_mb = 128
    context.remaining_time_in_millis = lambda: 30000
    context.log_group_name = "/aws/lambda/TestFunction"
    context.log_stream_name = "2023/10/20/[$LATEST]test123"
    context.aws_request_id = "test-request-id"
    return context

@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing"""
    with patch('time.time') as mock_time_func:
        # Return consistent timestamps for testing
        mock_time_func.side_effect = [1697800000.0, 1697800001.5]  # 1.5 second difference
        yield mock_time_func

@pytest.fixture
def cdk_app():
    """Mock CDK App for stack testing"""
    import aws_cdk as cdk
    return cdk.App()

@pytest.fixture
def mock_cdk_stack_props():
    """Mock CDK stack properties"""
    import aws_cdk as cdk
    return {
        'env': cdk.Environment(account='934249453094', region='ap-southeast-2'),
        'description': 'Test stack for unit testing'
    }
"""
Pytest fixtures for integration tests
"""
import pytest
import boto3
import time
from ..aws_test_helpers import AWSTestHelper
from ..test_config import (
    AWS_REGION, TEST_STACK_PREFIX, get_resource_name,
    LAMBDA_FUNCTION_PREFIX, DYNAMO_TABLE_PREFIX, ALARM_TOPIC_PREFIX
)

@pytest.fixture(scope="session")
def aws_helper():
    """AWS helper instance for tests"""
    return AWSTestHelper()

@pytest.fixture(scope="session")
def stack_name():
    """Beta stack name for testing"""
    return f"{TEST_STACK_PREFIX}-WebHealthStack"

@pytest.fixture(scope="session")
def monitor_lambda_name(stack_name):
    """Monitor Lambda function name"""
    # The actual function name includes stack prefix
    return f"WebMonitorPipelineStack-{TEST_STACK_PREFIX}WebHealthStackMonitorNYT"

@pytest.fixture(scope="session")
def alarm_logger_lambda_name(stack_name):
    """Alarm logger Lambda function name"""
    return f"WebMonitorPipelineStack-{TEST_STACK_PREFIX}WebHealthStackAlarmLoggerLambda"

@pytest.fixture(scope="session")
def dynamodb_table_name(stack_name):
    """DynamoDB table name for alarm logs"""
    return get_resource_name(DYNAMO_TABLE_PREFIX, stack_name)

@pytest.fixture(scope="session")
def sns_topic_arn(stack_name):
    """SNS topic ARN for alarms"""
    topic_name = get_resource_name(ALARM_TOPIC_PREFIX, stack_name)
    return f"arn:aws:sns:{AWS_REGION}:934249453094:{topic_name}"

@pytest.fixture
def wait_for_propagation():
    """Wait for AWS resource propagation"""
    def _wait(seconds=10):
        time.sleep(seconds)
    return _wait

@pytest.fixture(scope="session") 
def cloudwatch_client():
    """CloudWatch client"""
    return boto3.client('cloudwatch', region_name=AWS_REGION)

@pytest.fixture(scope="session")
def lambda_client():
    """Lambda client"""
    return boto3.client('lambda', region_name=AWS_REGION)

@pytest.fixture(scope="session")
def dynamodb_resource():
    """DynamoDB resource"""
    return boto3.resource('dynamodb', region_name=AWS_REGION)
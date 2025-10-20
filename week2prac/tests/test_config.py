"""
Configuration for integration tests
"""
import os

# AWS Configuration
AWS_REGION = "ap-southeast-2"
ACCOUNT_ID = "934249453094"

# Test environment settings
TEST_STACK_PREFIX = "Beta"  # Use Beta stack for testing
METRIC_NAMESPACE = "NYTMonitor"

# Resource naming patterns (will be suffixed with stack name)
ALARM_TOPIC_PREFIX = "WebMonitorAlarms"
DYNAMO_TABLE_PREFIX = "WebMonitorAlarmLogs"
LAMBDA_FUNCTION_PREFIX = "MonitorNYT"
ALARM_LOGGER_PREFIX = "AlarmLoggerLambda"

# Test sites for safe testing
TEST_SITES = [
    "https://httpbin.org/status/200",  # Always returns 200
    "https://httpbin.org/delay/1",     # Returns 200 with 1s delay
    "https://httpbin.org/status/500"   # Returns 500 for testing failures
]

# Timeouts
LAMBDA_TIMEOUT = 30
CLOUDWATCH_WAIT_TIME = 60  # Time to wait for metrics to appear
ALARM_WAIT_TIME = 300      # Time to wait for alarms to trigger

def get_resource_name(prefix: str, stack_name: str = None) -> str:
    """Get full resource name with stack suffix"""
    if stack_name is None:
        stack_name = f"{TEST_STACK_PREFIX}-WebHealthStack"
    return f"{prefix}-{stack_name}"
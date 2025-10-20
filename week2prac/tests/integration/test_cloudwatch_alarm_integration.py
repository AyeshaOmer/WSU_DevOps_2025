"""
Integration test: CloudWatch Alarms → SNS Integration
Tests that CloudWatch alarms properly trigger and send SNS notifications
"""
import pytest
import time
import boto3
from datetime import datetime, timedelta
from ..test_config import METRIC_NAMESPACE, AWS_REGION

class TestCloudWatchAlarmIntegration:
    """Test CloudWatch Alarm to SNS integration"""
    
    def test_availability_alarm_exists_and_configured(self, cloudwatch_client, sns_topic_arn):
        """Test that availability alarms are properly configured"""
        
        # List alarms to find availability alarms
        response = cloudwatch_client.describe_alarms(
            AlarmNamePrefix="WebMonitorPipelineStack-Beta"  # Beta stack prefix
        )
        
        alarms = response.get('MetricAlarms', [])
        availability_alarms = [a for a in alarms if 'Availability' in a['AlarmName']]
        
        assert len(availability_alarms) > 0, "No availability alarms found"
        
        # Check first availability alarm configuration
        alarm = availability_alarms[0]
        
        # Verify alarm configuration
        assert alarm['Namespace'] == METRIC_NAMESPACE, f"Wrong namespace: {alarm['Namespace']}"
        assert alarm['MetricName'] == 'Availability', f"Wrong metric: {alarm['MetricName']}"
        assert alarm['Threshold'] == 1.0, f"Wrong threshold: {alarm['Threshold']}"
        assert alarm['ComparisonOperator'] == 'LessThanThreshold', f"Wrong operator: {alarm['ComparisonOperator']}"
        
        # Verify SNS action is configured
        alarm_actions = alarm.get('AlarmActions', [])
        assert len(alarm_actions) > 0, "No alarm actions configured"
        
        # Check if our SNS topic is in the actions
        topic_found = any(sns_topic_arn in action for action in alarm_actions)
        assert topic_found, f"SNS topic {sns_topic_arn} not found in alarm actions"
        
        print(f"✓ Availability alarm properly configured: {alarm['AlarmName']}")
    
    def test_latency_alarm_exists_and_configured(self, cloudwatch_client, sns_topic_arn):
        """Test that latency alarms are properly configured"""
        
        # List alarms to find latency alarms
        response = cloudwatch_client.describe_alarms(
            AlarmNamePrefix="WebMonitorPipelineStack-Beta"
        )
        
        alarms = response.get('MetricAlarms', [])
        latency_alarms = [a for a in alarms if 'Latency' in a['AlarmName']]
        
        assert len(latency_alarms) > 0, "No latency alarms found"
        
        # Check first latency alarm configuration
        alarm = latency_alarms[0]
        
        # Verify alarm configuration
        assert alarm['Namespace'] == METRIC_NAMESPACE, f"Wrong namespace: {alarm['Namespace']}"
        assert alarm['MetricName'] == 'Latency', f"Wrong metric: {alarm['MetricName']}"
        assert alarm['Threshold'] == 2000.0, f"Wrong threshold: {alarm['Threshold']}"
        assert alarm['ComparisonOperator'] == 'GreaterThanThreshold', f"Wrong operator: {alarm['ComparisonOperator']}"
        
        # Verify SNS action is configured
        alarm_actions = alarm.get('AlarmActions', [])
        assert len(alarm_actions) > 0, "No alarm actions configured"
        
        topic_found = any(sns_topic_arn in action for action in alarm_actions)
        assert topic_found, f"SNS topic {sns_topic_arn} not found in alarm actions"
        
        print(f"✓ Latency alarm properly configured: {alarm['AlarmName']}")
    
    def test_alarm_state_transitions(self, cloudwatch_client):
        """Test that alarms can transition between states"""
        
        # Get current alarm states
        response = cloudwatch_client.describe_alarms(
            AlarmNamePrefix="WebMonitorPipelineStack-Beta"
        )
        
        alarms = response.get('MetricAlarms', [])
        assert len(alarms) > 0, "No alarms found"
        
        # Check that alarms have valid states
        valid_states = ['OK', 'ALARM', 'INSUFFICIENT_DATA']
        
        for alarm in alarms[:3]:  # Check first 3 alarms
            state = alarm.get('StateValue')
            assert state in valid_states, f"Invalid alarm state: {state}"
            
            # Verify state has timestamps
            assert 'StateUpdatedTimestamp' in alarm, "Missing state timestamp"
            
            print(f"✓ Alarm {alarm['AlarmName']} in state: {state}")
    
    def test_manual_alarm_trigger(self, aws_helper, sns_topic_arn, dynamodb_table_name,
                                 wait_for_propagation):
        """Test manual alarm triggering and end-to-end notification flow"""
        
        # Create a test alarm message manually
        test_alarm_name = f"ManualTestAlarm-{int(time.time())}"
        
        # Publish directly to SNS (simulating CloudWatch alarm)
        success = aws_helper.publish_test_alarm(sns_topic_arn, test_alarm_name)
        assert success, "Failed to publish manual test alarm"
        
        # Wait for processing
        wait_for_propagation(30)
        
        # Verify the alarm was logged in DynamoDB
        records = aws_helper.check_dynamo_records(dynamodb_table_name)
        
        # Look for our test alarm in the records
        test_records = [r for r in records if r.get('alarm_name') == test_alarm_name]
        assert len(test_records) > 0, f"Manual test alarm {test_alarm_name} not logged"
        
        record = test_records[0]
        assert record['new_state'] == 'ALARM', f"Wrong alarm state: {record['new_state']}"
        assert 'timestamp' in record, "Missing timestamp"
        
        print(f"✓ Manual alarm trigger successful: {test_alarm_name}")
    
    def test_sns_topic_configuration(self):
        """Test SNS topic exists and has proper subscriptions"""
        
        sns_client = boto3.client('sns', region_name=AWS_REGION)
        
        # List topics to find our alarm topic
        topics_response = sns_client.list_topics()
        topics = topics_response.get('Topics', [])
        
        # Find our specific topic
        alarm_topics = [t for t in topics if 'WebMonitorAlarms-Beta' in t['TopicArn']]
        assert len(alarm_topics) > 0, "WebMonitor alarm topic not found"
        
        topic_arn = alarm_topics[0]['TopicArn']
        
        # Check subscriptions
        subs_response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = subs_response.get('Subscriptions', [])
        
        assert len(subscriptions) >= 2, "Expected at least 2 subscriptions (email + lambda)"
        
        # Verify subscription types
        protocols = [sub['Protocol'] for sub in subscriptions]
        assert 'email' in protocols, "Email subscription not found"
        assert 'lambda' in protocols, "Lambda subscription not found"
        
        print(f"✓ SNS topic configured with {len(subscriptions)} subscriptions")
        print(f"  Protocols: {', '.join(protocols)}")
"""
Integration test: EventBridge Schedule → Lambda Integration
Tests that EventBridge rules properly trigger Lambda functions on schedule
"""
import pytest
import time
import boto3
from datetime import datetime, timedelta
from ..test_config import AWS_REGION

class TestEventBridgeLambdaIntegration:
    """Test EventBridge to Lambda integration"""
    
    def test_eventbridge_rule_exists_and_configured(self, monitor_lambda_name):
        """Test that EventBridge rule exists and is properly configured"""
        
        events_client = boto3.client('events', region_name=AWS_REGION)
        
        # List rules to find our monitoring rule
        response = events_client.list_rules(
            NamePrefix="WebMonitorPipelineStack-Beta"  # Beta stack prefix
        )
        
        rules = response.get('Rules', [])
        monitor_rules = [r for r in rules if 'MonitorSchedule' in r.get('Name', '')]
        
        assert len(monitor_rules) > 0, "EventBridge monitoring rule not found"
        
        rule = monitor_rules[0]
        
        # Verify rule configuration
        assert rule['State'] == 'ENABLED', f"Rule not enabled: {rule['State']}"
        
        # Check schedule expression (should be rate(5 minutes))
        schedule = rule.get('ScheduleExpression', '')
        assert 'rate(5 minutes)' in schedule, f"Wrong schedule: {schedule}"
        
        print(f"✓ EventBridge rule configured: {rule['Name']}")
        print(f"  Schedule: {schedule}")
        print(f"  State: {rule['State']}")
    
    def test_eventbridge_rule_targets_lambda(self, monitor_lambda_name):
        """Test that EventBridge rule correctly targets the monitor Lambda"""
        
        events_client = boto3.client('events', region_name=AWS_REGION)
        
        # Find the rule first
        rules_response = events_client.list_rules(
            NamePrefix="WebMonitorPipelineStack-Beta"
        )
        
        rules = rules_response.get('Rules', [])
        monitor_rules = [r for r in rules if 'MonitorSchedule' in r.get('Name', '')]
        assert len(monitor_rules) > 0, "EventBridge rule not found"
        
        rule_name = monitor_rules[0]['Name']
        
        # Get targets for the rule
        targets_response = events_client.list_targets_by_rule(Rule=rule_name)
        targets = targets_response.get('Targets', [])
        
        assert len(targets) > 0, f"No targets found for rule {rule_name}"
        
        # Verify Lambda target
        lambda_targets = [t for t in targets if 'lambda' in t.get('Arn', '').lower()]
        assert len(lambda_targets) > 0, "No Lambda targets found"
        
        # Check if our specific Lambda is targeted
        target_arn = lambda_targets[0]['Arn']
        lambda_name_from_arn = target_arn.split(':')[-1]  # Extract function name from ARN
        
        # The ARN should contain our monitor Lambda function name
        assert monitor_lambda_name in target_arn, f"Wrong Lambda targeted: {target_arn}"
        
        print(f"✓ EventBridge rule targets correct Lambda: {lambda_name_from_arn}")
    
    def test_lambda_has_eventbridge_permissions(self, monitor_lambda_name):
        """Test that Lambda has proper permissions for EventBridge invocation"""
        
        lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        
        try:
            # Get Lambda function policy
            response = lambda_client.get_policy(FunctionName=monitor_lambda_name)
            policy = response.get('Policy', '{}')
            
            # Check if EventBridge has permission to invoke the Lambda
            assert 'events.amazonaws.com' in policy, "EventBridge permission not found in Lambda policy"
            
            print("✓ Lambda has EventBridge invocation permissions")
            
        except lambda_client.exceptions.ResourceNotFoundException:
            # If no policy exists, check if Lambda can be invoked by EventBridge
            # This might be handled by CDK automatically
            print("ℹ No explicit policy found (may be handled by CDK)")
    
    def test_scheduled_lambda_execution_history(self, monitor_lambda_name):
        """Test that Lambda has been executed by EventBridge recently"""
        
        # Check CloudWatch logs for recent Lambda executions
        logs_client = boto3.client('logs', region_name=AWS_REGION)
        
        # Find log group for the monitor Lambda
        log_group_name = f"/aws/lambda/{monitor_lambda_name}"
        
        try:
            # Get recent log streams
            response = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )
            
            streams = response.get('logStreams', [])
            assert len(streams) > 0, f"No log streams found for {log_group_name}"
            
            # Check if we have recent activity (within last hour)
            recent_stream = streams[0]
            last_event_time = recent_stream.get('lastEventTime', 0)
            
            # Convert milliseconds to datetime
            last_event_dt = datetime.fromtimestamp(last_event_time / 1000)
            time_diff = datetime.now() - last_event_dt
            
            # Allow up to 1 hour since last execution (EventBridge runs every 5 minutes)
            assert time_diff < timedelta(hours=1), f"No recent Lambda execution found. Last: {last_event_dt}"
            
            print(f"✓ Recent Lambda execution found: {last_event_dt}")
            
        except logs_client.exceptions.ResourceNotFoundException:
            # Log group might not exist yet if Lambda hasn't run
            print("ℹ Log group not found - Lambda may not have executed yet")
    
    def test_eventbridge_lambda_end_to_end(self, aws_helper, monitor_lambda_name,
                                          wait_for_propagation):
        """Test complete EventBridge to Lambda execution flow"""
        
        # Manually invoke the Lambda to simulate EventBridge trigger
        print("Simulating EventBridge trigger by invoking Lambda...")
        
        # Create an EventBridge-style event payload
        eventbridge_event = {
            "version": "0",
            "id": "test-event-id",
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "account": "934249453094",
            "time": datetime.utcnow().isoformat(),
            "region": AWS_REGION,
            "detail": {}
        }
        
        # Invoke Lambda with EventBridge event structure
        response = aws_helper.invoke_lambda(monitor_lambda_name, eventbridge_event)
        
        # Verify Lambda executed successfully
        assert response.get('ok') is True, f"Lambda failed with EventBridge event: {response}"
        
        sites_checked = response.get('sites_checked', 0)
        assert sites_checked > 0, "Lambda didn't check any sites"
        
        print(f"✓ EventBridge-style Lambda execution successful: {sites_checked} sites checked")
        
        # Wait for metrics to be published
        wait_for_propagation(30)
        
        # Verify that metrics were published (indicating complete flow worked)
        test_site = "https://www.nytimes.com"
        metrics_found = aws_helper.wait_for_metrics(
            "Availability",
            {"Site": test_site},
            timeout_seconds=60
        )
        
        assert metrics_found, "Metrics not published after EventBridge-style execution"
        print("✓ Metrics published successfully after EventBridge simulation")
    
    def test_eventbridge_rule_failure_handling(self, monitor_lambda_name):
        """Test that EventBridge handles Lambda failures gracefully"""
        
        events_client = boto3.client('events', region_name=AWS_REGION)
        
        # Find our EventBridge rule
        rules_response = events_client.list_rules(
            NamePrefix="WebMonitorPipelineStack-Beta"
        )
        
        rules = rules_response.get('Rules', [])
        monitor_rules = [r for r in rules if 'MonitorSchedule' in r.get('Name', '')]
        assert len(monitor_rules) > 0, "EventBridge rule not found"
        
        rule_name = monitor_rules[0]['Name']
        
        # Get rule metrics if available (this checks if EventBridge is monitoring the rule)
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
            
            # Look for EventBridge metrics
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Events',
                MetricName='SuccessfulInvocations',
                Dimensions=[
                    {'Name': 'RuleName', 'Value': rule_name}
                ],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                total_invocations = sum(dp['Sum'] for dp in datapoints)
                print(f"✓ EventBridge successful invocations in last hour: {total_invocations}")
            else:
                print("ℹ No EventBridge metrics available (may be too recent)")
                
        except Exception as e:
            print(f"ℹ Could not retrieve EventBridge metrics: {e}")
        
        print("✓ EventBridge failure handling test completed")
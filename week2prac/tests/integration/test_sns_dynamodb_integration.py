"""
Integration test: SNS → Alarm Logger Lambda → DynamoDB
Tests that alarm notifications are properly logged to DynamoDB
"""
import pytest
import time
import json
from datetime import datetime
from ..test_config import ALARM_WAIT_TIME

class TestSNSDynamoDBIntegration:
    """Test SNS to DynamoDB alarm logging integration"""
    
    def test_alarm_message_logged_to_dynamodb(self, aws_helper, sns_topic_arn, 
                                             dynamodb_table_name, wait_for_propagation):
        """Test that SNS alarm messages are logged to DynamoDB"""
        
        # Create a unique test alarm name to avoid conflicts
        test_alarm_name = f"TestAlarm-{int(time.time())}"
        
        # Publish a test alarm message to SNS
        success = aws_helper.publish_test_alarm(sns_topic_arn, test_alarm_name)
        assert success, "Failed to publish test alarm to SNS"
        
        # Wait for Lambda processing and DynamoDB write
        wait_for_propagation(30)
        
        # Check if the alarm was logged in DynamoDB
        records = aws_helper.check_dynamo_records(
            dynamodb_table_name,
            key_condition={
                'KeyConditionExpression': boto3.dynamodb.conditions.Key('alarm_name').eq(test_alarm_name)
            }
        )
        
        assert len(records) > 0, f"No records found for alarm {test_alarm_name}"
        
        # Verify the record structure
        record = records[0]
        assert record['alarm_name'] == test_alarm_name
        assert record['new_state'] == 'ALARM'
        assert 'timestamp' in record
        assert 'reason' in record
        
        print(f"Successfully logged alarm {test_alarm_name} to DynamoDB")
    
    def test_alarm_logger_lambda_processes_sns_message(self, aws_helper, 
                                                      alarm_logger_lambda_name):
        """Test that alarm logger Lambda can process SNS messages directly"""
        
        # Create a test SNS event payload
        test_alarm_name = f"DirectTestAlarm-{int(time.time())}"
        sns_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": test_alarm_name,
                            "AlarmDescription": "Direct test alarm",
                            "NewStateValue": "ALARM",
                            "NewStateReason": "Direct Lambda test",
                            "StateChangeTime": datetime.utcnow().isoformat()
                        })
                    }
                }
            ]
        }
        
        # Invoke the alarm logger Lambda directly
        response = aws_helper.invoke_lambda(alarm_logger_lambda_name, sns_event)
        
        # Verify Lambda processed successfully
        assert response.get('status') == 'success', f"Lambda failed: {response}"
        assert response.get('records_logged') == 1, f"Expected 1 record logged, got {response.get('records_logged')}"
        
        print(f"Alarm logger Lambda successfully processed {test_alarm_name}")
    
    def test_multiple_alarms_logged_correctly(self, aws_helper, sns_topic_arn, 
                                            dynamodb_table_name, wait_for_propagation):
        """Test that multiple alarm messages are logged correctly"""
        
        # Create multiple test alarms
        base_time = int(time.time())
        test_alarms = [
            f"MultiTest1-{base_time}",
            f"MultiTest2-{base_time}",
            f"MultiTest3-{base_time}"
        ]
        
        # Publish multiple test alarms
        for alarm_name in test_alarms:
            success = aws_helper.publish_test_alarm(sns_topic_arn, alarm_name)
            assert success, f"Failed to publish alarm {alarm_name}"
            time.sleep(2)  # Small delay between publishes
        
        # Wait for processing
        wait_for_propagation(45)
        
        # Check that all alarms were logged
        for alarm_name in test_alarms:
            records = aws_helper.check_dynamo_records(
                dynamodb_table_name,
                key_condition={
                    'KeyConditionExpression': boto3.dynamodb.conditions.Key('alarm_name').eq(alarm_name)
                }
            )
            assert len(records) > 0, f"Alarm {alarm_name} not found in DynamoDB"
        
        print(f"Successfully logged {len(test_alarms)} alarms to DynamoDB")
    
    def test_dynamodb_table_structure(self, dynamodb_resource, dynamodb_table_name):
        """Test that DynamoDB table has correct structure"""
        
        try:
            table = dynamodb_resource.Table(dynamodb_table_name)
            
            # Check table exists and is active
            table.load()
            assert table.table_status == 'ACTIVE', f"Table status: {table.table_status}"
            
            # Check key schema
            key_schema = table.key_schema
            partition_key = next((key for key in key_schema if key['KeyType'] == 'HASH'), None)
            sort_key = next((key for key in key_schema if key['KeyType'] == 'RANGE'), None)
            
            assert partition_key is not None, "Partition key not found"
            assert partition_key['AttributeName'] == 'alarm_name', f"Wrong partition key: {partition_key['AttributeName']}"
            
            assert sort_key is not None, "Sort key not found" 
            assert sort_key['AttributeName'] == 'timestamp', f"Wrong sort key: {sort_key['AttributeName']}"
            
            print(f"DynamoDB table {dynamodb_table_name} structure verified")
            
        except Exception as e:
            pytest.fail(f"Failed to verify table structure: {str(e)}")


# Import boto3 for DynamoDB conditions
import boto3.dynamodb.conditions
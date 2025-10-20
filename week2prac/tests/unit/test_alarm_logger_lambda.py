"""
Unit tests for alarm_logger.py Lambda function
"""
import pytest
import json
import sys
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime

# Add the lambda_alarm_logger directory to Python path
alarm_logger_dir = Path(__file__).parent.parent.parent / "week2prac" / "lambda_alarm_logger"
sys.path.insert(0, str(alarm_logger_dir))

import alarm_logger

class TestAlarmLoggerLambda:
    """Unit tests for alarm_logger Lambda function"""
    
    def test_lambda_handler_single_record(self, mock_dynamodb_resource, mock_environment_vars, 
                                         lambda_context, sample_sns_event):
        """Test lambda_handler processes single SNS record correctly"""
        
        # Call the lambda handler
        result = alarm_logger.lambda_handler(sample_sns_event, lambda_context)
        
        # Verify successful response
        assert result['status'] == 'success'
        assert result['records_logged'] == 1
        
        # Verify DynamoDB put_item was called
        assert mock_dynamodb_resource.put_item.called
        call_args = mock_dynamodb_resource.put_item.call_args
        
        # Extract the item that was written
        item = call_args[1]['Item']
        
        # Verify the item structure
        assert 'alarm_name' in item
        assert 'timestamp' in item
        assert 'new_state' in item
        assert 'reason' in item
        
        # Verify specific values from the test SNS message
        assert item['alarm_name'] == 'AvailabilityAlarm-https://www.nytimes.com'
        assert item['new_state'] == 'ALARM'
        assert 'Threshold Crossed' in item['reason']
    
    def test_lambda_handler_multiple_records(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler processes multiple SNS records"""
        
        # Create event with multiple records
        multi_record_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "TestAlarm1",
                            "NewStateValue": "ALARM",
                            "NewStateReason": "Test reason 1"
                        })
                    }
                },
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "TestAlarm2", 
                            "NewStateValue": "OK",
                            "NewStateReason": "Test reason 2"
                        })
                    }
                }
            ]
        }
        
        result = alarm_logger.lambda_handler(multi_record_event, lambda_context)
        
        # Verify response
        assert result['status'] == 'success'
        assert result['records_logged'] == 2
        
        # Verify DynamoDB was called twice
        assert mock_dynamodb_resource.put_item.call_count == 2
        
        # Verify both items were written correctly
        calls = mock_dynamodb_resource.put_item.call_args_list
        
        first_item = calls[0][1]['Item']
        assert first_item['alarm_name'] == 'TestAlarm1'
        assert first_item['new_state'] == 'ALARM'
        
        second_item = calls[1][1]['Item'] 
        assert second_item['alarm_name'] == 'TestAlarm2'
        assert second_item['new_state'] == 'OK'
    
    def test_lambda_handler_malformed_sns_message(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler handles malformed SNS messages gracefully"""
        
        # Event with invalid JSON in SNS message
        malformed_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": "invalid json {"
                    }
                }
            ]
        }
        
        # Should not raise exception
        result = alarm_logger.lambda_handler(malformed_event, lambda_context)
        
        # Should still report success (graceful handling)
        assert result['status'] == 'success'
        assert result['records_logged'] == 1
        
        # Should still write to DynamoDB with default values
        assert mock_dynamodb_resource.put_item.called
        call_args = mock_dynamodb_resource.put_item.call_args
        item = call_args[1]['Item']
        
        # Should have default values for malformed message
        assert item['alarm_name'] == 'UnknownAlarm'
        assert item['new_state'] == 'UNKNOWN'
    
    def test_lambda_handler_missing_fields(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler handles missing fields in SNS message"""
        
        # Event with minimal SNS message (missing optional fields)
        minimal_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "MinimalAlarm"
                            # Missing NewStateValue and NewStateReason
                        })
                    }
                }
            ]
        }
        
        result = alarm_logger.lambda_handler(minimal_event, lambda_context)
        
        assert result['status'] == 'success'
        assert result['records_logged'] == 1
        
        # Verify item with default values for missing fields
        call_args = mock_dynamodb_resource.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['alarm_name'] == 'MinimalAlarm'
        assert item['new_state'] == 'UNKNOWN'  # Default value
        assert item['reason'] == ''  # Default empty string
    
    def test_timestamp_generation(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test that timestamps are generated correctly"""
        
        test_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "TimestampTest",
                            "NewStateValue": "ALARM", 
                            "NewStateReason": "Test"
                        })
                    }
                }
            ]
        }
        
        # Mock datetime to control timestamp
        with patch('alarm_logger.datetime') as mock_datetime:
            fixed_time = datetime(2023, 10, 20, 10, 0, 0)
            mock_datetime.utcnow.return_value = fixed_time
            mock_datetime.utcnow().isoformat.return_value = fixed_time.isoformat()
            
            result = alarm_logger.lambda_handler(test_event, lambda_context)
        
        # Verify timestamp was set correctly
        call_args = mock_dynamodb_resource.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['timestamp'] == fixed_time.isoformat()
    
    def test_environment_variable_usage(self, mock_environment_vars, lambda_context):
        """Test that TABLE_NAME environment variable is used correctly"""
        
        # Verify the module uses the environment variable
        assert alarm_logger.TABLE_NAME == 'TestTable'
        
        # Verify DynamoDB resource uses the table name
        with patch('boto3.resource') as mock_resource:
            mock_dynamo = Mock()
            mock_table = Mock()
            mock_resource.return_value = mock_dynamo
            mock_dynamo.Table.return_value = mock_table
            
            # Import again to trigger module initialization with mocked boto3
            import importlib
            importlib.reload(alarm_logger)
            
            # Verify Table was called with correct name
            mock_dynamo.Table.assert_called_with('TestTable')
    
    def test_dynamodb_error_handling(self, mock_environment_vars, lambda_context):
        """Test lambda_handler handles DynamoDB errors gracefully"""
        
        test_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "DynamoErrorTest",
                            "NewStateValue": "ALARM",
                            "NewStateReason": "Test error handling"
                        })
                    }
                }
            ]
        }
        
        # Mock DynamoDB to raise an exception
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_table.put_item.side_effect = Exception("DynamoDB unavailable")
            mock_resource.return_value.Table.return_value = mock_table
            
            # Reload module with mocked boto3
            import importlib
            importlib.reload(alarm_logger)
            
            # Should not raise exception, even if DynamoDB fails
            try:
                result = alarm_logger.lambda_handler(test_event, lambda_context)
                # If no exception handling, this test will fail due to the exception
                # If there is proper error handling, we can verify the response
                assert 'status' in result
            except Exception as e:
                pytest.fail(f"Lambda should handle DynamoDB errors gracefully, but got: {e}")
    
    def test_empty_records_list(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler handles empty records list"""
        
        empty_event = {"Records": []}
        
        result = alarm_logger.lambda_handler(empty_event, lambda_context)
        
        assert result['status'] == 'success'
        assert result['records_logged'] == 0
        
        # Should not call DynamoDB
        assert not mock_dynamodb_resource.put_item.called
    
    def test_record_parsing_variations(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test various CloudWatch alarm message formats"""
        
        # Test different alarm state transitions
        test_cases = [
            {
                "AlarmName": "HighLatencyAlarm",
                "NewStateValue": "ALARM", 
                "NewStateReason": "Latency exceeded 2000ms",
                "OldStateValue": "OK"
            },
            {
                "AlarmName": "LowAvailabilityAlarm",
                "NewStateValue": "OK",
                "NewStateReason": "Site is back online",
                "OldStateValue": "ALARM"
            },
            {
                "AlarmName": "InsufficientDataAlarm",
                "NewStateValue": "INSUFFICIENT_DATA",
                "NewStateReason": "No recent data points"
            }
        ]
        
        for i, alarm_data in enumerate(test_cases):
            event = {
                "Records": [
                    {
                        "Sns": {
                            "Message": json.dumps(alarm_data)
                        }
                    }
                ]
            }
            
            result = alarm_logger.lambda_handler(event, lambda_context)
            
            assert result['status'] == 'success'
            assert result['records_logged'] == 1
            
            # Verify correct data was written
            call_args = mock_dynamodb_resource.put_item.call_args
            item = call_args[1]['Item']
            
            assert item['alarm_name'] == alarm_data['AlarmName']
            assert item['new_state'] == alarm_data['NewStateValue']
            assert item['reason'] == alarm_data['NewStateReason']
            
            # Reset mock for next iteration
            mock_dynamodb_resource.reset_mock()
    
    def test_parse_alarm_tags(self):
        """Test parsing tags from alarm descriptions"""
        
        # Test with tagged description
        tagged_description = "[METRIC_TYPE:availability][SEVERITY:critical][SITE:https://www.nytimes.com] Alarm for https://www.nytimes.com"
        tags = alarm_logger.parse_alarm_tags(tagged_description)
        
        assert tags['metric_type'] == 'availability'
        assert tags['severity'] == 'critical'
        assert tags['site'] == 'https://www.nytimes.com'
        
        # Test with untagged description
        untagged_description = "Simple alarm description"
        tags = alarm_logger.parse_alarm_tags(untagged_description)
        assert tags == {}
        
        # Test with partial tags
        partial_description = "[METRIC_TYPE:latency] Partial tag description"
        tags = alarm_logger.parse_alarm_tags(partial_description)
        assert tags['metric_type'] == 'latency'
        assert 'severity' not in tags
    
    def test_lambda_handler_with_tagged_alarms(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler processes tagged alarm messages correctly"""
        
        # Create event with tagged alarm description
        tagged_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "AvailabilityAlarm-Test",
                            "NewStateValue": "ALARM",
                            "NewStateReason": "Site is down",
                            "AlarmDescription": "[METRIC_TYPE:availability][SEVERITY:critical][SITE:test-site] Test alarm"
                        })
                    }
                }
            ]
        }
        
        result = alarm_logger.lambda_handler(tagged_event, lambda_context)
        
        assert result['status'] == 'success'
        assert result['records_logged'] == 1
        
        # Verify DynamoDB item includes tags
        call_args = mock_dynamodb_resource.put_item.call_args
        item = call_args[1]['Item']
        
        # Check basic fields
        assert item['alarm_name'] == 'AvailabilityAlarm-Test'
        assert item['new_state'] == 'ALARM'
        
        # Check parsed tags
        assert item['metric_type'] == 'availability'
        assert item['severity'] == 'critical'
        assert item['site'] == 'test-site'
        assert 'alarm_description' in item
        assert 'tags' in item
        
        # Verify tags JSON
        stored_tags = json.loads(item['tags'])
        assert stored_tags['metric_type'] == 'availability'
        assert stored_tags['severity'] == 'critical'
        assert stored_tags['site'] == 'test-site'
    
    def test_lambda_handler_with_untagged_alarms(self, mock_dynamodb_resource, mock_environment_vars, lambda_context):
        """Test lambda_handler handles untagged alarm messages gracefully"""
        
        # Create event with untagged alarm description
        untagged_event = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps({
                            "AlarmName": "UntaggedAlarm",
                            "NewStateValue": "ALARM", 
                            "NewStateReason": "Some issue",
                            "AlarmDescription": "Plain alarm description without tags"
                        })
                    }
                }
            ]
        }
        
        result = alarm_logger.lambda_handler(untagged_event, lambda_context)
        
        assert result['status'] == 'success'
        assert result['records_logged'] == 1
        
        # Verify DynamoDB item has default tag values
        call_args = mock_dynamodb_resource.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['alarm_name'] == 'UntaggedAlarm'
        assert 'alarm_description' in item
        
        # Should not have tag fields for untagged alarms
        assert 'metric_type' not in item
        assert 'severity' not in item
        assert 'site' not in item
        assert 'tags' not in item

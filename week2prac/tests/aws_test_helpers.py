"""
AWS helper utilities for integration tests
"""
import boto3
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .test_config import AWS_REGION, METRIC_NAMESPACE

class AWSTestHelper:
    """Helper class for AWS service interactions in tests"""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        self.cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.sns = boto3.client('sns', region_name=AWS_REGION)
        
    def invoke_lambda(self, function_name: str, payload: Dict = None) -> Dict:
        """Invoke a Lambda function and return the response"""
        if payload is None:
            payload = {}
            
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result
    
    def wait_for_metrics(self, metric_name: str, dimensions: Dict, 
                        timeout_seconds: int = 60) -> bool:
        """Wait for CloudWatch metrics to appear"""
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=METRIC_NAMESPACE,
                    MetricName=metric_name,
                    Dimensions=[{'Name': k, 'Value': v} for k, v in dimensions.items()],
                    StartTime=datetime.utcnow() - timedelta(minutes=10),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    return True
                    
            except Exception as e:
                print(f"Error checking metrics: {e}")
                
            time.sleep(5)
            
        return False
    
    def get_metric_value(self, metric_name: str, dimensions: Dict, 
                        statistic: str = 'Average') -> Optional[float]:
        """Get the latest value for a metric"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=METRIC_NAMESPACE,
                MetricName=metric_name,
                Dimensions=[{'Name': k, 'Value': v} for k, v in dimensions.items()],
                StartTime=datetime.utcnow() - timedelta(minutes=10),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=[statistic]
            )
            
            if response['Datapoints']:
                # Get the most recent datapoint
                latest = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                return latest[statistic]
                
        except Exception as e:
            print(f"Error getting metric value: {e}")
            
        return None
    
    def check_dynamo_records(self, table_name: str, 
                           key_condition: Dict = None) -> List[Dict]:
        """Check DynamoDB table for records"""
        try:
            table = self.dynamodb.Table(table_name)
            
            if key_condition:
                response = table.query(**key_condition)
            else:
                response = table.scan(Limit=10)  # Limit for safety
                
            return response.get('Items', [])
            
        except Exception as e:
            print(f"Error checking DynamoDB records: {e}")
            return []
    
    def publish_test_alarm(self, topic_arn: str, alarm_name: str) -> bool:
        """Publish a test alarm message to SNS"""
        try:
            message = {
                "AlarmName": alarm_name,
                "AlarmDescription": "Test alarm for integration testing",
                "NewStateValue": "ALARM",
                "NewStateReason": "Test triggered alarm",
                "StateChangeTime": datetime.utcnow().isoformat()
            }
            
            self.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
                Subject=f"ALARM: {alarm_name}"
            )
            return True
            
        except Exception as e:
            print(f"Error publishing test alarm: {e}")
            return False
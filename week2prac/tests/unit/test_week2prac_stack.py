import aws_cdk as core
import aws_cdk.assertions as assertions

from week2prac.week2prac_stack import Week2PracStack

class TestWeek2PracStack:
    """Unit tests for Week2PracStack CDK resources"""
    
    def test_lambda_function_created(self):
        """Test that monitor Lambda function is created with correct properties"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify Lambda function exists
        template.has_resource_properties("AWS::Lambda::Function", {
            "Runtime": "python3.12",
            "Handler": "monitor.lambda_handler",
            "Timeout": 30,
            "Environment": {
                "Variables": {
                    "METRIC_NAMESPACE": "NYTMonitor"
                }
            }
        })
    
    def test_alarm_logger_lambda_created(self):
        """Test that alarm logger Lambda function is created"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify alarm logger Lambda exists
        template.has_resource_properties("AWS::Lambda::Function", {
            "Runtime": "python3.12",
            "Handler": "alarm_logger.lambda_handler",
            "Timeout": 10
        })
    
    def test_eventbridge_rule_created(self):
        """Test that EventBridge rule is created with 5-minute schedule"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify EventBridge rule
        template.has_resource_properties("AWS::Events::Rule", {
            "ScheduleExpression": "rate(5 minutes)",
            "State": "ENABLED"
        })
    
    def test_cloudwatch_alarms_created(self):
        """Test that CloudWatch alarms are created for monitored sites"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Should have availability alarms
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "ComparisonOperator": "LessThanThreshold",
            "Threshold": 1,
            "MetricName": "Availability",
            "Namespace": "NYTMonitor"
        })
        
        # Should have latency alarms  
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "ComparisonOperator": "GreaterThanThreshold",
            "Threshold": 2000,
            "MetricName": "Latency",
            "Namespace": "NYTMonitor"
        })
    
    def test_sns_topic_created(self):
        """Test that SNS topic is created for alarm notifications"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify SNS topic exists
        template.has_resource("AWS::SNS::Topic")
        
        # Verify email subscription
        template.has_resource_properties("AWS::SNS::Subscription", {
            "Protocol": "email",
            "Endpoint": "vrishtii.padhya@gmail.com"
        })
        
        # Verify Lambda subscription
        template.has_resource_properties("AWS::SNS::Subscription", {
            "Protocol": "lambda"
        })
    
    def test_dynamodb_table_created(self):
        """Test that DynamoDB table is created for alarm logging"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify DynamoDB table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": [
                {"AttributeName": "alarm_name", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            "AttributeDefinitions": [
                {"AttributeName": "alarm_name", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"}
            ]
        })
    
    def test_cloudwatch_dashboard_created(self):
        """Test that CloudWatch dashboard is created"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify dashboard exists
        template.has_resource("AWS::CloudWatch::Dashboard")
    
    def test_iam_permissions_configured(self):
        """Test that proper IAM permissions are configured"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify Lambda execution role exists
        template.has_resource("AWS::IAM::Role")
        
        # Verify CloudWatch metrics policy
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": "cloudwatch:PutMetricData",
                        "Resource": "*",
                        "Condition": {
                            "StringEquals": {
                                "cloudwatch:namespace": "NYTMonitor"
                            }
                        }
                    }
                ])
            }
        })
    
    def test_resource_naming_with_stack_suffix(self):
        """Test that resources are named with stack suffix to avoid conflicts"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack-name")
        template = assertions.Template.from_stack(stack)
        
        # Verify SNS topic includes stack name
        template.has_resource_properties("AWS::SNS::Topic", {
            "TopicName": "WebMonitorAlarms-test-stack-name"
        })
        
        # Verify DynamoDB table includes stack name
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": "WebMonitorAlarmLogs-test-stack-name"
        })
        
        # Verify dashboard includes stack name
        template.has_resource_properties("AWS::CloudWatch::Dashboard", {
            "DashboardName": "WebHealthDashboard-test-stack-name"
        })
    
    def test_multiple_site_monitoring(self):
        """Test that alarms are created for multiple monitored sites"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Should have multiple alarms (at least 6: 2 types × 3 sites)
        alarms = template.find_resources("AWS::CloudWatch::Alarm")
        assert len(alarms) >= 6, f"Expected at least 6 alarms, found {len(alarms)}"
        
        # Should have dashboard widgets for each site
        template.has_resource("AWS::CloudWatch::Dashboard")
    
    def test_alarm_actions_configured(self):
        """Test that alarms have proper SNS actions configured"""
        app = core.App()
        stack = Week2PracStack(app, "test-stack")
        template = assertions.Template.from_stack(stack)
        
        # Verify alarms have SNS actions
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmActions": assertions.Match.array_with([
                assertions.Match.any_value()  # SNS topic ARN
            ])
        })

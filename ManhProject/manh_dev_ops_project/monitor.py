from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class MonitorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -------DynamoDB Database Service------------
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        # Create table for website configurations
        self.web_table = dynamodb.TableV2(
            self, "Website_Table",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create table for alarm history
        self.alarm_history_table = dynamodb.TableV2(
            self, "AlarmHistory",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="website",
                type=dynamodb.AttributeType.STRING
            )
        )

        # ------------SNS Topic for alarms service------------
        # Create SNS topic for alarm notifications
        # Name as "WebMonitorAlarmTopic"
        # Add a default email subscription - for more emails can be added through AWS Console or manually add here as well
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        self.alarm_topic = sns.Topic(self, "WebAlarmTopic")
        self.alarm_topic.add_subscription(subscriptions.EmailSubscription("long.nm187254@gmail.com"))

        # ------------ Build Lambda Function Service -----------
        # Build Lambda function for website availability and latency monitoring
        # Name as "WebsiteMonitorFunction"
        # Set environment variables for DynamoDB table names
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        self.monitor_lambda = _lambda.Function(
            self, "WebsiteMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("modules/monitor"),
            handler="monitor.lambda_handler",
            environment={
                "WEBSITES_TABLE": self.web_table.table_name,
                "ALARM_SNS_TOPIC_ARN": self.alarm_topic.topic_arn
            }
        )

        # Build Lambda function to handle SNS alarm notifications and write to DynamoDB
        # Name as "AlarmHandler"
        # Set environment variable for DynamoDB alarm history table name
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        alarm_handler = _lambda.Function(
            self, "AlarmHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="alarm_handler.lambda_handler",
            code=_lambda.Code.from_asset("modules/alarm"),
            environment={
                'ALARM_HISTORY_TABLE': self.alarm_history_table.table_name
            }
        )

        # Subscribe the Lambda to the SNS topic
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/LambdaSubscription.html
        self.alarm_topic.add_subscription(subscriptions.LambdaSubscription(alarm_handler))
        # Grant the Lambda write permissions to the DynamoDB table
        self.alarm_history_table.grant_write_data(alarm_handler)

        # Grant permissions for CloudWatch metrics and alarms
        self.monitor_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "cloudwatch:PutMetricData",
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DescribeAlarms"
            ],
            resources=["*"]
        ))

        # ------------ CloudWatch Dashboard Service -----------
        # Create CloudWatch dashboard to visualize website monitoring metrics
        # Name as "WebMonitoringDashboard"
        # Add widgets for website monitoring metrics
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        self.dashboard = cloudwatch.Dashboard(
            self, "WebMonitoringDashboard",
            dashboard_name="WebsiteMonitoringDashboard"
        )

        # Add widgets to dashboard
        self.dashboard.add_widgets(
            # Website Availability Overview
            cloudwatch.GraphWidget(
                title="Website Availability",
                left=[
                    cloudwatch.Metric(
                        namespace="WebsiteMonitoring",
                        metric_name="Availability",
                        statistic="Average",
                        dimensions_map={"WebsiteName": "*"},
                        period=Duration.minutes(5)
                    )
                ],
                width=12,
                height=6
            ),
            # Website Latency Overview
            cloudwatch.GraphWidget(
                title="Website Latency (ms)",
                left=[
                    cloudwatch.Metric(
                        namespace="WebsiteMonitoring",
                        metric_name="Latency",
                        statistic="Average",
                        dimensions_map={"WebsiteName": "*"},
                        period=Duration.minutes(5)
                    )
                ],
                width=12,
                height=6
            ),
            # Website Status Codes
            cloudwatch.GraphWidget(
                title="Website Status Codes",
                left=[
                    cloudwatch.Metric(
                        namespace="WebsiteMonitoring",
                        metric_name="StatusCode",
                        statistic="Maximum",
                        dimensions_map={"WebsiteName": "*"},
                        period=Duration.minutes(5)
                    )
                ],
                width=12,
                height=6
            )
        )

        # ------------ CloudWatch Alarms for Website Monitoring -----------
        # Create alarm when website is not available (availability = 0)
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
        availability_alarm = cloudwatch.Alarm(
            self, "WebsiteAvailabilityAlarm",
            alarm_name="WebsiteAvailabilityAlarm",
            alarm_description="Alert when website is not available (availability = 0)",
            metric=cloudwatch.Metric(
                namespace="WebsiteMonitoring",
                metric_name="Availability",
                statistic="Minimum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1
        )
        availability_alarm.add_alarm_action(cloudwatch_actions.SnsAction(self.alarm_topic))

        # Create alarm when latency is greater than 400ms
        latency_alarm = cloudwatch.Alarm(
            self, "WebsiteLatencyAlarm",
            alarm_name="WebsiteLatencyAlarm",
            alarm_description="Alert when website latency exceeds 400ms",
            metric=cloudwatch.Metric(
                namespace="WebsiteMonitoring",
                metric_name="Latency",
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=400,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1
        )
        latency_alarm.add_alarm_action(cloudwatch_actions.SnsAction(self.alarm_topic))


  
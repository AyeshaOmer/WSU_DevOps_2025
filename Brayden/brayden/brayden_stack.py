from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch_,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct

class BraydenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create a log group for the Lambda function with a removal policy.
        log_group = logs.LogGroup(self, "WanMONLambdaLogGroup",
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create the Lambda function.
        fn = lambda_.Function(self, "WanMONLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="WanMONLambda.lambda_handler",    
            code=lambda_.Code.from_asset("./modules"),
            log_group=log_group
        )
        
        # ADDED: Add a policy to the Lambda function's IAM role to allow it to push metrics to CloudWatch.
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"] 
        ))

    # Triger lamda every 5 min
        rule = events.Rule(self, "WanMONLambdaSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )

    # Target the lamdba function for the rule
        rule.add_target(targets.LambdaFunction(fn))

    # Availability Alarm: Triggers if the website returns a status code other than 200.
        availability_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="Availability",
            dimensions_map={"URL": "https://www.google.com"}
        )
        
        availability_alarm = cloudwatch_.Alarm(self, "AvailabilityAlarm",
            metric=availability_metric,
            threshold=1,
            comparison_operator=cloudwatch_.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when website availability is down (value is 0)."
        )

    # Latency Alarm: Triggers if the website response latency is over 30ms.
        latency_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="Latency",
            dimensions_map={"URL": "https://www.google.com"}
        )

        latency_alarm = cloudwatch_.Alarm(self, "LatencyAlarm",
            metric=latency_metric,
            threshold=200,
            comparison_operator=cloudwatch_.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when website latency is above 100ms."
        )

    # SSL Certificate Expiry Alarm: Triggers if the SSL certificate has 5 or fewer days remaining.
    # This assumes the metric from the Lambda is the number of remaining days.
        ssl_expiry_metric = cloudwatch_.Metric(
            namespace="WebsiteMonitor",
            metric_name="SSLCertificateExpiryDays",
            dimensions_map={"URL": "www.google.com"}
        )
        
        ssl_expiry_alarm = cloudwatch_.Alarm(self, "SSLExpiryAlarm",
            metric=ssl_expiry_metric,
            threshold=5,
            comparison_operator=cloudwatch_.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
            evaluation_periods=1,
            alarm_description="Alarm when SSL certificate has 5 or fewer days remaining."
        )

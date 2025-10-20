from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cw,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
)
from constructs import Construct
from pathlib import Path
import json

def create_alarm_description(metric_type: str, site: str, severity: str = "warning"):
    """Create alarm description with embedded tags for filtering"""
    return f"[METRIC_TYPE:{metric_type}][SEVERITY:{severity}][SITE:{site}] Alarm for {site}"

class Week2PracStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        METRIC_NAMESPACE = "NYTMonitor"

        base_dir = Path(__file__).resolve().parent
        lambda_dir = str(base_dir / "lambda")
        alarm_logger_dir = str(base_dir / "lambda_alarm_logger")
        sites_file = base_dir / "lambda" / "sites.json"

        # Per-stage suffix to avoid name collisions across Beta/Gamma/Prod (and old stacks)
        suffix = self.stack_name  # e.g., "Beta-WebHealthStack"

        # Sites DynamoDB Table for CRUD API (created early so monitor can reference it)
        sites_table = dynamodb.Table(
            self,
            "SitesTable",
            table_name=f"Sites-{suffix}",
            partition_key=dynamodb.Attribute(name="site_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_class=dynamodb.TableClass.STANDARD,
        )
        sites_table.apply_removal_policy(RemovalPolicy.DESTROY)

        monitor_fn = lambda_.Function(
            self,
            "MonitorNYT",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="monitor.lambda_handler",
            code=lambda_.Code.from_asset(lambda_dir),
            timeout=Duration.seconds(30),
            environment={
                "METRIC_NAMESPACE": METRIC_NAMESPACE,
                "SITES_TABLE_NAME": sites_table.table_name
            },
        )

        monitor_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": METRIC_NAMESPACE}},
            )
        )
        
        # Grant DynamoDB read access to monitor Lambda
        sites_table.grant_read_data(monitor_fn)

        events.Rule(
            self,
            "MonitorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(monitor_fn)],
        )

        with sites_file.open("r", encoding="utf-8") as f:
            sites = json.load(f)

        dashboard = cw.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name=f"WebHealthDashboard-{self.stack_name}",
        )

        widgets: list[cw.IWidget] = []

        # --- Make names unique per stage ---
        alarm_topic = sns.Topic(
            self,
            "WebMonitorAlarmTopic",
            topic_name=f"WebMonitorAlarms-{suffix}",
        )
        alarm_topic.add_subscription(subs.EmailSubscription("vrishtii.padhya@gmail.com"))

        alarm_log_table = dynamodb.Table(
            self,
            "AlarmLogTable",
            table_name=f"WebMonitorAlarmLogs-{suffix}",
            partition_key=dynamodb.Attribute(name="alarm_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_class=dynamodb.TableClass.STANDARD,
        )
        alarm_log_table.apply_removal_policy(RemovalPolicy.DESTROY)

        log_lambda = lambda_.Function(
            self,
            "AlarmLoggerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=lambda_.Code.from_asset(alarm_logger_dir),
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": alarm_log_table.table_name},
        )
        alarm_log_table.grant_write_data(log_lambda)
        alarm_topic.add_subscription(subs.LambdaSubscription(log_lambda))

        # CRUD Lambda Function
        crud_api_dir = str(base_dir / "crud_api")
        sites_crud_lambda = lambda_.Function(
            self,
            "SitesCrudLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="sites_crud.lambda_handler",
            code=lambda_.Code.from_asset(crud_api_dir),
            timeout=Duration.seconds(60),  # Increased for CloudWatch operations
            environment={
                "SITES_TABLE_NAME": sites_table.table_name,
                "METRIC_NAMESPACE": METRIC_NAMESPACE,
                "SNS_TOPIC_ARN": alarm_topic.topic_arn,
                "DASHBOARD_NAME": f"WebHealthDashboard-{self.stack_name}"
            },
        )
        
        # Grant DynamoDB permissions to CRUD Lambda
        sites_table.grant_read_write_data(sites_crud_lambda)
        
        # Grant CloudWatch permissions to CRUD Lambda for dynamic alarm/dashboard management
        sites_crud_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricAlarm",
                    "cloudwatch:DeleteAlarms",
                    "cloudwatch:DescribeAlarms",
                    "cloudwatch:PutDashboard",
                    "cloudwatch:GetDashboard",
                    "cloudwatch:ListDashboards"
                ],
                resources=["*"]
            )
        )

        # API Gateway REST API
        sites_api = apigateway.RestApi(
            self,
            "SitesApi",
            rest_api_name=f"Sites-API-{suffix}",
            description="CRUD API for managing website monitoring targets",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )

        # API Gateway Integration
        sites_integration = apigateway.LambdaIntegration(sites_crud_lambda)

        # /sites resource for list and create operations
        sites_resource = sites_api.root.add_resource("sites")
        sites_resource.add_method("GET", sites_integration)  # List all sites
        sites_resource.add_method("POST", sites_integration)  # Create site

        # /sites/{site_id} resource for individual site operations
        site_resource = sites_resource.add_resource("{site_id}")
        site_resource.add_method("GET", sites_integration)  # Get single site
        site_resource.add_method("PUT", sites_integration)  # Update site
        site_resource.add_method("DELETE", sites_integration)  # Delete site

        for site in sites:
            avail_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Availability",
                dimensions_map={"Site": site},
                statistic="Average",
                period=Duration.minutes(5),
                label=f"{site} Availability",
            )
            latency_metric = cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="Latency",
                dimensions_map={"Site": site},
                statistic="p95",
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,
                label=f"{site} Latency (p95 ms)",
            )

            widgets.append(cw.GraphWidget(title=f"Availability - {site}", left=[avail_metric], width=12, height=6))
            widgets.append(cw.GraphWidget(title=f"Latency (p95 ms) - {site}", left=[latency_metric], width=12, height=6))

            availability_alarm = cw.Alarm(
                self,
                f"AvailabilityAlarm-{site}",
                metric=avail_metric,
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=create_alarm_description("availability", site, "critical"),
            )
            availability_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

            latency_alarm = cw.Alarm(
                self,
                f"LatencyAlarm-{site}",
                metric=latency_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=create_alarm_description("latency", site, "warning"),
            )
            latency_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Operational health alarms for the crawler itself
        crawler_execution_time_alarm = cw.Alarm(
            self,
            f"CrawlerExecutionTimeAlarm",
            metric=cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="CrawlerExecutionTime",
                dimensions_map={"Function": "WebCrawler"},
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=30000,  # 30 seconds
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description=create_alarm_description("operational", "WebCrawler", "warning"),
        )
        crawler_execution_time_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        crawler_memory_alarm = cw.Alarm(
            self,
            f"CrawlerMemoryUsageAlarm",
            metric=cw.Metric(
                namespace=METRIC_NAMESPACE,
                metric_name="CrawlerMemoryUsage",
                dimensions_map={"Function": "WebCrawler"},
                statistic="Maximum",
                period=Duration.minutes(5)
            ),
            threshold=100,  # 100 MB
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description=create_alarm_description("operational", "WebCrawler", "critical"),
        )
        crawler_memory_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Add operational metrics to dashboard
        operational_widgets = [
            cw.GraphWidget(
                title="Crawler Execution Time",
                left=[cw.Metric(
                    namespace=METRIC_NAMESPACE,
                    metric_name="CrawlerExecutionTime",
                    dimensions_map={"Function": "WebCrawler"},
                    statistic="Average",
                    period=Duration.minutes(5),
                    label="Execution Time (ms)"
                )],
                width=12,
                height=6
            ),
            cw.GraphWidget(
                title="Crawler Memory Usage",
                left=[cw.Metric(
                    namespace=METRIC_NAMESPACE,
                    metric_name="CrawlerMemoryUsage",
                    dimensions_map={"Function": "WebCrawler"},
                    statistic="Maximum",
                    period=Duration.minutes(5),
                    label="Memory Usage (MB)"
                )],
                width=12,
                height=6
            )
        ]
        
        # Add operational widgets to dashboard
        widgets.extend(operational_widgets)

        dashboard.add_widgets(*widgets)
        
        # CDK Outputs for integration testing
        CfnOutput(
            self,
            "SitesApiUrl",
            value=sites_api.url,
            description="Sites CRUD API Gateway URL",
            export_name=f"SitesApiUrl-{suffix}"
        )
        
        CfnOutput(
            self,
            "SitesTableName", 
            value=sites_table.table_name,
            description="Sites DynamoDB table name",
            export_name=f"SitesTableName-{suffix}"
        )

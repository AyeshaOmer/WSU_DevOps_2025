import os
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_apigateway as apigw,
    custom_resources as cr,
)
from constructs import Construct
from gursh import constants as C


class GurshStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        # DynamoDB tables
        
        urls_table = dynamodb.TableV2(
            self,
            "UrlsTable",
            partition_key=dynamodb.Attribute(name="url", type=dynamodb.AttributeType.STRING),
            table_name=f"{C.NAMESPACE}-Urls",
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=False,
        )

        mrsc_table = dynamodb.TableV2(
            self,
            "MRSCTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            table_name=f"{C.NAMESPACE}-MRSCTable",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Seed URLs ONCE from constants (simple, on-create only)
        seed_urls = cr.AwsCustomResource(
            self,
            "SeedUrlsOnce",
            on_create=cr.AwsSdkCall(
                service="DynamoDB",
                action="batchWriteItem",
                parameters={
                    "RequestItems": {
                        urls_table.table_name: [
                            {"PutRequest": {"Item": {"url": {"S": u}}}} for u in C.URLS
                        ]
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of("SeedUrlsOnce"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=["dynamodb:BatchWriteItem"],
                        resources=[urls_table.table_arn],
                    )
                ]
            ),
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        seed_urls.node.add_dependency(urls_table)

        
        # Lambdas
       
        # WebHealth crawler (Project 1)
        webhealth_fn = lambda_.Function(
            self,
            "WebHealthLAMBDA",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="WHLambda.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "modules")),
            timeout=Duration.minutes(10),
            memory_size=512,
            environment={
                "URL_NAMESPACE": C.NAMESPACE,
                "DIMENSION_NAME": C.DIMENSION_NAME,
                "URLS_TABLE_NAME": urls_table.table_name,   # read list from table
                "TABLE_NAME": mrsc_table.table_name,        # write run results
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        # allow custom metrics
        webhealth_fn.add_to_role_policy(
            iam.PolicyStatement(actions=["cloudwatch:PutMetricData"], resources=["*"])
        )

        # DB logging for alarms (Project 1)
        db_fn = lambda_.Function(
            self,
            "DBLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="DBLambda.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "modules")),
            timeout=Duration.minutes(5),
            environment={
                "URL_NAMESPACE": C.NAMESPACE,
                "TABLE_NAME": mrsc_table.table_name,
                "DIMENSION_NAME": C.DIMENSION_NAME,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # CRUD Lambda (Project 2)
        crud_fn = lambda_.Function(
            self,
            "CrudLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="APIgateway.lambda_handler",  # file: modules/APIgateway.py
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), "modules")),
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={"TABLE_NAME": urls_table.table_name},
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Permissions
        urls_table.grant_read_data(webhealth_fn)
        mrsc_table.grant_read_write_data(webhealth_fn)
        mrsc_table.grant_read_write_data(db_fn)
        urls_table.grant_read_write_data(crud_fn)

        
        # EventBridge schedule (every 5 minutes)
        # 
        events.Rule(
            self,
            "WHInvokeRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(webhealth_fn)],
            description="Run WebHealth every 5 minutes.",
        )

        
        # SNS topic + subscriptions (email + DB lambda)
        
        topic = sns.Topic(self, "AlertsTopic")
        topic.add_subscription(subs.EmailSubscription("22115841@student.westernsydney.edu.au"))
        topic.add_subscription(subs.LambdaSubscription(db_fn))

        
        # Per-URL metrics + alarms (Project 1)
      
        def url_latency_metric(url: str) -> cw.Metric:
            return cw.Metric(
                namespace=C.NAMESPACE,
                metric_name="URL_MONITOR_LATENCY",
                dimensions_map={C.DIMENSION_NAME: url},
                period=Duration.minutes(5),
                unit=cw.Unit.MILLISECONDS,
                label=f"Latency (ms) – {url}",
                statistic="Average",
            )

        def url_availability_metric(url: str) -> cw.Metric:
            return cw.Metric(
                namespace=C.NAMESPACE,
                metric_name="URL_MONITOR_AVAILABILITY",
                dimensions_map={C.DIMENSION_NAME: url},
                period=Duration.minutes(5),
                label=f"Availability – {url}",
                statistic="Average",
            )

        for i, url in enumerate(C.URLS, start=1):
            # Latency alarm
            cw.Alarm(
                self,
                f"LatencyHigh{i}",
                metric=url_latency_metric(url),
                threshold=550,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Latency > 550 ms ({url})",
            ).add_alarm_action(cw_actions.SnsAction(topic))

            # Availability alarm
            cw.Alarm(
                self,
                f"AvailabilityLow{i}",
                metric=url_availability_metric(url),
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                treat_missing_data=cw.TreatMissingData.BREACHING,
                alarm_description=f"Availability < 1 over last 5 minutes ({url})",
            ).add_alarm_action(cw_actions.SnsAction(topic))

        
        # Dashboard (one widget per URL)
        
        dashboard = cw.Dashboard(self, "Dash", default_interval=Duration.days(7))
        for url in C.URLS:
            dashboard.add_widgets(
                cw.GraphWidget(
                    title=f"URL Health – {url}",
                    left=[url_latency_metric(url)],
                    right=[url_availability_metric(url)],
                    left_y_axis=cw.YAxisProps(label="Latency (ms)", show_units=True),
                    right_y_axis=cw.YAxisProps(label="Availability (0–1)", show_units=True),
                )
            )
        dashboard.add_widgets(
            cw.LogQueryWidget(
                title="WebHealth Logs",
                log_group_names=[f"/aws/lambda/{webhealth_fn.function_name}"],
                query_lines=["fields @message"],
            )
        )

       
        # API Gateway (Project 2)
      
        api = apigw.RestApi(
            self,
            "TargetsApi",
            rest_api_name=f"{C.NAMESPACE}-TargetsApi",
            deploy_options=apigw.StageOptions(stage_name="prod", metrics_enabled=True),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            ),
        )

        urls_res = api.root.add_resource("urls")
        urls_res.add_method("POST",   apigw.LambdaIntegration(crud_fn))
        urls_res.add_method("GET",    apigw.LambdaIntegration(crud_fn))
        urls_res.add_method("PUT",    apigw.LambdaIntegration(crud_fn))
        urls_res.add_method("DELETE", apigw.LambdaIntegration(crud_fn))

        CfnOutput(self, "TargetsApiUrl", value=api.url)


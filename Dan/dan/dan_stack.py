
"This file is for deploy and call built in services/components in lambda"

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    Duration,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions,
    SecretValue,
)
from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline_actions as cp_actions
from constructs import Construct

websites = [
        {"name": "Google", "url": "https://www.google.com"},
        {"name": "Facebook", "url": "https://www.facebook.com"},
        {"name": "YouTube", "url": "https://www.youtube.com"}
    ]

metrix = ["latency", "availability", "status_code"]

THRESHOLD_METRICS = {
    "latency": 100,
    "availability": 1,
    "status_code": 200
}

class DanStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Add trigger interval time
        self.trigger_interval = Duration.minutes(5)

        # Handle Lambda function with calculation
        web_crawler_lambda = _lambda.Function(
            self, "WebCrawlerFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="Metrix.lambda_handler",
            code=_lambda.Code.from_asset("./modules"),
            timeout=Duration.minutes(5),
            memory_size=256
        )

        # Create EventBridge rule and add Lambda as target (runs every trigger_interval)
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.rate(self.trigger_interval),
        )
        rule.add_target(targets.LambdaFunction(web_crawler_lambda))

        # Add permissions for CloudWatch
        web_crawler_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"]
            )
        )

        # Creating the CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(self, "Dash",
            default_interval=Duration.days(7),
            dashboard_name="WebTestDashboard",
            variables=[cloudwatch.DashboardVariable(
                id="region2",
                type=cloudwatch.VariableType.PATTERN,
                label="Sydney",
                input_type=cloudwatch.VariableInputType.INPUT,
                value="ap-southeast-2",
                default_value=cloudwatch.DefaultValue.value("ap-southeast-2"),
                visible=True
            )]
        )

        # Creating topics and subscriptions
        topic = sns.Topic(self, "WebTestTopic")
        topic.add_subscription(subs.EmailSubscription("long.nm187254@gmail.com"))

        # Create a DynamoDB table to store alarms
        alarm_table = dynamodb.Table(
            self, "AlarmTable",
            partition_key=dynamodb.Attribute(name="AlarmId", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create a Lambda function to handle SNS alarm notifications and write to DynamoDB
        alarm_handler = _lambda.Function(
            self, "AlarmHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="alarm_handler.lambda_handler",
            code=_lambda.Code.from_asset("./modules"),
            timeout=Duration.minutes(1),
            memory_size=128,
            environment={
                'ALARM_TABLE_NAME': alarm_table.table_name
            }
        )

        # Subscribe the Lambda to the SNS topic
        topic.add_subscription(subs.LambdaSubscription(alarm_handler))

        # Grant the Lambda write permissions to the DynamoDB table
        alarm_table.grant_write_data(alarm_handler)

        for site in websites:
            # Add metrix for website and alarm
            latency_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="Latency",
                dimensions_map={"Website": site["name"], "URL": site["url"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            availability_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="Availability",
                dimensions_map={"Website": site["name"], "URL": site["url"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            status_code_metrix = cloudwatch.Metric(
                namespace="WebTest",
                metric_name="StatusCode",
                dimensions_map={"Website": site["name"], "URL": site["url"]},
                statistic="avg",
                period=Duration.minutes(5)
            )
            # This is alarm for Latency
            # Latency "not equal to expected" is implemented as two alarms:
            # one for latency > expected and one for latency < expected.
            cloudwatch.Alarm(
                self, f"{site['name']}LatencyAlarm",
                metric=latency_metrix,
                threshold=THRESHOLD_METRICS["latency"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            ).add_alarm_action(cw_actions.SnsAction(topic))
            # These are alarms for availability.
            # Availability "not equal to expected" is implemented as two alarms:
            # one for availability > expected and one for availability < expected.
            cloudwatch.Alarm(
                self, f"{site['name']}AvailabilityAlarm",
                metric=availability_metrix,
                threshold=THRESHOLD_METRICS["availability"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
            ).add_alarm_action(cw_actions.SnsAction(topic))
            # These are alarms for status code.
            # Status code "not equal to expected" is implemented as two alarms:
            # one for status > expected and one for status < expected.
            cloudwatch.Alarm(
                self, f"{site['name']}StatusCodeHighAlarm",
                metric=status_code_metrix,
                threshold=THRESHOLD_METRICS["status_code"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            ).add_alarm_action(cw_actions.SnsAction(topic))
            cloudwatch.Alarm(
                self, f"{site['name']}StatusCodeLowAlarm",
                metric=status_code_metrix,
                threshold=THRESHOLD_METRICS["status_code"],
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
            ).add_alarm_action(cw_actions.SnsAction(topic))
            # This for cloudwatch dashboard
            # Add a graph widget for each site's metrics
            dashboard.add_widgets(
                cloudwatch.GraphWidget(
                    title=f"{site['name']} Metrics",
                    left=[latency_metrix],
                    right=[availability_metrix, status_code_metrix],
                    width=12,
                    height=6
                )
            )
            # Add alarm actions to notify via SNS topic
            
        # Create the CI/CD Pipeline
        pipeline = codepipeline.Pipeline(self, "DanPipeline")

        # Source Stage
        source_output = codepipeline.Artifact()
        source_action = cp_actions.GitHubSourceAction(
            action_name="DevOps_Test",
            owner="DannisNguyen12", 
            repo="https://github.com/DannisNguyen12/DevOps_Pineline.git",
            branch="main",
            oauth_token=SecretValue.secrets_manager("github-token", json_field="oauth_token"),  # Store token in Secrets Manager
            output=source_output
        )
        pipeline.add_stage(stage_name="Source", actions=[source_action])

        # Build Stage with Lambda compute
        build_project = codebuild.PipelineProject(
            self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml")
        )
        build_output = codepipeline.Artifact()
        build_action = cp_actions.CodeBuildAction(
            action_name="Build",
            project=build_project,
            input=source_output,
            outputs=[build_output]
        )
        pipeline.add_stage(stage_name="Build", actions=[build_action])

        # Deploy Stage
        deploy_action = cp_actions.CloudFormationCreateUpdateStackAction(
            action_name="Deploy",
            template_path=build_output.at_path("cdk.out/DanStack.template.json"),
            stack_name="DanStack",
            admin_permissions=True
        )
        pipeline.add_stage(stage_name="Deploy", actions=[deploy_action])
            
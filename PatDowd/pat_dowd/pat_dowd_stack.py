from aws_cdk import (
    Stack,
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_cloudwatch as cw,
    aws_iam as iam,


)
from constructs import Construct

class PatDowdStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

       
        fn = _lambda.Function(
            self,
            "WebHelperFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="WebHealthLambda.lambda_handler",
            code=_lambda.Code.from_asset("modules"),
            timeout=Duration.seconds(30),
        )
        #cadence definition
        
        rule = events.Rule(
            self, "EveryMinuteRule", schedule=events.Schedule.rate(Duration.minutes(1))
        )
        rule.add_target(targets.LambdaFunction(fn))

        #role definitons
        fn.add_to_role_policy(
            aws_iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"], resources=["*"]
            )
        )

        #dashboard
        dashboard = cw.Dashboard(self, "Dash",
            default_interval=Duration.days(7),
            variables=[cw.DashboardVariable(
                id="board1",
                type=cw.VariableType.PATTERN,
                label="Web Health",
                input_type=cw.VariableInputType.INPUT,
                value="us-east-1",
                default_value=cw.DefaultValue.value("us-east-1"),
                visible=True
            )]
        )

        # create widgets
        for url in ["www.google.com", "www.youtube.com", "www.coolmathgames.com"]:
            availability_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="Availability",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1)
            )

            latency_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="Latency",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1)
            )

            size_metric = cw.Metric(
                namespace="WebHelperDashboard",
                metric_name="ResponseSize",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(1)
            )
        dashboard.add_widgets(
            cw.GraphWidget(
                title=f"{url} Health",
                left=[availability_metric, latency_metric, size_metric]
            )
        )



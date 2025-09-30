from aws_cdk import (
    Duration,
    Stack,
    aws_iam,
    aws_lambda as lambda_,
    RemovalPolicy,   
    aws_iam as iam,   
    aws_events as events_, 
    aws_events_targets as targets_,
    aws_cloudwatch as cloudwatch_,
    aws_cloudwatch_actions as cw_actions,
    aws_dynamodb as db_,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions
)
from constructs import Construct
from modules import constants as constants 

class AshStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # hw_lambda = self.create_lambda('FirstHWLambda', './resources', 'HWLambda.lambda_handler')
        # hw_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

        # Creating lambda roles
        WHlambda_role = self.create_lambda_role()
        DBlambda_role = self.create_dblambda_role()

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html        
        wh_lambda = self.create_lambda('ASH_WebHealthLambda', './modules', 'WHLambda.lambda_handler',WHlambda_role)
        wh_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

        DB_lambda = self.create_lambda('ASH_DynamoDBLambda', './modules', 'DBLambda.lambda_handler',DBlambda_role)
        DB_lambda.apply_removal_policy(RemovalPolicy.DESTROY)


        # Creating dynamoDB table
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_dynamodb/Table.html
        table = self.create_table()
        table.grant_full_access(DB_lambda)
        tableName = table.table_name

        # stroing tablename in environment variable so that we can access this table in DBApp.py to populate 
        DB_lambda.add_environment('tableName', tableName)
               
        # Schedule for scheduled event rules.
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_events/Schedule.html
        lambda_schedule = events_.Schedule.rate(Duration.minutes(1))
        
        # create the event target
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_events_targets/LambdaFunction.html
        lambda_target = targets_.LambdaFunction(handler=wh_lambda)
        
        # Lastly we bind it all together in an aws_events.Rule
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_events/Rule.html
        rule = events_.Rule(self, "webHealth_Invocation_Rule", description="Periodic Lambda", enabled=True, schedule=lambda_schedule, targets=[lambda_target])
        rule.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        topic = sns.Topic(self, "AlarmNotification")

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html
        topic.add_subscription(subscriptions.EmailSubscription('ayesha@skipq.org'))

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/LambdaSubscription.html
        topic.add_subscription(subscriptions.LambdaSubscription(DB_lambda))

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
        dim={'url':constants.URL_TO_MONITOR}     # donot need to define dim here. If you done, Metric will just use the same you defined in the lambda.
        availability_metric=cloudWatch_metric = cloudwatch_.Metric(
            namespace=constants.URL_MONITOR_NAMESPACE, 
            metric_name=constants.URL_MONITOR_METRIC_NAME_AVAILABILITY,
            dimensions_map=dim,
            label='Availability Metric',
            period=Duration.minutes(1)
            )
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
        availability_alarm = cloudwatch_.Alarm(self,
            id='alarm_on_availability',
            metric=availability_metric,
            comparison_operator=cloudwatch_.ComparisonOperator.LESS_THAN_THRESHOLD,
            datapoints_to_alarm=1,
            threshold=1,
            evaluation_periods=1,
            # treat_missing_data = cloudwatch_.TreatMissingData.BREACHING            
        )
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
        dim={'url':constants.URL_TO_MONITOR}
        latency_metric=cloudWatch_metric =  cloudwatch_.Metric(namespace=constants.URL_MONITOR_NAMESPACE, 
            metric_name=constants.URL_MONITOR_METRIC_NAME_LATENCY,
            dimensions_map=dim,
            label='Latency Metric',
            period=Duration.minutes(1)
            )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
        latency_alarm = cloudwatch_.Alarm(self,
            id='alarm_on_latency',
            metric=latency_metric,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch_.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold=0.31,
            evaluation_periods=1,
            # treat_missing_data = cloudwatch_.TreatMissingData.BREACHING
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GaugeWidget.html
        graph_widget = cloudwatch_.GraphWidget(
            title="Metrics for SkipQ.org",
            left=[availability_metric, latency_metric],
            width=24,
            height=6,
            legend_position=cloudwatch_.LegendPosition.RIGHT,
            left_y_axis=cloudwatch_.YAxisProps(label='MetricValues',min=0,show_units=False),   
             right_y_axis=cloudwatch_.YAxisProps(label='Time', min=0, show_units=False),   
            # vertical_annotations= [cloudwatch_.VerticalAnnotation(
            #     date="2025-08-25T12:00:00",  # ISO 8601 date-time string
            #     label="Time",                
            #     )
            # ],
            period = Duration.minutes(1)
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        dashboard = cloudwatch_.Dashboard(
            self,
            "URLMonitorDashboard",
            dashboard_name="URLMonitorDashboard"
        )
        dashboard.add_widgets(graph_widget)



    def create_lambda_role(self):
        """
        Returns the role for whLambda
        Args:
        """
        lambdaRole = aws_iam.Role(self, "lambda-role", 
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'), 
            managed_policies=[
                                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                                aws_iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchFullAccess')
                            ])
        return lambdaRole

    def create_lambda(self, id, asset, handler, role):
        """
        Returns the lambda function
        Args:
            id (str): id for the lambda function
            asset (str): asset folder where the python file is located
            handler (str): lambda handler function name in the python file.
            lambda_role (aws_iam.Role): describing role and adding policies
        """
        return lambda_.Function(self, id,
        code = lambda_.Code.from_asset(asset),
        handler = handler,
        runtime = lambda_.Runtime.PYTHON_3_12,
        role=role
        )
    
    # Creating role for DynanamoDB lambda function to have full access of AWS DynamoDB
    def create_dblambda_role(self):
        """
        Returns the role dblambda
        Args:
        """
        lambdaRole = aws_iam.Role(self, "dblambda-role",
            assumed_by = aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies = [
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
            ])
        return lambdaRole

    
    # Creating dynamodb table that will store notification data
    def create_table(self):
        """
        Returns the AWS DynamoDB table
        Args:
            id (str): id for the lambda function
            asset (str): asset folder where the python file is located
            handler (str): lambda handler function name in the python file.
            lambda_role (aws_iam.Role): describing role and adding policies
        """
        table = db_.Table(self, "NotificationTable",
            partition_key=db_.Attribute(name="id", type=db_.AttributeType.STRING),
            removal_policy = RemovalPolicy.DESTROY,
            # sort_key 
        )
        return table
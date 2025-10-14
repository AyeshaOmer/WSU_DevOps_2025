from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_synthetics as synthetics,
    aws_lambda as lambda_,
    aws_events as events_,
    aws_events_targets as targets,
    # lamba_. or import removal policy. one of the two
    aws_logs as logs,
    RemovalPolicy,

    Duration,
    aws_iam as iam,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_sns_subscriptions as sns_subscriptions,

    aws_cloudwatch as cloudwatch,
    aws_codedeploy as codedeploy,
)
from constructs import Construct
from modules import constants
from aws_cdk.aws_cloudwatch_actions import SnsAction


class EugeneStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        memory_size_mb = 512
        # function to run WHLambda file
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function-timeout
        fn = lambda_.Function(self, "WHLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(10),
            handler="WHLambda.lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
            memory_size=memory_size_mb,
        )
        fn.apply_removal_policy(RemovalPolicy.DESTROY)

        db_lambda = lambda_.Function(self, "DBLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(5),
            handler="DBLambda.db_lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
        )
        db_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        alarm_table = dynamodb.TableV2(self, "AlarmTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
        )
        alarm_table.apply_removal_policy(RemovalPolicy.DESTROY)
        alarm_table.grant_write_data(db_lambda)

        db_lambda.add_environment("TABLE_NAME", alarm_table.table_name)
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html
        schedule = events_.Schedule.rate(Duration.minutes(1)) # 1 for testing, 30 for normal
        target = targets.LambdaFunction(fn)
        rule = events_.Rule(self, "Rule",
            schedule=schedule,
            targets=[target],
            description="This rule triggers the WHLambda function every 30 minutes."
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "cloudwatch:PutMetricData",
                "dynamodb:*"
                ],
            resources=["*"],
        ))
        # Have not tested this properly until pipeline issue is fixed
        # Metrics before deploying application
        WebHealthInvocMetric = fn.metric_invocations()
        WebHealthMemMetric = fn.metric("MaxMemoryUsed")
        WebHealthDurMetric = fn.metric_duration()

        # To create alarms: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
        # Expereiment the paramters needed for the alarm
        invoc_alarm = cloudwatch.Alarm(self, f"InvocationsAlarm-{construct_id}",
            metric=WebHealthInvocMetric,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
            alarm_description="Triggers when the Lambda function is not invoked (invocations < 1)."
        )


        mem_threshold_mb = int(memory_size_mb * 0.9)
        memory_alarm = cloudwatch.Alarm(self, f"MemoryAlarm-{construct_id}",
            metric=WebHealthMemMetric,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=mem_threshold_mb, # what is the correct number for the threshold based on the metric
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING, 
            alarm_description=f"Triggers when MaxMemoryUsed > {mem_threshold_mb} MB (≈90% of configured memory)."
        )
        duration_alarm = cloudwatch.Alarm(self, f"DurationAlarm-{construct_id}",
            metric=WebHealthDurMetric,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=300_000, # 300,000 ms = 5 minutes
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING, 
            alarm_description="Triggers when Lambda duration exceeds 5 minutes."
        )
        # Add sns features for these lambda alarms above
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        topic = sns.Topic(self, "AlarmLambdaNotificationTopic",
            display_name="Alarm Notifications for WebHealth Lambda"
        )
            
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Subscription.html
        # Used the prefered ITopic.addSubscription()
        topic.add_subscription(sns_subscriptions.EmailSubscription("22067815@student.westernsydney.edu.au"))
        topic.add_subscription(sns_subscriptions.LambdaSubscription(db_lambda))

        for alarm in [invoc_alarm, memory_alarm, duration_alarm]:
            alarm.add_alarm_action(SnsAction(topic))

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Alias.html
        
        version = fn.current_version
        alias = lambda_.Alias(self, "LambdaAlias",
            alias_name="Prod",
            version=version,
        )
        alias.apply_removal_policy(RemovalPolicy.DESTROY)

         # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html
        '''
        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias, # alias shifts traffic to the previous version of the lambda
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
            alarms=[invoc_alarm, memory_alarm, duration_alarm]
        )
        '''

        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
            alarms=[invoc_alarm, memory_alarm, duration_alarm],
            
            auto_rollback=codedeploy.AutoRollbackConfig(
                failed_deployment=True,
                deployment_in_alarm=True
            )
        )


        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
        ''' # Create metric for lambda - ignore invocmetric = cloudwatch.Metric(, it is bellow it ath is the metric for lambda
        invocmetric = cloudwatch.Metric(
            namespace="AWS/Lambda", # AWS default namespace for lambda metrics
            metric_name="Invocations",
            period=Duration.minutes(5),
        )
        WebHealthInvocMetric = fn.metric_invocations()
        WebHealthMemMetric = fn.metric_duration()

        # To create alarms: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
        # Expereiment the paramters needed for the alarm
        invoc_alarm = cloudwatch.Alarm(self, "InvocationsAlarm",
            id ='alarm_lambda_invocations',
            metric=invocmetric,
            comparrison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1, # what is the correct number for the threshold based on the metric
            evaluation_periods=1,
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Alias.html
            - create a temporary alias (false name) for the lambda function
            - alias shifts traffic to the previous version of the lambda
            - alias's purpose: points to current version of the lambda that is running

        version = fn.current_version
        alias = lambda_.Alias(self, "LambdaAlias",
            alias_name="Prod",
            version=version
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html
        - use to define automated rollback feature
        - BlueGreenDeployment - takes 50% deployment
        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias, # alias shifts traffic to the previous version of the lambda
            deployment_config=LambdaDeploymentConfig.Canary20Percent5Minutes
            alarms=[invoc_alarm, memory_alarm, duration_alarm]
        )
        

        # Add sns features for these lambda alarms
        '''


        urls = constants.MONITORED_URLS
        # set up dashboard from stack: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html
        dashboard = cloudwatch.Dashboard(
            scope=self,
            id="dashboard",
            dashboard_name="URL_Monitor_Dashboard",
        )

        for url in urls:
            # --- Metrics ---
            # To create metrics: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
            avail_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_AVAILABILITY,
                period=Duration.minutes(5), # How often CloudWatch looks at this metric
                label="Availability",
                dimensions_map={"URL": url} # Dimension to filter metric by URL
            )
            latency_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_LATENCY,
                period=Duration.minutes(5),
                label="Latency",
                dimensions_map={"URL": url}
            )
            response_size_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_SIZE,
                period=Duration.minutes(5),
                label="Response Size",
                dimensions_map={"URL": url}
            )

            # --- Alarms ---
            # To create alarms: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
            avail_alarm = cloudwatch.Alarm(self, f"AvailAlarm-{url}",
                threshold=1,  # Trigger alarm if metric falls below 1
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                evaluation_periods=1,# Number of periods to evaluate before triggering alarm, 
                                        # so if does it 3 times then it triggers alarm, but in this case we 
                                        # are only doing it at 1 for immediacy
                metric=avail_metric, # Metric to base alarm on
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description=f"Alarm when the availability metric is below 1 for {url}"
            )
            latency_alarm = cloudwatch.Alarm(self, f"LatencyAlarm-{url}",
                threshold=250, # Trigger alarm if metric is above 250ms
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1, 
                metric=latency_metric,
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description=f"Alarm when the latency metric is above 250ms for {url}"
            )
            response_size_alarm = cloudwatch.Alarm(self, f"ResponseSizeAlarm-{url}",
                threshold=20000, # Trigger alarm if metric is above 20000 bytes
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1, 
                metric=response_size_metric,
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description=f"Alarm when the Response size metric is above 20000 bytes for {url}",
            )

            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
            topic = sns.Topic(self, f"AlarmNotificationTopic-{url.replace('https://','').replace('.','-')}",
                            display_name=f"Alarm Notifications for {url}")
            
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Subscription.html
            # Used the prefered ITopic.addSubscription()
            topic.add_subscription(sns_subscriptions.EmailSubscription("22067815@student.westernsydney.edu.au"))
            topic.add_subscription(sns_subscriptions.LambdaSubscription(db_lambda))

            avail_alarm.add_alarm_action(SnsAction(topic))
            latency_alarm.add_alarm_action(SnsAction(topic))
            response_size_alarm.add_alarm_action(SnsAction(topic))

            # --- Dashboard Widget ---
            metrics_for_url = [avail_metric, latency_metric, response_size_metric]

            # configure displays of graphs: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html
            widget = cloudwatch.GraphWidget(
                title=f"Metrics for {url}", # title of graph
                left=metrics_for_url, # display metrics on left side of graph
                legend_position=cloudwatch.LegendPosition.RIGHT, # Legend placement
                period=Duration.minutes(1),  # every minute it should show metric on dashboard
                left_y_axis=cloudwatch.YAxisProps(min=0), # y-axis start at 0
            )

            dashboard.add_widgets(widget)


''' No more recordings for the tutoral anymore, so take your own notes

insert this into line 112:         metrics = [avail_metric, latency_metric, response_size_metric] # Collect all metrics into a list


- To reference you code make sure you get it from AWS cdk links
- roles are needed later on 
- move constants from WHLambda to a constants.py file in module

- in the cloudwatch logs if it has start and end, it means the function is working


To create a dashboard:
- Lambda function, publish metrics to cloudwatch ( this has been done)
- Based on these metrics we want alarms ( set threshold for latency and availability 
    - if theshold is bellow 1 then website not avialble)
    - if latency is above x ammount, raise alarm
- From these alarms we want a simple notification service (email and sms stating that one of the metrics has an alarm)
    It also triggers another lambda (Dynamo DB), once it runs it writes alarm informaiton into Dynamo Database
- From these we want to log the information in a Dynamo DB ()

- Stack file contains all components of your infrastructure (alarms, lambda functions, synth, dynamo DB) not your metrics as thats on lambda 
- Lambda is using SDK, stack file uses CDK
- Make it reference using one namespace

- We currently have custom metrics


Metric: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html

# Create a metric
metric = cloudwatch.Metric(
    namespace="AWS/EC2",
    metric_name="CPUUtilization",
    statistic="Average",
    period=Duration.minutes(5)
)

In Boto3 the dimentiosn is a list of dictionaries

Aim for 18 lines total on dashboard

'''

'''
26/8/25
- Publish metrics -> alarms -> notification service (email and sms) -> 
Lambda or EC2 to write to the databse about the alarms/metrics-> Dynamo DB (no sequal database)

- Lambda is used as it should only be triggered when an alarm is sent off, and not needed to run all the time


SMS:
- https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
- Create a topic: everyone that subscribes to this topic will get a message when an alarm is sent off

topic = sns.Topic(self, "AlarmNotification", display_name="Alarm Notification Topic")
- give is a display name
- for the topic_names or names in general, if AWS already does it for you, then you don't need to give it a name


https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Subscription.html
bellow the alarms function do avail_alarm.add_alarm_action("insert topic here")


Write information into database:
https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html
- subscription target: sends alarm message to email address and lambda function, so we need another lambda function for SNS topic

https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/LambdaSubscription.html
- Create a new lambda function bellow the WHLambda function above. Call it DBLambda

- create a new dynamo DB role to give full access, we don't need a lambda role as it has already been done

- Dynamo DB will created in a stack file as its apart of your infrastructure

https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html

https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
- use the link above as the original table is being deprecated (not approved anymore)
import aws_cdk.aws_dynamodb as dynamodb

mrsc_table = dynamodb.TableV2(stack, "MRSCTable",
    partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
    multi_region_consistency=dynamodb.MultiRegionConsistency.STRONG,
    replicas=[dynamodb.ReplicaTableProps(region="us-east-1")
    ],
    witness_region="us-east-2"
)
table = dynamodb.Table(self, "Table",
    partition_key=dynamodb.Attribute(
        name="id",
        type=dynamodb.AttributeType.STRING
    ),
    stream=dynamodb.StreamViewType.NEW_IMAGE
)
 - 


 We we are at so far:
- Lambda function to publish metrics to cloudwatch (done)
- Create threshold for the metrics to trigger alarms (done)
- SNS is triggered once it goes past the threshold, if it goes back to normal no sns is triggered, only once it breaks the threshold
- SNS topic is created in stack file (emails, sms)
- Lambda function created in stack to write alarm information into Dynamo DB
- Dynamo DB table is created in the stack file, but to write to the database create a lambda file
- The dynamo DB table is created in stack file as if we did in lambda file then we would create the same table over and over again
    - environment variables

- 




'''
'''
Feedback for work so far: 26/8/25
- read me file think of it as a user manual from the perspective of a user
- think about how response size is helpful in monitoring website health
- move websites to constants file as that is used in multiple files
'''


'''
Pipeline stuff:
go to here https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines.html


Code for the pipeline: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipeline.html
Code for Pipeline Source: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html

create a new file for stack file so do mikdir, cd PipelineSprint. Folow rest of commands from project setup:
    - npm install -g aws-cdk
    - git clone <repo>
    - mkdir <your_name>
    - cd <your_name>
    - cdk init --language python
    - source .venv/bin/activate
    - python -m pip install -r requirements.txt

In the pipelie stack code:
- source = pipelines.CodePipelineSource.git_hub("owner/repo", "main", authentication, trigger)
- for authentication we need to go into the github repository, go to settings -> developer settings -> personal access tokens -> tokens (classic) -> generate new token
    - the token is only shown once so copy it into notes
- Trigger: make it a poll

import aws_codePilepline

source = pipeline.CodePipelineSource.git)hub( # look up the reference for this part
    repo_string "EugeneKosiak/WSU_DevOps_2025" # repo string
    branch = "main"
    action_name = :WSU_DeveOps_2025" # repo name
    authentication = SecretValue.secrets_manager("insert name given to token here - the link bellow"),
    trigger = GitHubTrigger('POLL') # Poll checks repo to see if there are any changes
    )

in this link: https://docs.aws.amazon.com/cli/latest/reference/secretsmanager/create-secret.html follow, this would be inputed into the terminal
    aws secretsmanager create-secret \
        --name MyTestSecret \
        --secret-string file://mycreds.json

Shell Step:
- take the code and build it
https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/ShellStep.html


    synth=pipelines.ShellStep("Synth",
        input=source,
        commands=['npm install -g aws-cdk','cd <>', 'python -m pip install -r requirements.txt', 'cdk synth'],
            # this part 'npm install -g aws-cdk', it depends, just do trial and error
        env={
            "COMMIT_ID": source.source_attribute("CommitId")
        }
    )
    # import pipelines as pipelines
    pipeline = pipelines.CodePipeline(scope, "EugnenPipeline",
        synth=synth)


steps:
- source, synth, pipeline, add_stage. Unit tests will be done next week
        

'''
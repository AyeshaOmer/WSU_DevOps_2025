Project-1 Stack
AWS Lambda
AWS Lambda – Function Configuration and Timeout

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function-timeout

Defines Lambda runtimes, handlers, timeouts, and environment variables for the Web Health Lambda and Database Lambda.

Amazon DynamoDB
Amazon DynamoDB – TableV2

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html

Creates two NoSQL tables — one for URL targets and one for monitoring results (MRSC). Also used for data seeding via a custom resource.

AWS Identity and Access Management (IAM)
IAM – PolicyStatement

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html

Grants specific permissions to Lambda roles for CloudWatch metric publishing and DynamoDB read/write actions.

IAM – Role

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html

Assigns execution roles to Lambdas so they can securely access CloudWatch and DynamoDB.

Amazon EventBridge Scheduler
EventBridge – Scheduled Lambda Invocations

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html

Schedules the Web Health Lambda to run automatically every five minutes to check website status.

Amazon Simple Notification Service (SNS)
SNS – Topic

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html

Creates an SNS topic for broadcasting alarm notifications to email subscribers and Lambdas.

SNS – Subscription

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Subscription.html

Subscribes email addresses and Lambdas to SNS topics to receive alerts when alarms trigger.

Amazon CloudWatch
CloudWatch – Metric

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html

Defines custom metrics for each URL’s latency and availability.

CloudWatch – Alarm

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html

Creates alarms that trigger SNS actions when latency or availability breach defined thresholds.

CloudWatch – Dashboard

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html

Builds a CloudWatch dashboard to display health metrics for all monitored URLs.

CloudWatch – GraphWidget

Link: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html

Displays graphs of latency and availability for each URL within the dashboard.

Project-1-WHLambda
AWS Documentation Index — WebHealth Lambda

File: gursh/modules/WHLambda.py
Purpose: References for AWS services and APIs used in the Web Health monitoring Lambda function that measures availability and latency, publishes metrics to CloudWatch, and stores results in DynamoDB.

AWS Lambda
AWS Lambda – Function Handler (Python)

Link: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html

Explains how the lambda_handler(event, context) entry point works in Python-based Lambda functions.

Amazon CloudWatch
Amazon CloudWatch – PutMetricData (Boto3 client)

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/put_metric_data.html

Used in _publish() to send custom CloudWatch metrics for URL latency and availability.

Amazon CloudWatch – Metric Dimensions and Units

Link: https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html

Defines valid metric attributes like MetricName, Dimensions, Unit, and Value used in the MetricData list.

Amazon DynamoDB
Amazon DynamoDB – Table Resource (Boto3)

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table

Used to access tables through ddb.Table(TABLE_NAME) for reading URLs and writing results.

Amazon DynamoDB – scan

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html

Used in _get_urls() to retrieve all items (URLs) from the target table.

Amazon DynamoDB – put_item

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html

Used in _write() to insert new monitoring results (availability, latency, timestamp) into the results table.

Python Standard Library References
urllib.request – urlopen

Link: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen

Used in _check() to open each URL and measure response time for availability and latency.

datetime – datetime.now(timezone.utc)

Link: https://docs.python.org/3/library/datetime.html#datetime.datetime.now

Used in _write() to generate timestamps for DynamoDB entries.

decimal.Decimal

Link: https://docs.python.org/3/library/decimal.html

Used to store numeric values in DynamoDB with high precision (avoiding float inaccuracies).

AWS CDK – Python Modules Overview

Link: https://docs.aws.amazon.com/cdk/api/v2/python/modules.html

General reference for AWS CDK module usage that defines environment variables (such as TABLE_NAME and URL_NAMESPACE) from your stack deployment.

Project-1 DBLambda
docs/AWS_DOCS_DB_LAMBDA.md

AWS Documentation Index — DB Lambda

File: modules/DBLambda.py
Purpose: References for services and APIs used by the Lambda that processes CloudWatch Alarm notifications (via SNS) and stores structured records in DynamoDB.

AWS Lambda
Lambda — Python Handler

Link: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html

Explains the lambda_handler(event, context) entry point and event processing model.

Amazon SNS and CloudWatch Alarms
Using AWS Lambda with Amazon SNS

Link: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html

How SNS invokes a Lambda function and the shape of Records[*].Sns.Message.

CloudWatch Alarms — Alarm Notifications via Amazon SNS

Link: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html

Describes CloudWatch alarm notifications and the JSON payload sent to SNS (fields like AlarmName, NewStateValue, NewStateReason, Trigger, Dimensions, etc.).

Amazon DynamoDB (Boto3)
DynamoDB — Table Resource

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table

Accessing a table with boto3.resource("dynamodb").Table(name).

DynamoDB — put_item

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html

Writing an item as used in _put_item().


Project-2 API Gateway
AWS Documentation Index — API Gateway Lambda (Project 2)

File: modules/APIgateway.py
Purpose: References for AWS services and APIs used in the Lambda function that handles REST API requests from Amazon API Gateway and performs CRUD operations on the DynamoDB URLs table.

AWS Lambda
Lambda — Python Handler

Link: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html

Explains how the lambda_handler(event, context) function receives event payloads, including httpMethod, body, and queryStringParameters when invoked through API Gateway.

Amazon API Gateway
API Gateway + Lambda Integration

Link: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

Describes how API Gateway passes request data (method, body, headers, query parameters) to a Lambda using the proxy-integration event format.

API Gateway — CORS Configuration

Link: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html

Explains the response headers (Access-Control-Allow-*) returned in the resp() helper to enable cross-origin requests.

API Gateway — Supported HTTP Methods

Link: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-settings-method-request.html

Lists REST methods (GET, POST, PUT, DELETE, OPTIONS) used for CRUD functionality.

Amazon DynamoDB (Boto3)
DynamoDB — Table Resource

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table

Used to connect to a specific table defined by the TABLE_NAME environment variable.

DynamoDB — put_item

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html

Used in the POST and PUT methods to create or update URL entries.

DynamoDB — get_item

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/get_item.html

Used in the GET method to read a single URL entry.

DynamoDB — scan

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html

Used in the GET method to list all URLs in the table.

DynamoDB — delete_item

Link: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/delete_item.html

Used in the DELETE method to remove a URL record.


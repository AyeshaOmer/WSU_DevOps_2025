# WSU_DevOps_2025
---
## Guransh DevOps Project
A serverless monitoring system built using **AWS Lambda**, **CloudWatch**, **DynamoDB**, and **SNS**.  
It automatically checks the health and latency of multiple websites, stores metrics, visualises them on dashboards, and sends alert notifications when thresholds are crossed.

**Key Features**
- Periodic URL health checks (ping + latency)
- Results stored in DynamoDB
- Metrics visualised in CloudWatch dashboards
- SNS email alerts on downtime

---
### Setting Up the Project
**Prerequisites**
- Install Python
- Install VS Code
- Install NodeJS

**Setup**
  - The AWS CLI must be installed through [this link](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  - Run the AWS Configure
  - Run the following commands to clone the repo and setup your project
  - ```
    npm install -g aws-cdk
    git clone https://github.com/AyeshaOmer/WSU_DevOps_2025.git
    mkdir Gursh
    cd Gursh
    cdk init --language python
    source .venv/bin/activate
    python -m pip install -r requirements.txt
---

**Deploy**

To deploy, Use **cdk synth** first and then **cdk deploy** to deploy and run your application in the AWS console. After deploying, always remember to destroy it using **cdk destroy**.

## Project 1 — Website Monitoring System (Based on AWS CDK Canary Specification)

This project uses **AWS CDK** to deploy a canary-based monitoring system that measures the **availability** and **latency** of multiple web resources.  
It extends the basic canary Lambda into a **web crawler** that periodically tests multiple target URLs and records metrics in **Amazon CloudWatch**.

### 1. Canary Lambda Function
- The system begins with a **Lambda function acting as a canary**.  
- It executes on a schedule and performs HTTP requests to verify that each target website is reachable.  
- For each request, it records two key metrics:
  - **Availability** – whether the site responded successfully.  
  - **Latency** – the time taken to receive a response.  
- These metrics are published to **CloudWatch** under a dedicated namespace.

### 2. Web Crawler Extension and Metrics Collection
- The single-URL canary is extended to handle a **list of websites** (stored in a DynamoDB table).  
- The Lambda runs every 5 minutes and writes `<availability, latency>` metrics for each URL.  
- Metrics are sent to **CloudWatch** using the `put_metric_data()` API.  
- Each metric includes dimensions such as the specific URL being monitored.

### 3. Dashboards and Alarms
- A **CloudWatch Dashboard** is automatically generated to visualize health data for all monitored websites.  
- **CloudWatch Alarms** are created to trigger when any metric exceeds its threshold:
  - Availability < 1  
  - Latency > 250 ms  
  - Response size < 20 KB  
- These alarms notify an **SNS Topic**, which has:
  - An **email subscription** (for user alerts).  
  - A **Lambda subscription** (for database logging).  
- Alarm events are also recorded in **DynamoDB**, enabling a historical view of downtime incidents.

### 4. Unit and Integration Testing
- Unit tests validate that all AWS resources are correctly created and wired together:
  - Lambda functions exist and are deployed.  
  - Correct number of CloudWatch alarms.  
  - Alarm thresholds match the prescribed values.  
  - SNS Topic and subscriptions are functional.  
  - DynamoDB tables exist and are linked to Lambdas.  
- Integration tests verify that metric publication and alert flow work as expected using local mocks (`moto` and `pytest`).

Run all the unit tests for Project 1 tests locally with:
```bash
 pytest -v c:\Users\Guran\Documents\NewProject\WSU_DevOps_2025\Gursh\gursh\modules\tests\unit\test_application.py
```
## Project 2 — CRUD API Gateway for URL Management

Project 2 extends the website monitoring system by adding a **public CRUD API** that allows users to manage the list of websites to be monitored.  
This is implemented using **Amazon API Gateway**, **AWS Lambda**, and **Amazon DynamoDB**, enabling dynamic updates to the target list without modifying the core monitoring stack.

### 1. Purpose
- Provide an API interface for users to **add, view, update, and delete** target URLs.  
- Store the list of monitored websites in a dedicated **DynamoDB table**.  
- Allow the main monitoring Lambda (from Project 1) to automatically read from this table to get its target URLs.

### 2. API Gateway and Lambda Integration
- A **Lambda function (`APIgateway.py`)** serves as the backend for all API requests.
- **API Gateway** exposes this Lambda through a RESTful interface with standard HTTP methods:
  - **POST** – Add a new URL to the DynamoDB table.
  - **GET** – Retrieve all URLs or a specific one.
  - **PUT** – Update an existing URL entry.
  - **DELETE** – Remove a URL from the database.
- The Lambda function uses the `boto3` library to interact with DynamoDB, ensuring secure, scalable data operations.

### 3. DynamoDB Table
- The URLs are stored in a DynamoDB table named **`UrlsTable`**.  
- Each item uses the `url` attribute as its **primary key**.  
- The table is created and managed automatically by AWS CDK, and it is also accessed by:
  - **WebHealth Lambda** (to read URLs)
  - **CRUD Lambda** (to modify URLs)

### 4. Unit Testing (Project 2)

These tests verify each CRUD path of the API Lambda locally using `pytest` and `moto` (mocked DynamoDB).  
They call your actual `lambda_handler` and monkeypatch the module’s `table` to a moto table, so no AWS calls are made.

Covered:
- POST adds a new URL to the table
- GET lists all URLs (or a specific one)
- PUT updates an existing URL
- DELETE removes the URL

Run the tests:
```bash
pytest -v gursh/modules/tests/unit/test_project2.py
```

### 5. Testing the CRUD API Gateway Endpoints (Manual)

After deploying the stack, you can manually test your live API using **PowerShell commands** with `irm` (Invoke-RestMethod).  
Replace the `$BASE` value with your actual API Gateway endpoint shown in the AWS Console.

#### Set the base URL:
$BASE = "https://<YOUR_API_ENDPOINT>/prod"

#### 1. GET – Retrieve all URLs
irm "$BASE/urls"

#### 2. DELETE – Remove a URL
irm -Method DELETE "$BASE/urls?url=https://example.com"

#### 3. POST – Add a new URL
irm -Method POST "$BASE/urls" -ContentType "application/json"
-Body '{"url":"https://example.com"}'

#### 4. PUT – Update an existing URL
irm -Method PUT "$BASE/urls" -ContentType "application/json"
-Body '{"url":"https://example.com","note":"Updated entry"}'

---

## Conclusion

This DevOps project demonstrates the design and deployment of a fully serverless website monitoring system using AWS Cloud services.  

In **Project 1**, the infrastructure was built entirely with **AWS CDK**, combining **Lambda**, **CloudWatch**, **DynamoDB**, and **SNS** to monitor multiple URLs, record health metrics, trigger alarms, and send notifications.  

In **Project 2**, the system was extended with a **CRUD API Gateway** that allows dynamic management of monitored URLs through a Lambda-powered REST API, backed by DynamoDB for persistent storage.  

Both projects were thoroughly tested using **pytest** and **moto**, ensuring all components—Lambdas, Alarms, Tables, and APIs—function as intended both locally and after deployment.  

**Overall, the project highlights practical implementation of DevOps concepts such as infrastructure as code, automation, serverless monitoring, continuous validation, and scalability in a cloud-native environment**

---

## References

The following official AWS and Boto3 documentation resources were used to design and implement **Project 1 (Website Monitoring System)**:

- **AWS Lambda – Function configuration and timeout**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function-timeout  
  *Used to define and configure multiple Lambda functions (Web Health, Database, and CRUD Lambdas) with custom runtimes, timeouts, and handlers.*

- **Amazon DynamoDB – TableV2**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html  
  *Used to create and manage DynamoDB tables for storing monitoring results and target URLs.*

- **Amazon API Gateway – LambdaRestApi**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaRestApi.html  
  *Used to expose CRUD endpoints through API Gateway, allowing Lambda to perform POST, GET, PUT, and DELETE operations.*

- **Amazon EventBridge Scheduler – Scheduled Lambda Invocations**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html  
  *Used to create a periodic event rule that automatically triggers the Web Health Lambda every few minutes.*

- **AWS Identity and Access Management – PolicyStatement**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html  
  *Used to grant specific permissions (CloudWatch and DynamoDB actions) to Lambda execution roles.*

- **AWS Identity and Access Management – Role**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html  
  *Used to assign execution roles to Lambdas, enabling secure access to AWS services such as DynamoDB and CloudWatch.*

- **Amazon CloudWatch – Metric**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html  
  *Used to define custom metrics such as URL latency, availability, and response size for each monitored website.*

- **Amazon CloudWatch – Alarm**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html  
  *Used to create CloudWatch alarms that trigger notifications when latency, memory, or availability metrics exceed thresholds.*

- **Amazon CloudWatch – Dashboard**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html  
  *Used to create a unified dashboard that displays real-time performance graphs for all monitored URLs.*

- **Amazon CloudWatch – GraphWidget**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html  
  *Used to visually represent metrics such as latency and availability in interactive CloudWatch dashboard widgets.*

- **Amazon Simple Notification Service (SNS) – Topic**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html  
  *Used to create SNS topics that broadcast alerts to subscribers when alarms are triggered.*

- **Amazon Simple Notification Service (SNS) – Subscription**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Subscription.html  
  *Used to subscribe both email addresses and Lambda functions to SNS topics for alarm notifications.*

- **AWS Lambda – Alias (version management)**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Alias.html  
  *Used to manage Lambda versions and deploy blue/green updates by pointing aliases to different Lambda versions.*

- **AWS CodeDeploy – LambdaDeploymentGroup (blue-green deployment)**  
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html  
  *Used to enable blue-green (canary) deployment strategy for the Lambda function with automated rollback support.*

- **Boto3 CloudWatch Client – get_metric_data**  
  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/get_metric_data.html  
  *Used in Lambda scripts to fetch and process CloudWatch metric data for monitoring and alerting purposes.*

- **AWS CDK – Python Modules Overview**  
  https://docs.aws.amazon.com/cdk/api/v2/python/modules.html  
  *Used as a general reference for understanding available AWS CDK Python modules and constructs.*

  ## Future Enhancements

- Learn and Integrate AWS CodePipeline for full CI/CD automation

## Acknowledgements

Big thanks to **Ash Mam** for all the guidance, support, and helpful feedback throughout this project.  

Also, a special shoutout to **Eugene** for all the help throughout the project. 



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
pytest -v 


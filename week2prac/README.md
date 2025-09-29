# Website Availability Monitor with AWS CDK

This project uses **AWS CDK (Python)** to deploy a monitoring solution for [https://www.nytimes.com](https://www.nytimes.com). It consists of:

* An AWS **Lambda function** that checks website latency, HTTP status, and availability
* An **EventBridge rule** that runs the Lambda every 5 minutes
* **Custom CloudWatch metrics** for latency, availability, and status codes
* **CloudWatch alarms** with **SNS notifications**
* **DynamoDB table** logging alarm events


---

### 1. Prerequisites

* AWS CLI configured
* Python 3.10 or newer
* AWS CDK installed globally:

```bash
npm install -g aws-cdk
```

### 2. Set Up the Project

```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Bootstrap & Deploy

Replace `YOUR_ACCOUNT_ID` in `app.py` with your AWS Account ID.

Then run:

```bash
cdk bootstrap
cdk deploy
```

---

## What It Does

Every 5 minutes, a Lambda function runs that:

* Sends an HTTP GET request to each URL listed in sites.json
* Measures latency in milliseconds
* Records the HTTP status code
* Publishes custom CloudWatch metrics:

  * `NYTMonitor/Latency`
  * `NYTMonitor/Availability`
  * `NYTMonitor/StatusCode_200` (and others if they occur)

* Triggers CloudWatch alarms if:

  * Availability < 1
  * Latency > 2000 ms

* Publishes alarm notifications to SNS (email + logging Lambda)

* Logs all alarms into a DynamoDB table (WebMonitorAlarmLogs) with:

  * alarm_name
  * timestamp
  * new_state
  * reason
---

## Viewing Results

### CloudWatch → Metrics

1. Go to **CloudWatch > Metrics**
2. Choose **Custom namespaces**
3. Select **`NYTMonitor`**
4. View:

   * `Latency`
   * `Availability`
   * `StatusCode_200`, `StatusCode_500`, etc.

### CloudWatch → Logs

1. Go to **CloudWatch > Logs > Log groups**
2. Look for the group starting with `/aws/lambda/MonitorNYT`
3. Inspect logs for details on each execution

### CloudWatch Dashboard

* Open the dashboard WebHealthDashboard for visual metrics and site-specific graphs
* Shows:

  * Availability
  * Latency

### DynamoDB Alarm Logs

* Table: WebMonitorAlarmLogs
* Columns:

  * alarm_name
  * timestamp
  * new_state
  * reason

* Stores each triggered alarm for auditing or analysis
---

## Optional Enhancements

* Add more SNS subscriptions (Slack, SMS, Lambda)
* Add more websites to sites.json
* Visualize metrics with additional CloudWatch dashboard widgets
* Implement anomaly detection on metrics
---

## Cleanup

To delete all resources created:

```bash
cdk destroy
```



# Website Availability Monitor with AWS CDK

This project uses **AWS CDK (Python)** to deploy a monitoring solution for [https://www.nytimes.com](https://www.nytimes.com). It consists of:

* An AWS **Lambda function** that checks website latency, HTTP status, and availability
* An **EventBridge rule** that runs the Lambda every 5 minutes
* **Custom CloudWatch metrics** for latency, availability, and status codes


---

## Getting Started

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

* Sends an HTTP GET request to `https://www.nytimes.com`
* Measures latency in milliseconds
* Records the HTTP status code
* Publishes custom CloudWatch metrics:

  * `NYTMonitor/Latency`
  * `NYTMonitor/Availability`
  * `NYTMonitor/StatusCode_200` (and others if they occur)

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

---

## Optional Enhancements

* Add CloudWatch **alarms** for availability drops
* Add **SNS or email alerts**
* Monitor multiple URLs
* Visualize with a **CloudWatch dashboard**

---

## Cleanup

To delete all resources created:

```bash
cdk destroy
```



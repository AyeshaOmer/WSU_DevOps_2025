# Website Availability Monitor with AWS CDK

This project uses **AWS CDK (Python)** to deploy a monitoring solution for multiple websites. It consists of:

- An AWS **Lambda function** that checks website latency, HTTP status, and availability
- An **EventBridge rule** that runs the Lambda every 5 minutes
- **Custom CloudWatch metrics** for latency, availability, and status codes
- A **CloudWatch Dashboard** to visualise website health


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

### 3. Configure and Deploy
Edit sites.json to add websites

### 4. Bootstrap & Deploy

Replace `YOUR_ACCOUNT_ID` in `app.py` with your AWS Account ID.

Then run:

```bash
cdk bootstrap
cdk deploy
```

---

## What It Does

Every 5 minutes, a Lambda function runs that:

- Sends an HTTP GET request to each website in the `sites.json` file
- Measures **latency** in milliseconds
- Records the **HTTP status code** (e.g., `200`, `404`, `500`)
- Publishes custom CloudWatch metrics:
  - `NYTMonitor/Latency`
  - `NYTMonitor/Availability`
  - `NYTMonitor/StatusCode_200`, `StatusCode_500`, etc.

---

## Viewing Results

### CloudWatch → Metrics

1. Go to **CloudWatch > Metrics**
2. Choose **Custom namespaces**
3. Select **`NYTMonitor`**
4. View:
   - `Latency`
   - `Availability`
   - `StatusCode_200`, `StatusCode_500`, etc.

### CloudWatch → Logs

1. Go to **CloudWatch > Logs > Log groups**
2. Look for the group starting with `/aws/lambda/MonitorNYT`
3. Inspect logs for details on each execution, including any errors or exceptions

### CloudWatch → Dashboard

1. Go to **CloudWatch > Dashboards**.
2. Select **WebHealthDashboard**.
3. View the following widgets:
   - **Availability** for each site (Up or Down)
   - **Latency (p95)** for each site
   - **Status codes** (e.g., `200`, `500`, etc.)

---

## Optional Enhancements

- **CloudWatch Alarms**:
  - Set up **alarms** for the `Availability` metric (e.g., if availability drops below `1`).
  - Set up alarms for **high latency** (e.g., `Latency > 2000ms`).
  
- **SNS/Email Alerts**:
  - Set up **SNS** to send **email alerts** when an alarm is triggered (for availability or latency).

- **Monitor More URLs**:
  - Update the `sites.json` file to add more websites. The Lambda function will automatically crawl the new websites every 5 minutes.

- **Scalability**:
  - As the number of websites grows, increase the Lambda function’s memory or adjust the timeout to handle more websites efficiently.

---

## Cleanup

To delete all resources created by this project:

```bash
cdk destroy
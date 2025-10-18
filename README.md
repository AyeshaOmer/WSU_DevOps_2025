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
###Setting Up the Project
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

**Deploy**
Once the project is deployed, Use **cdk synth** and **cdk deploy** to deploy and run your project in the AWS console. After, always remember to destroy it using **cdk destroy**.

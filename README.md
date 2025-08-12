# WSU_DevOps_2025
This is a repo for the 2025 batch of DevOp Course. 

📖 Overview

This is a cdk project that runs in lambda. This project is about web monitoring where you are able to choose a URL to monitor for HTML status as well as latency. The Lambda will published the results to the cloudwatch function in AWS.

🚀 Getting Started
Prerequisites
You'll need the following installed:
* AWS CLI: Configured with your AWS credentials.
* AWS CDK: npm install -g aws-cdk
* Python 3.9+
* Pipenv or pip

Setup Guide

1. Clone the repository
2. Do cdk inti
3. Activate a Python virtual environment
4. Install the required Python dependencies (pip install -r requirements.txt)
5. Do cdk bootstrap
6. In the WanMONLambda.py file chagne the WEBSITE to whatever the website you want monitored
7. cdk synth
8. cdk deploy 


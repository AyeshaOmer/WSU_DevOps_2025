
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

# AWS Lambda Monitoring with CDK and Synthetics Canary
## Update 4/8/25

This project integrates an AWS Lambda function and an AWS Synthetics Canary using AWS CDK (Python) to monitor an external web resource. The Canary simulates a real user visiting a webpage every 5 minutes, helping track the availability and performance of the resource.


What it does:
- Deploys lambda function with a simple hello message
- Sets up a Synthetics Canary that periodically checks the health of a web page (every 5 minutes).
- Metrics and alarms setup is commented out for the time being, and will be added in a future update.

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- Open AWS Lambda Console.
- Click “Create function” → select "Author from scratch".
- Name the function (e.g., MyLambda) and choose the runtime (e.g., Python or Node.js).
- Paste the Lambda code into the inline editor.
- Save and deploy the function using the AWS Console UI.

Testing:
- after doing cdk synth, deploy go onto the lambda function website and you should see this output
    {
    "statusCode": 200,
    "body": "\"Hello from Lambda!\""
    // there is also some mention of latency and availability
    }

Quality Characteristics:
- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout 
    to minimise latency and catch outages quickly.
- Usability: 
    - Canary can be built upon with matrics later on


Future Improvements:
- Add Cloudwatch Alarms for Lambda metrics

# AWS - Building the Foundation of DevOps
## Update 18/8/25
This project integrates the availability and latency metrics into the Web Health module. The crawler runs periodically every 5 min to write the availability and latency for metrics of a website. Using the Cloudwatch it produces a dashboard showing the web health(metrics) of each website.


What it does:
- Display the availabilty and latency of Google, Youtube and Facebook websites
- Publishes metrics to CloudWatch
- Display results in a CloudWatch dashboard

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the code onto
the Lambda website.
-  Once on the lambda website your code will appear in a function, and once you make a test,
it will test the websites.
- After testing, go to the Cloudwatch dashboard and you will see graphs of the metrics of the website

Testing:
- After doing the test it should show this in the console (function logs)
    Health check for https://www.youtube.com: {'
        url': 'https://www.youtube.com', 
        'availability': 1, 
        'latency_ms': 478.26457023620605, 
        'status_code': 200
    }

Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.
- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0)
- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails, the metric reports unavailability, making outages visible on the dashboard.
    - Scheduled EventBridge rules guarantee regular execution.
- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.

Future Improvements:
- The log removal policy is not functioning
- Testing fails for the third website (fixed now due to timeout of lambda being too short)
- Add a third metric to test for.

# AWS - Building the Foundation of DevOps
## Update 22/8/25
This update involves the additoinal metric response size into the Web Health Module. It also includes the ability to create a Cloudwatch dashboard to monitor all three metrics of three websites give. It includes alarms that alert the user if the latency or response size is too much to handle or if the availability is less than 1, meaning not available. It also includes a constants file to to centralize configuration values (such as URLs, thresholds, and metric names), and has fixed all the future improvements from the previous update.

What it does:
- Display the availabilty, latency, and response size of Google, Youtube and Facebook websites
- Creates its on Cloudwatch dashboard
- Publishes metrics to CloudWatch
- Display results in a CloudWatch dashboard

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the code onto
the Lambda website.
-  Once on the lambda website your code will appear in a function, and once you make a test,
it will test the websites.
- After testing, go to the Cloudwatch dashboard and you will see three graphs each representing a metric, with a key indicating each website.

Testing:
- After pressing the test button on lambda, go to cloudwatch -> all alarms, this will show which metrics have triggered an alarm.
- Also after pressing the test button, go to cloudwatch -> Dashboards -> URL_Monitor_Dashboard, you should all the metrics of the websites, shown in the graphs.

Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.

- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0).
    - Response size metric allows monitoring of abnormal increases/decreases in webpage content size that may indicate outages, errors, or changes.
    - The metrics are checked every minuete to provide more data points to capture and display on the graphs.
    - Scalability: It can perform metrics on any number of websites, as long as you add the website link in the url list that is on WHLambda and stack file.

- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails, the user will have an alarm appear in Cloudwatch indicating that it has been set off. 
    - The metric reports if the website exceeds the limit on response size and latency, or if the website is not available.

- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.

Future Improvements:
- Add SMS/email feature where the user is to be notified if a metric's alarm has been sent off.
- Implement another lambda (Dynamo DB) to write alarm information into a Dynamo Database, from this we want to log the information in a Dynamo DB.


# AWS - The First Way - The Technical Practices of Flow (Cont.) 
## Update 2/9/25
This update involves SNS to send emails to the DevOps engineeer that an from one of the metrics has been triggered. The information from the SNS is sent to a Dynamo DB where the alarmed metric data is stored in.

What it does:
- Send alarmed metric data to DevOps Engineer via email
- Store alarmed metric data into DynamoDB

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the code onto
the Lambda website.
-  Once on the lambda website your code will appear in a function, and once you make a test,
it will test the websites.
- After testing, go to the Cloudwatch dashboard and you will see three graphs each representing a metric, with a key indicating each website.
- SNS:
    - After deploying stack file, it will automatically send an email to the DevOps Engineer if an alarm has been triggered.
    - In the email you can click on a link that will take you to view the alarm in the AWS Management Console.
    - After clicking the link it will show you the alarm dashboard
- DB Lambda:
    - Go to DBLambda on the lambda website, then go to tables where you can see your table that you created in the stack.
    - Click on explore table options, and scroll down until you get items returned, in this section you should see the metric that trigggered the alarm and its details such as:
        - Alarm Description
        - Alarm Name
        - Dimensions
        - Metric Name
        - New State Reason
        - Timestamp

Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.
    - Email notifications via SNS, ensure that only the DevOps engineer receives alerts for triggered metrics, reducing the risk of sensitive information being missed or exposed.
    - AWS IAM roles and policies control Lambda and DynamoDB access, ensuring that only authorized functions and users can read/write metric data.
    - Data storage in DynamoDB is secure and encrypted at rest by AWS, protecting sensitive monitoring information.

- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0).
    - Response size metric allows monitoring of abnormal increases/decreases in webpage content size that may indicate outages, errors, or changes.
    - The metrics are checked every minuete to provide more data points to capture and display on the graphs.
    - It is scalable as it can perform metrics on any number of websites, as long as you add the website link in the url list that is on WHLambda and stack file.

- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails or exceeds metric thresholds, an email is sent to the DevOps engineer with details of the triggered metric.
    - Alarm emails include a link to the CloudWatch dashboard for the specific metric and website.
    - Alarm details are also stored in DynamoDB, ensuring a durable record of all events for future reference or audits.

- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.
    - Alarm emails include direct links to the alarm in the AWS Management Console for quick access and investigation.

Future Improvements:
- make the code more modular, by adding url links to the constants file


# Read Me File final version

## Overview - tidy up the wording
The project uses AWS services to monitor website health. It is deployed through a pipline which allows for project to be properly tested before deployment. Checking through unit, functional, and integration tests. Once these tests are sucessfull, the project is properly deployed and is able to perform with the bellow features.

This project uses AWS Lambda and a Synthetics Canary, deployed via AWS CDK (Python), to monitor external websites by tracking availability, latency, response size, and memory metrics. The Canary simulates real user visits every 5 minutes, while Lambda collects metrics and publishes them to CloudWatch dashboards. 

Alarms are configured to alert users if availability drops below 1, latency is high, or response size is abnormal. SNS sends email notifications to DevOps engineers when alarms are triggered, and the alarmed metric data is logged in DynamoDB. 

To extend on the new metrics memory, invocations, and duration metrics, they have been included to monitor the lambdas, with their metrics uploaded to cloudwatch. The alarms are configured to activate if the memory exceeds 90% usage, the invocations captured by the lambda function is not invoked, and the lambda duration does not exceed 5 minuetes. SNS sends email notifiactions to DevOps engineres when alarms are triggered, the alarmed metric is logged into DynamoDB, and the project automatically rolls back to the previous successful runnning version.

## What it does:
- Deploys a Lambda function to perform web health checks with a simple initial message.
- Sets up a Synthetics Canary that simulates user visits every 5 minutes to monitor websites.
- Collects availability, latency, and response size metrics for multiple websites (e.g., Google, YouTube, Instagram).
- Collects memory, invocations, and duration metrics for lambdas
- Publishes metrics to CloudWatch and displays results on dashboards.
- Configures alarms for metric thresholds (availability <1, high latency, abnormal response size, high memory, low invocations, high duration).
- Sends SNS email notifications to DevOps engineers when alarms are triggered.
- Stores alarmed metric data in DynamoDB for auditing and historical tracking.
- Centralizes configuration values (URLs, thresholds, metric names) for easy maintenance and scalability.
- Uses a pipeline to performs unit, functional, and integration tests before project is fully sucessfully deployed
- Rolls back to previous working version if memory, invocations, and duration fails.


## Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the pipeline which will run unit, functional, and integration tests to check if the application is ready to run.

WH Lambda:
- Once the pipeline is sucessfully deployed go to the lambda website called application stack.
- Once on the lambda application stack website your code will appear in a function, and once you make a test,
it will test the websites and print out the results of each metric at the time of testing.
- After testing, go to the Cloudwatch dashboard and you will see three graphs each representing a metric, with real time readings on the metrics of each website.
- SNS:
    - After deploying stack file, it will automatically send an email to the DevOps Engineer if an alarm has been triggered.
    - In the email you can click on a link that will take you to view the alarm in the AWS Management Console.
    - After clicking the link it will show you the alarm dashboard
- DB Lambda:
    - Go to DBLambda on the lambda website, then go to tables where you can see your table that you created in the stack.
    - Click on explore table options, and scroll down until you get items returned, in this section you should see the metric that trigggered the alarm and its details such as:
        - Alarm Description
        - Alarm Name
        - Dimensions
        - Metric Name
        - New State Reason
        - Timestamp

CRUD Lambda:
- Once the pipeline is sucessfully deployed go to the lambda website called CRUD.
- On the CRUD website scroll down to the API gateway, and under Triggers select on of the titles (API Gateway: CrawlerTargetAPI) depending on Put, Get, Post
- - Go to resources and click on Either Put, get, Post, delete. Then go to the test section
- input the data in the body section in this format, then press test:
{
  "id": "target1",
  "name": "Example Target",
  "url": "https://example.com"
}
- Then go to stages and copy the link in targets to confirm if the action is done

- DB Lambda:
    - Go to DBLambda on the lambda website, then go to tables where you can see your table that you created in the stack.
    - Click on explore table options, and scroll down until you get items returned, in this section it should show the website data in the format above.


## Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.
    - Email notifications via SNS, ensure that only the DevOps engineer receives alerts for triggered metrics, reducing the risk of sensitive information being missed or exposed.
    - AWS IAM roles and policies control Lambda and DynamoDB access, ensuring that only authorized functions and users can read/write metric data.
    - Data storage in DynamoDB is secure and encrypted at rest by AWS, protecting sensitive monitoring information.

- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0).
    - Response size metric allows monitoring of abnormal increases/decreases in webpage content size that may indicate outages, errors, or changes.
    - Memory metric allows performance monitoring if the website takes up more memory than required, to prevent the servers becoming slow or unresponsive.
    - The metrics are checked every minuete to provide more data points to capture and display on the graphs.
    - It is scalable through the contants.py file which is used to insert as many websites links as needed to perform metrics on, and can carry over to other files.

- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails or exceeds metric thresholds, an email is sent to the DevOps engineer with details of the triggered metric.
    - Alarm emails include a link to the CloudWatch dashboard for the specific metric and website.
    - Alarm details are also stored in DynamoDB, ensuring a durable record of all events for future reference or audits.

- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.
    - Alarm emails include direct links to the alarm in the AWS Management Console for quick access and investigation.

## Future Improvements:
- Resolve issue with auto rollback not working, due to S3 bucket
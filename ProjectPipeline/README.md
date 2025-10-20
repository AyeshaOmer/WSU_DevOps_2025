
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

# Read Me File

## Overview
### Project 1:
The project uses AWS services to monitor website health. It is deployed through a pipline which allows for project to be properly tested before deployment. Checking through unit, functional, and integration tests. Once these tests are sucessfull, the project is properly deployed and is able to perform with the bellow features.

This project uses AWS Lambda and a Synthetics Canary, deployed via AWS CDK (Python), to monitor external websites by tracking availability, latency, response size, and memory metrics. The Canary simulates real user visits every 5 minutes, while Lambda collects metrics and publishes them to CloudWatch dashboards. 

Alarms are configured to alert users if availability drops below 1, latency is high, or response size is abnormal. SNS sends email notifications to DevOps engineers when alarms are triggered, and the alarmed metric data is logged in DynamoDB. 

To extend on the new metrics memory, invocations, and duration metrics, they have been included to monitor the lambdas, with their metrics uploaded to cloudwatch. The alarms are configured to activate if the memory exceeds 90% usage, the invocations captured by the lambda function is not invoked, and the lambda duration does not exceed 5 minuetes. SNS sends email notifiactions to DevOps engineres when alarms are triggered, the alarmed metric is logged into DynamoDB, and the project automatically rolls back to the previous successful runnning version.

### Project 2:
This project uses AWS services to build a public CRUD API Gateway endpoint for the web crawler to create/read/update/delete the target list containing the list of websites/webpages to crawl.

The targeted list of websites appear in the DynamoDB database, where the user can implement CRUD REST commands on the entries.

There are also tests to cover the CRUD operations, and dynamoDB read/write time.

## What it does:
- Deploys a Lambda function to perform web health checks with a simple initial message.
- Sets up a Synthetics Canary that simulates user visits every 5 minutes to monitor websites.
- Collects availability, latency, and response size metrics for multiple websites (e.g., Google, YouTube, Instagram).
- Collects memory, invocations, and duration metrics for lambdas
- Publishes metrics to CloudWatch and displays results on dashboards.
- Configures alarms for metric thresholds (availability <1, high latency, abnormal response size, high memory, low invocations, high duration).
- Sends SNS email notifications to DevOps engineers when alarms are triggered.
- Stores alarmed metric data in DynamoDB for auditing and historical tracking.
- Centralises configuration values (URLs, thresholds, metric names) for easy maintenance and scalability.
- Uses a pipeline to performs unit, functional, and integration tests before project is fully sucessfully deployed
- Rolls back to previous working version if memory, invocations, and duration metrics fails, or if the unit, functional, or integration tests fail.

- Builds a API Gateway for the web crawler to create/read/update/delete the target list containing the list of websites/webpages to crawl.
- Interact with the database to implement CRUD REST commands on entries.
- Test the CRUD REST commands, and dynamoDB read/write time.


## Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the pipeline which will run unit, functional, and integration tests to check if the application is ready to run.

### Project 1: Web Health Monitoring
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

## Project 2: CRUD Lambda
CRUD Lambda:
- Once the pipeline is sucessfully deployed go to the lambda website called CRUD.
- On the CRUD website scroll down to the API gateway, and under Triggers select one of the titles (API Gateway: CrawlerTargetAPI) depending on Put, Get, Post, Delete
- - Go to resources and click on either Put, Get, Post, Delete. Then go to the test section
- Input the website data in the body section in this format, then press test:
{
  "id": "target1",
  "name": "Example Target",
  "url": "https://example.com"
}
- Then go to stages, click on either Put, Get, Post, Delete, and copy the link in /targets to confirm if the action is done
- You can also see this in the 'TargetListTable' on DynamoDB


## Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.
    - Email notifications via SNS, ensure that only the DevOps engineer receives alerts for triggered metrics, reducing the risk of sensitive information being missed or exposed.
    - AWS IAM roles and policies control Lambda and DynamoDB access, ensuring that only authorized functions and users can read/write metric data.
    - Data storage in DynamoDB is secure and encrypted at rest by AWS, protecting sensitive monitoring information.
    - The CRUD API follows secure RESTful API practices, restricting public access to authorized methods and validating request data before performing any database operations.
    - AWS API Gateway adds an additional security layer, supporting HTTPS endpoints and input validation to prevent malformed requests or injection attacks.

- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0).
    - Response size metric allows monitoring of abnormal increases/decreases in webpage content size that may indicate outages, errors, or changes.
    - The metrics are checked every minuete to provide more data points to capture and display on the graphs.
    - It is scalable through the contants.py file which is used to insert as many websites links as needed to perform metrics on, and can carry over to other files.
    - Memory metric allows performance monitoring if the website takes up more than 90% of memory, to prevent the servers becoming slow or unresponsive.
    - Duration metric allows to check if the lambdas run longer than 5 minuetes, to detect potential performance bottlenecks.
    - Invocations metric checks if the lambda has runned at all, to check for issues in regard to deployment or IAM permission issues.
    - For the CRUD API, DynamoDB’s auto-scaling capability ensures high performance and fast read/write operations even as data volume grows.
    - API Gateway and Lambda functions use on-demand scaling, automatically adjusting capacity to handle fluctuating traffic without manual intervention.

- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails or exceeds metric thresholds, an email is sent to the DevOps engineer with details of the triggered metric.
    - Alarm emails include a link to the CloudWatch dashboard for the specific metric and website.
    - Alarm details are also stored in DynamoDB, ensuring a durable record of all events for future reference or audits.
    - Pipeline ensures that the code in the application is tested before deployment.
    - Automatic rollback ensures that if the pipeline has an issue in deployment, it will revert back to the previous sucessful version, until the new version is fixed.
    - DynamoDB has high availability which ensures CRUD operations remain reliable even under high load, with automatic replication across multiple availability zones.

- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.
    - Alarm emails include direct links to the alarm in the AWS Management Console for quick access and investigation.
    - The CRUD API Gateway provides a simple REST interface that can be tested directly through the AWS console or integrated with other systems such as a web crawler or frontend dashboard.

## Future Improvements:
- Resolve issue with auto rollback not working, due to S3 bucket
- Convert unit tests to alpha stage, functional tests to beta stage, integration tests to gamma stage, and add prod stage for manual deployment
- Resolve issue with manual deployment
- Add integration tests for project 1 (application), and project 2 (CRUD)

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
$ python -m venv .venv
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

**Reference**
lambda construction library: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
Scheduler Construct Library: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html


**Changelog**
Sunday 3 Aug:
    - Create the lambda function in phuoc_tai_tran_lambda_stack.py to handle ObtainMetric.py
    - Create ObtainMetrics.py to collect 3 metrics from 3 websites 
    - Create the removal policy for the lambda function
    - Create schedule to trigger lambda function every 5 minutes

Monday 11 Aug:
    - Create publish_metric.py to publish data to AWS cloudwatch

Tuesday 26 Aug:
    - Create iam policy to access the service-role/AWSLambdaBasicExecutionRole, 
                                      service-role/AWSLambdaVPCAccessExecutionRole,
                                      AmazonDynamoDBFullAccess,
                                      AmazonSNSFullAccess,
                                      CloudWatchFullAccess
    - Create dashboard widget in stack.py
    - Create alarm for availability and latency
    - Progress to trigger SNS 
    - Progress to send notification to SNS subscription email
    - Create DBlambda.py to insert alarm notification into dynamoDB
    - Place the remove policy at the end of the code - done
    - Create a constrant globally URLs - done
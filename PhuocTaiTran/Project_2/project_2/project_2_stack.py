from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class Project2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for web crawler targets
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        crawler_targets_table = dynamodb.Table(
            self, "CrawlerTargetsTable",
            table_name=f"crawler-targets-{self.account}-{self.region}",
            partition_key=dynamodb.Attribute(
                name="target_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Add Global Secondary Index for status-based queries
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.add_global_secondary_index
        crawler_targets_table.add_global_secondary_index(
            index_name="status-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Lambda function for CRUD API operations
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        crud_api_lambda = _lambda.Function(
            self, "CrudApiLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="crud_api_handler.lambda_handler", # call the crud_api_handler.py file and its lambda_handler function
            code=_lambda.Code.from_asset("Module"), # point to the folder where the lambda code is
            timeout=Duration.seconds(30), # set timeout to 30 seconds
            environment={
                "DYNAMODB_TABLE_NAME": crawler_targets_table.table_name
            }
        )

        # Grant Lambda permissions to access DynamoDB table
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_read_write_data
        crawler_targets_table.grant_read_write_data(crud_api_lambda)

        # REST API Gateway for CRUD operations
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html
        crud_api = apigw.RestApi(
            self, "CrudApi",
            rest_api_name="Web Crawler CRUD API",
            description="RESTful API for managing web crawler targets",
            # Enable CORS for all origins (CORS: Cross-Origin Resource Sharing)
            # Allow access from any domain for testing purposes
            #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Cors.html
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"]
            ),
            #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/EndpointType.html
            endpoint_types=[apigw.EndpointType.REGIONAL]
        )

        # Lambda integration for API Gateway
        # Integrates an AWS Lambda function to an API Gateway method.
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
        lambda_integration = apigw.LambdaIntegration(
            crud_api_lambda,
            proxy=True,
            integration_responses=[
                apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                )
            ]
        )

        # /targets resource for collection operations
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html
        targets_resource = crud_api.root.add_resource("targets")
        
        # POST /targets - Create new target website
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Method.html
        targets_resource.add_method(
            "POST", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    # Return 201 Created on successful creation
                    status_code="201",
                    # Enable CORS headers in the response
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )
        
        # GET /targets - List targets with optional filtering
        targets_resource.add_method(
            "GET", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    # Return 200 OK on successful retrieval
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # /targets/{target_id} resource for individual target operations
        target_resource = targets_resource.add_resource("{target_id}")
        
        # GET /targets/{target_id} - Get specific target with filtering
        target_resource.add_method(
            "GET", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )
        
        # PUT /targets/{target_id} - Update target
        target_resource.add_method(
            "PUT", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )
        
        # DELETE /targets/{target_id} - Delete target
        target_resource.add_method(
            "DELETE", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="204",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # CloudFormation outputs
        #  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/CfnOutput.html
        CfnOutput(
            self, "ApiGatewayUrl",
            value=crud_api.url,
            description="URL of the CRUD API Gateway"
        )
        
        CfnOutput(
            self, "DynamoDBTableName",
            value=crawler_targets_table.table_name,
            description="Name of the DynamoDB table for crawler targets"
        )
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config_table: dynamodb.Table = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use provided config table
        self.config_table = config_table

        # Create API Lambda functions
        # Lambda function for CRUD operations on website configurations
        # reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        self.fn_CRUD = _lambda.Function(
            self, "WebsiteCrudLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("modules/api"),
            handler="api_handler.handler",
            timeout=Duration.minutes(1),
            environment={
                "CONFIG_TABLE": config_table.table_name
            }
        )

        # Grant DynamoDB permissions
        # Grant read/write permissions to the config table
        config_table.grant_read_write_data(self.fn_CRUD)

        # Create API Gateway
        # reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html
        api = apigw.RestApi(
            self, "WebsiteManagementApi",
            rest_api_name="Website Management API",
            description="API for CRUD websites",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )

        # Create API resources and methods
        # Resource for /websites
        # reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html
        websites = api.root.add_resource("websites")
        
        # GET /websites (List all websites)
        # reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
        websites.add_method(
            "GET",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # POST /websites (Create new website)
        websites.add_method(
            "POST",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # Single website operations
        website = websites.add_resource("{websiteId}")
        
        # GET /websites/{websiteId}
        website.add_method(
            "GET",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # PUT /websites/{websiteId}
        website.add_method(
            "PUT",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # DELETE /websites/{websiteId}
        website.add_method(
            "DELETE",
            apigw.LambdaIntegration(self.fn_CRUD)
        )
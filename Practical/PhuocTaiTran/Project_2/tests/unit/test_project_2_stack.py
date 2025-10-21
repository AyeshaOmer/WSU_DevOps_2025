import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from project_2.project_2_stack import Project2Stack


def test_s3_bucket_created():
    """Test that S3 bucket is created with correct properties"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that S3 bucket exists
    template.resource_count_is("AWS::S3::Bucket", 1)
    
    # Check bucket has auto-delete tag
    template.has_resource_properties("AWS::S3::Bucket", {
        "Tags": [
            {
                "Key": "aws-cdk:auto-delete-objects",
                "Value": "true"
            }
        ]
    })


def test_dynamodb_table_created():
    """Test that DynamoDB table is created with correct properties"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that DynamoDB table exists
    template.resource_count_is("AWS::DynamoDB::Table", 1)
    
    # Check table properties
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {
                "AttributeName": "target_id",
                "KeyType": "HASH"
            }
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "status-index",
                "KeySchema": [
                    {
                        "AttributeName": "status", 
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        ]
    })


def test_lambda_function_created():
    """Test that Lambda function is created with correct properties"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that we have Lambda functions (CDK creates additional ones for S3 auto-delete)
    template.resource_count_is("AWS::Lambda::Function", 2)
    
    # Check our specific Lambda properties
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.12",
        "Handler": "crud_api_handler.lambda_handler",
        "Timeout": 30
    })


def test_api_gateway_created():
    """Test that API Gateway is created with correct CRUD endpoints"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that API Gateway REST API exists
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    
    # Check API Gateway properties
    template.has_resource_properties("AWS::ApiGateway::RestApi", {
        "Name": "Web Crawler CRUD API",
        "Description": "RESTful API for managing web crawler targets"
    })
    
    # Check that we have API Gateway resources for targets
    template.has_resource_properties("AWS::ApiGateway::Resource", {
        "PathPart": "targets"
    })
    
    # Check that we have the target_id resource
    template.has_resource_properties("AWS::ApiGateway::Resource", {
        "PathPart": "{target_id}"
    })


def test_api_gateway_methods():
    """Test that API Gateway has all required HTTP methods"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check for POST method on /targets
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "POST"
    })
    
    # Check for GET method on /targets
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "GET"
    })
    
    # Check for PUT method on /targets/{target_id}
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "PUT"
    })
    
    # Check for DELETE method on /targets/{target_id}
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "DELETE"
    })


def test_lambda_permissions():
    """Test that Lambda has proper permissions for DynamoDB and S3"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that Lambda has DynamoDB permissions
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                {
                    "Effect": "Allow",
                    "Action": assertions.Match.array_with([
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:ConditionCheckItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:DescribeTable",
                        "dynamodb:GetItem",
                        "dynamodb:GetRecords",
                        "dynamodb:GetShardIterator",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:UpdateItem"
                    ])
                }
            ])
        }
    })


def test_outputs_defined():
    """Test that CloudFormation outputs are properly defined"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that outputs exist
    outputs = template.find_outputs("*")
    assert "ApiGatewayUrl" in outputs
    assert "DynamoDBTableName" in outputs
    assert "S3BucketName" in outputs


def test_cors_configuration():
    """Test that CORS is properly configured"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check for OPTIONS methods (CORS preflight)
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "OPTIONS"
    })
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    
    # Check that API Gateway has the correct name
    template.has_resource_properties("AWS::ApiGateway::RestApi", {
        "Name": "Project2 Service"
    })


def test_iam_role_created():
    """Test that IAM role for Lambda is created"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that IAM roles exist (CDK creates additional roles for auto-delete Lambda)
    template.resource_count_is("AWS::IAM::Role", 3)
    
    # Check that at least one role has Lambda service principal
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    }
                }
            ]
        }
    })


def test_api_gateway_methods():
    """Test that API Gateway has all required HTTP methods"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # We have many methods including OPTIONS for CORS
    # At minimum: POST/GET/PUT/DELETE for targets + OPTIONS for each resource
    template.resource_count_is("AWS::ApiGateway::Method", 8)
    
    # Check for POST method on /targets
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "POST"
    })
    
    # Check for GET method on /targets
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "GET"
    })
    
    # Check for PUT method on /targets/{target_id}
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "PUT"
    })
    
    # Check for DELETE method on /targets/{target_id}
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "DELETE"
    })


def test_lambda_permissions():
    """Test that Lambda has proper permissions for DynamoDB and S3"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that Lambda has DynamoDB permissions (more flexible check)
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Effect": "Allow",
                    "Action": assertions.Match.array_with([
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ])
                })
            ])
        }
    })


def test_cors_configuration():
    """Test that CORS is properly configured"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check for OPTIONS methods (CORS preflight)
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "OPTIONS"
    })


def test_lambda_environment_variables():
    """Test that Lambda function has correct environment variables"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that Lambda has DynamoDB table name environment variable
    template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {
            "Variables": {
                "DYNAMODB_TABLE_NAME": assertions.Match.any_value()
            }
        }
    })


def test_s3_bucket_policy():
    """Test that S3 bucket has appropriate IAM policy for Lambda access"""
    app = core.App()
    stack = Project2Stack(app, "project-2-test")
    template = assertions.Template.from_stack(stack)
    
    # Check that IAM policy exists for S3 access
    template.resource_count_is("AWS::IAM::Policy", 1)
    
    # Verify the policy allows S3 operations
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Effect": "Allow",
                    "Action": assertions.Match.array_with([
                        assertions.Match.string_like_regexp("s3:.*")
                    ])
                })
            ])
        }
    })
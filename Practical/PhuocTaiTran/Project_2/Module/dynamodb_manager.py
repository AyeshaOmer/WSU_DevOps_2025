"""
DynamoDB operations for Project 2 Web Crawler API
This module handles all database operations for managing crawler targets.

https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from botocore.exceptions import ClientError
from constants import (
    CRAWLER_TABLE_NAME, CRAWLER_TABLE_PK, CRAWLER_TABLE_GSI_NAME,
    HTTP_STATUS, ERROR_MESSAGES, TARGET_STATUS
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
# https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
dynamodb = boto3.resource('dynamodb')


class DynamoDBManager:
    """
    DynamoDB operations manager for web crawler targets.
    
    https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
    """
    
    def __init__(self, table_name: str = None):
        """
        Initialize DynamoDB manager.
        
        Args:
            table_name (str): Name of the DynamoDB table
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.table_name
        """
        self.table_name = table_name or CRAWLER_TABLE_NAME
        self.table = dynamodb.Table(self.table_name)
    
    def create_target(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new crawler target in DynamoDB.
        
        Args:
            target_data (Dict[str, Any]): Target data to create
            
        Returns:
            Dict[str, Any]: API response with created target data
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_write_data
        """
        try:
            # Check if target already exists
            existing_target = self.get_target(target_data["target_id"])
            if existing_target["statusCode"] == HTTP_STATUS["OK"]:
                return {
                    "statusCode": HTTP_STATUS["BAD_REQUEST"],
                    "body": {
                        "error": ERROR_MESSAGES["DUPLICATE_TARGET"],
                        "target_id": target_data["target_id"]
                    }
                }
            
            # Add timestamps
            current_time = datetime.utcnow().isoformat()
            target_data["created_at"] = current_time
            target_data["updated_at"] = current_time
            
            # Convert float values to Decimal for DynamoDB
            target_data = self._convert_floats_to_decimal(target_data)
            
            # Put item in DynamoDB
            response = self.table.put_item(Item=target_data)
            
            logger.info(f"Created target: {target_data['target_id']}")
            
            return {
                "statusCode": HTTP_STATUS["CREATED"],
                "body": {
                    "message": "Target created successfully",
                    "target": self._convert_decimal_to_float(target_data)
                }
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error creating target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "details": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error creating target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            }
    
    def get_target(self, target_id: str) -> Dict[str, Any]:
        """
        Retrieve a crawler target from DynamoDB.
        
        Args:
            target_id (str): ID of the target to retrieve
            
        Returns:
            Dict[str, Any]: API response with target data
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_read_data
        """
        try:
            response = self.table.get_item(
                Key={CRAWLER_TABLE_PK: target_id}
            )
            
            if 'Item' not in response:
                return {
                    "statusCode": HTTP_STATUS["NOT_FOUND"],
                    "body": {
                        "error": ERROR_MESSAGES["TARGET_NOT_FOUND"],
                        "target_id": target_id
                    }
                }
            
            target = self._convert_decimal_to_float(response['Item'])
            
            return {
                "statusCode": HTTP_STATUS["OK"],
                "body": {
                    "target": target
                }
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error retrieving target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "details": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error retrieving target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            }
    
    def update_target(self, target_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a crawler target in DynamoDB.
        
        Args:
            target_id (str): ID of the target to update
            update_data (Dict[str, Any]): Data to update
            
        Returns:
            Dict[str, Any]: API response with updated target data
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_read_write_data
        """
        try:
            # Check if target exists
            existing_target = self.get_target(target_id)
            if existing_target["statusCode"] != HTTP_STATUS["OK"]:
                return existing_target
            
            # Prepare update expression
            update_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Convert float values to Decimal
            update_data = self._convert_floats_to_decimal(update_data)
            
            # Build update expression
            for key, value in update_data.items():
                if key != CRAWLER_TABLE_PK:  # Don't update primary key
                    attr_name = f"#{key}"
                    attr_value = f":{key}"
                    update_expression_parts.append(f"{attr_name} = {attr_value}")
                    expression_attribute_names[attr_name] = key
                    expression_attribute_values[attr_value] = value
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            # Update item in DynamoDB
            response = self.table.update_item(
                Key={CRAWLER_TABLE_PK: target_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            
            updated_target = self._convert_decimal_to_float(response['Attributes'])
            
            logger.info(f"Updated target: {target_id}")
            
            return {
                "statusCode": HTTP_STATUS["OK"],
                "body": {
                    "message": "Target updated successfully",
                    "target": updated_target
                }
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error updating target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "details": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error updating target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            }
    
    def delete_target(self, target_id: str) -> Dict[str, Any]:
        """
        Delete a crawler target from DynamoDB.
        
        Args:
            target_id (str): ID of the target to delete
            
        Returns:
            Dict[str, Any]: API response
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_write_data
        """
        try:
            # Check if target exists
            existing_target = self.get_target(target_id)
            if existing_target["statusCode"] != HTTP_STATUS["OK"]:
                return existing_target
            
            # Delete item from DynamoDB
            response = self.table.delete_item(
                Key={CRAWLER_TABLE_PK: target_id},
                ReturnValues="ALL_OLD"
            )
            
            deleted_target = self._convert_decimal_to_float(response.get('Attributes', {}))
            
            logger.info(f"Deleted target: {target_id}")
            
            return {
                "statusCode": HTTP_STATUS["OK"],
                "body": {
                    "message": "Target deleted successfully",
                    "deleted_target": deleted_target
                }
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error deleting target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "details": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error deleting target: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            }
    
    def list_targets(self, status_filter: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        List crawler targets from DynamoDB.
        
        Args:
            status_filter (str): Filter by status
            limit (int): Maximum number of targets to return
            
        Returns:
            Dict[str, Any]: API response with list of targets
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/GlobalSecondaryIndex.html
        """
        try:
            targets = []
            
            if status_filter:
                # Use GSI to filter by status
                response = self.table.query(
                    IndexName=CRAWLER_TABLE_GSI_NAME,
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('status').eq(status_filter),
                    Limit=limit,
                    ScanIndexForward=False  # Sort by created_at in descending order
                )
                targets = response.get('Items', [])
            else:
                # Scan all targets
                response = self.table.scan(Limit=limit)
                targets = response.get('Items', [])
            
            # Convert Decimal to float for JSON serialization
            targets = [self._convert_decimal_to_float(target) for target in targets]
            
            return {
                "statusCode": HTTP_STATUS["OK"],
                "body": {
                    "targets": targets,
                    "count": len(targets)
                }
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error listing targets: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "details": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error listing targets: {e}")
            return {
                "statusCode": HTTP_STATUS["INTERNAL_ERROR"],
                "body": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            }
    
    def _convert_floats_to_decimal(self, data: Any) -> Any:
        """
        Convert float values to Decimal for DynamoDB storage.
        
        Args:
            data: Data to convert
            
        Returns:
            Data with floats converted to Decimal
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/AttributeType.html
        """
        if isinstance(data, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_floats_to_decimal(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        return data
    
    def _convert_decimal_to_float(self, data: Any) -> Any:
        """
        Convert Decimal values to float for JSON serialization.
        
        Args:
            data: Data to convert
            
        Returns:
            Data with Decimals converted to float
            
        https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/AttributeType.html
        """
        if isinstance(data, dict):
            return {key: self._convert_decimal_to_float(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimal_to_float(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        return data
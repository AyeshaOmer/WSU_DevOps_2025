"""
Validation utilities for Project 2 Web Crawler API
This module provides validation functions for API inputs and data integrity.

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from constants import URL_PATTERN, TARGET_ID_PATTERN, TARGET_STATUS, ERROR_MESSAGES


def validate_url(url: str) -> bool:
    """
    Validate URL format using regex pattern.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL, False otherwise
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
    """
    if not url or not isinstance(url, str):
        return False
    return bool(re.match(URL_PATTERN, url))


def validate_target_id(target_id: str) -> bool:
    """
    Validate target ID format.
    
    Args:
        target_id (str): Target ID to validate
        
    Returns:
        bool: True if valid target ID, False otherwise
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/README.html
    """
    if not target_id or not isinstance(target_id, str):
        return False
    return bool(re.match(TARGET_ID_PATTERN, target_id))


def validate_status(status: str) -> bool:
    """
    Validate target status value.
    
    Args:
        status (str): Status to validate
        
    Returns:
        bool: True if valid status, False otherwise
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/README.html
    """
    return status in TARGET_STATUS.values()


def validate_create_target_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate create target request data.
    Auto-generates missing fields from URL if only URL is provided.
    
    Args:
        data (Dict[str, Any]): Request data to validate
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function.add_environment
    """
    # If only URL is provided, auto-generate other fields
    if "url" in data and data["url"] and len(data) == 1:
        from urllib.parse import urlparse
        import re
        
        url = data["url"]
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        
        # Auto-generate target_id from domain
        target_id = re.sub(r'[^a-zA-Z0-9-]', '-', domain.lower())
        target_id = re.sub(r'-+', '-', target_id).strip('-')
        
        # Auto-generate name from domain
        name = domain.replace('.com', '').replace('.org', '').replace('.net', '')
        name = name.replace('.', ' ').title()
        
        # Update data with auto-generated fields
        data["target_id"] = target_id
        data["name"] = name
        data["description"] = f"Auto-generated target for {domain}"
    
    # Check required fields
    required_fields = ["target_id", "url", "name"]
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"{ERROR_MESSAGES['MISSING_REQUIRED_FIELD']}: {field}"
    
    # Validate target_id
    if not validate_target_id(data["target_id"]):
        return False, ERROR_MESSAGES["INVALID_TARGET_ID"]
    
    # Validate URL
    if not validate_url(data["url"]):
        return False, ERROR_MESSAGES["INVALID_URL"]
    
    # Validate status if provided
    if "status" in data and not validate_status(data["status"]):
        return False, ERROR_MESSAGES["INVALID_STATUS"]
    
    return True, None


def validate_update_target_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate update target request data.
    Allows partial updates - user can provide only the fields they want to update.
    
    Args:
        data (Dict[str, Any]): Request data to validate
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
    """
    # Check if at least one updatable field is provided
    updatable_fields = ["url", "name", "description", "status", "crawl_config"]
    provided_fields = [field for field in updatable_fields if field in data and data[field]]
    
    if not provided_fields:
        return False, "At least one updatable field (name, url, description, status, crawl_config) must be provided"
    
    # Validate URL if provided and not empty
    if "url" in data and data["url"] and not validate_url(data["url"]):
        return False, ERROR_MESSAGES["INVALID_URL"]
    
    # Validate status if provided and not empty
    if "status" in data and data["status"] and not validate_status(data["status"]):
        return False, ERROR_MESSAGES["INVALID_STATUS"]
    
    # Remove empty or None fields from data (so they won't be updated)
    fields_to_remove = []
    for field in data:
        if data[field] is None or data[field] == "":
            fields_to_remove.append(field)
    
    for field in fields_to_remove:
        del data[field]
    
    return True, None


def sanitize_target_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and prepare target data for database storage.
    
    Args:
        data (Dict[str, Any]): Raw target data
        
    Returns:
        Dict[str, Any]: Sanitized target data
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Attribute.html
    """
    sanitized = {}
    
    # Copy allowed fields
    allowed_fields = [
        "target_id", "url", "name", "description", 
        "status", "crawl_config", "tags"
    ]
    
    for field in allowed_fields:
        if field in data:
            sanitized[field] = data[field]
    
    # Add timestamps
    current_time = datetime.utcnow().isoformat()
    sanitized["updated_at"] = current_time
    
    if "created_at" not in sanitized:
        sanitized["created_at"] = current_time
    
    # Set default status if not provided
    if "status" not in sanitized:
        sanitized["status"] = TARGET_STATUS["PENDING"]
    
    return sanitized


def validate_query_parameters(params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate query parameters for list operations.
    
    Args:
        params (Dict[str, Any]): Query parameters
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
        
    Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RequestValidator.html
    """
    # Validate status filter if provided
    if "status" in params and not validate_status(params["status"]):
        return False, ERROR_MESSAGES["INVALID_STATUS"]
    
    # Validate limit parameter
    if "limit" in params:
        try:
            limit = int(params["limit"])
            if limit < 1 or limit > 100:
                return False, "Limit must be between 1 and 100"
        except ValueError:
            return False, "Limit must be a valid integer"
    
    return True, None
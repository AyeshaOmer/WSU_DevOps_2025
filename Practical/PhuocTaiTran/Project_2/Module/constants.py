"""
Configuration constants for Project 2 Web Crawler API
This file contains all the configuration settings and constants used throughout the project.

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.html
"""

# DynamoDB Configuration
CRAWLER_TABLE_NAME = "WebCrawlerTargets"
CRAWLER_TABLE_PK = "target_id"
CRAWLER_TABLE_GSI_NAME = "StatusIndex"
CRAWLER_TABLE_GSI_PK = "status"
CRAWLER_TABLE_GSI_SK = "created_at"

# API Gateway Configuration
API_NAME = "WebCrawlerAPI"
API_DESCRIPTION = "RESTful API for managing web crawler target URLs"
API_VERSION = "v1"

# Lambda Configuration
LAMBDA_TIMEOUT_SECONDS = 30
LAMBDA_MEMORY_MB = 256
LAMBDA_RUNTIME = "python3.12"

# CloudWatch Configuration
CLOUDWATCH_NAMESPACE = "WebCrawler/API"
CLOUDWATCH_LOG_RETENTION_DAYS = 30

# Target URL Status Values
TARGET_STATUS = {
    "ACTIVE": "active",
    "INACTIVE": "inactive", 
    "PENDING": "pending",
    "ERROR": "error",
    "COMPLETED": "completed"
}

# HTTP Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "INTERNAL_ERROR": 500
}

# Response Headers for CORS
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
}

# Default crawl configuration
DEFAULT_CRAWL_CONFIG = {
    "depth": 1,
    "delay_seconds": 1,
    "timeout_seconds": 30,
    "user_agent": "WebCrawler/1.0",
    "follow_redirects": True,
    "max_pages": 100
}

# Validation patterns
URL_PATTERN = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
TARGET_ID_PATTERN = r"^[a-zA-Z0-9-_]{1,50}$"

# Error messages
ERROR_MESSAGES = {
    "INVALID_URL": "Invalid URL format",
    "INVALID_TARGET_ID": "Invalid target ID format",
    "TARGET_NOT_FOUND": "Target not found",
    "DUPLICATE_TARGET": "Target already exists",
    "MISSING_REQUIRED_FIELD": "Missing required field",
    "INVALID_STATUS": "Invalid status value",
    "DATABASE_ERROR": "Database operation failed",
    "VALIDATION_ERROR": "Input validation failed"
}
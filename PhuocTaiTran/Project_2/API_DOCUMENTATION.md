"""
API Documentation for Web Crawler CRUD API
RESTful API for managing web crawler target websites/webpages.

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/README.html
"""

# Web Crawler CRUD API Documentation

## Overview

The Web Crawler CRUD API provides a RESTful interface for managing target websites and webpages that will be crawled. This API is built using AWS API Gateway, Lambda, and DynamoDB for scalable and serverless operations.

**Base URL:** `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

## Authentication

Currently, the API is public and does not require authentication. In production environments, consider implementing:
- API Key authentication
- AWS IAM authentication
- JWT token authentication

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/AuthorizationType.html

## Data Model

### Target Object

```json
{
  "target_id": "string",           // Unique identifier (auto-generated)
  "url": "string",                 // Website/webpage URL (required)
  "title": "string",               // Display title (optional)
  "description": "string",         // Description of the target (optional)
  "status": "string",              // Status: "active" | "inactive" | "pending" | "error"
  "priority": "number",            // Priority level (1-5, 1 = highest)
  "tags": ["string"],              // Array of tags for categorization
  "crawl_frequency": "number",     // Hours between crawls (default: 24)
  "last_crawled": "string",        // ISO timestamp of last crawl
  "next_crawl": "string",          // ISO timestamp of next scheduled crawl
  "created_at": "string",          // ISO timestamp of creation
  "updated_at": "string"           // ISO timestamp of last update
}
```

### Status Values

- `active`: Target is enabled for crawling
- `inactive`: Target is disabled
- `pending`: Target is queued for first crawl
- `error`: Target had errors during last crawl

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/AttributeType.html

## API Endpoints

### 1. Create Target

**POST** `/targets`

Creates a new crawler target.

#### Request Body

```json
{
  "url": "https://example.com",
  "title": "Example Website",
  "description": "Sample website for testing",
  "priority": 1,
  "tags": ["test", "example"],
  "crawl_frequency": 24
}
```

#### Response

**Status: 201 Created**
```json
{
  "target_id": "target-abc123",
  "url": "https://example.com",
  "title": "Example Website",
  "description": "Sample website for testing",
  "status": "pending",
  "priority": 1,
  "tags": ["test", "example"],
  "crawl_frequency": 24,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "next_crawl": "2024-01-16T10:30:00Z"
}
```

#### Error Responses

**Status: 400 Bad Request**
```json
{
  "error": "URL is required"
}
```

### 2. Get Target

**GET** `/targets/{target_id}`

Retrieves a specific crawler target by ID.

#### Path Parameters

- `target_id` (string, required): Unique identifier of the target

#### Response

**Status: 200 OK**
```json
{
  "target_id": "target-abc123",
  "url": "https://example.com",
  "title": "Example Website",
  "status": "active",
  "priority": 1,
  "last_crawled": "2024-01-15T12:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

#### Error Responses

**Status: 404 Not Found**
```json
{
  "error": "Target not found"
}
```

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Resource.html

### 3. Update Target

**PUT** `/targets/{target_id}`

Updates an existing crawler target.

#### Path Parameters

- `target_id` (string, required): Unique identifier of the target

#### Request Body

```json
{
  "title": "Updated Website Title",
  "description": "Updated description",
  "status": "active",
  "priority": 2,
  "crawl_frequency": 12
}
```

#### Response

**Status: 200 OK**
```json
{
  "target_id": "target-abc123",
  "url": "https://example.com",
  "title": "Updated Website Title",
  "description": "Updated description",
  "status": "active",
  "priority": 2,
  "crawl_frequency": 12,
  "updated_at": "2024-01-15T14:30:00Z"
}
```

#### Error Responses

**Status: 404 Not Found**
```json
{
  "error": "Target not found"
}
```

### 4. Delete Target

**DELETE** `/targets/{target_id}`

Deletes a crawler target.

#### Path Parameters

- `target_id` (string, required): Unique identifier of the target

#### Response

**Status: 204 No Content**

No response body.

#### Error Responses

**Status: 404 Not Found**
```json
{
  "error": "Target not found"
}
```

### 5. List Targets

**GET** `/targets`

Retrieves a list of crawler targets with optional filtering.

#### Query Parameters

- `status` (string, optional): Filter by status (`active`, `inactive`, `pending`, `error`)
- `limit` (number, optional): Maximum number of results (default: 50, max: 100)
- `offset` (string, optional): Pagination token for next page

#### Response

**Status: 200 OK**
```json
{
  "targets": [
    {
      "target_id": "target-abc123",
      "url": "https://example.com",
      "title": "Example Website",
      "status": "active",
      "priority": 1,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "target_id": "target-def456",
      "url": "https://test.com",
      "title": "Test Site",
      "status": "pending",
      "priority": 2,
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "count": 2,
  "has_more": false,
  "next_offset": null
}
```

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/GlobalSecondaryIndex.html

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:

- **Access-Control-Allow-Origin:** `*`
- **Access-Control-Allow-Methods:** `GET, POST, PUT, DELETE, OPTIONS`
- **Access-Control-Allow-Headers:** `Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token`

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Cors.html

## Error Handling

All error responses follow a consistent format:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data or parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default limit:** 1000 requests per hour per IP
- **Burst limit:** 100 requests per minute

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/ThrottleSettings.html

## Examples

### Create a new target

```bash
curl -X POST https://api-id.execute-api.region.amazonaws.com/prod/targets \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.example.com",
    "title": "Example News Site",
    "description": "Daily news website",
    "priority": 1,
    "tags": ["news", "daily"],
    "crawl_frequency": 6
  }'
```

### List active targets

```bash
curl "https://api-id.execute-api.region.amazonaws.com/prod/targets?status=active&limit=10"
```

### Update a target

```bash
curl -X PUT https://api-id.execute-api.region.amazonaws.com/prod/targets/target-abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "inactive",
    "description": "Temporarily disabled for maintenance"
  }'
```

### Delete a target

```bash
curl -X DELETE https://api-id.execute-api.region.amazonaws.com/prod/targets/target-abc123
```

## SDK Examples

### Python with boto3

```python
import boto3
import requests
import json

# Using requests library
api_url = "https://api-id.execute-api.region.amazonaws.com/prod"

# Create target
response = requests.post(f"{api_url}/targets", 
                        json={
                            "url": "https://example.com",
                            "title": "Example Site",
                            "priority": 1
                        })

if response.status_code == 201:
    target = response.json()
    print(f"Created target: {target['target_id']}")
```

### JavaScript with fetch

```javascript
const apiUrl = 'https://api-id.execute-api.region.amazonaws.com/prod';

// Create target
async function createTarget(targetData) {
  try {
    const response = await fetch(`${apiUrl}/targets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(targetData)
    });
    
    if (response.ok) {
      const target = await response.json();
      console.log('Created target:', target.target_id);
      return target;
    } else {
      const error = await response.json();
      console.error('Error:', error.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}

// Usage
createTarget({
  url: 'https://example.com',
  title: 'Example Site',
  priority: 1
});
```

## Monitoring and Logging

The API provides comprehensive monitoring through AWS CloudWatch:

- **Request/Response metrics:** Request count, latency, error rates
- **Lambda metrics:** Duration, memory usage, cold starts
- **DynamoDB metrics:** Read/write capacity, throttling
- **Custom metrics:** Crawl success rates, target health

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/README.html

## Security Considerations

1. **Input Validation:** All inputs are validated and sanitized
2. **URL Validation:** URLs are validated for format and security
3. **Rate Limiting:** Prevents API abuse
4. **CORS Policy:** Configured for security
5. **IAM Roles:** Least privilege access for Lambda functions

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/README.html

## Infrastructure

The API is built using:

- **AWS API Gateway:** RESTful API endpoints
- **AWS Lambda:** Serverless compute (Python 3.12)
- **Amazon DynamoDB:** NoSQL database with GSI
- **AWS CloudWatch:** Monitoring and logging
- **AWS CDK:** Infrastructure as Code

Reference: https://docs.aws.amazon.com/cdk/api/v2/python/index.html
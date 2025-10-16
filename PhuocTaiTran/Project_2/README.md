# Project 2: Web Crawler CRUD API

A comprehensive RESTful API built with AWS CDK for managing web crawler target websites and webpages. This project demonstrates modern serverless architecture using AWS Lambda, API Gateway, and DynamoDB.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Client Apps   │    │   API Gateway    │    │  Lambda Function │    │    DynamoDB      │
│                 │───▶│   (REST API)     │───▶│  (CRUD Handler)  │───▶│  (Target Store)  │
│ Web/Mobile/CLI  │    │  /targets/*      │    │   Python 3.12   │    │   NoSQL Database │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
                                │                        │                        │
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
                       │   CloudWatch     │    │      S3         │    │  Global Secondary│
                       │  (Monitoring)    │    │  (Data Storage) │    │     Index        │
                       │   Logs/Metrics   │    │   File Storage  │    │ (Status Queries) │
                       └──────────────────┘    └─────────────────┘    └──────────────────┘
```

## 🚀 Features

### Core Functionality
- **Full CRUD Operations**: Create, Read, Update, Delete crawler targets
- **RESTful Design**: Standard HTTP methods with proper status codes
- **Data Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Robust error handling with descriptive messages
- **CORS Support**: Cross-origin resource sharing for web applications

### Technical Features
- **Serverless Architecture**: AWS Lambda with automatic scaling
- **NoSQL Database**: DynamoDB with Global Secondary Index for fast queries
- **Infrastructure as Code**: Complete AWS CDK implementation
- **Testing Suite**: Comprehensive unit tests for all components
- **Monitoring**: CloudWatch logs and metrics integration
- **Documentation**: Complete API documentation with examples

## 📋 API Endpoints

### Base URL
```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/targets` | Create a new crawler target |
| `GET` | `/targets` | List all targets (with optional filtering) |
| `GET` | `/targets/{id}` | Get a specific target by ID |
| `PUT` | `/targets/{id}` | Update an existing target |
| `DELETE` | `/targets/{id}` | Delete a target |

## 🛠️ Technology Stack

### AWS Services
- **AWS CDK v2.160.0**: Infrastructure as Code
- **AWS Lambda**: Serverless compute (Python 3.12)
- **Amazon API Gateway**: RESTful API management
- **Amazon DynamoDB**: NoSQL database with GSI
- **Amazon S3**: File storage for crawler data
- **AWS CloudWatch**: Monitoring and logging
- **AWS IAM**: Security and access control

### Development Tools
- **Python 3.12**: Programming language
- **pytest**: Testing framework
- **moto**: AWS service mocking for tests
- **boto3**: AWS SDK for Python

## 📁 Project Structure

```
Project_2/
├── Module/                          # Lambda function code
│   ├── constants.py                 # Configuration constants
│   ├── validators.py                # Input validation functions
│   ├── dynamodb_manager.py          # DynamoDB CRUD operations
│   └── crud_api_handler.py          # Main Lambda handler
├── project_2/                       # CDK infrastructure code
│   └── project_2_stack.py           # Stack definition
├── tests/                           # Test suites
│   ├── unit/
│   │   └── test_project_2_stack.py  # CDK stack tests
│   ├── test_crud_api_handler.py     # API handler tests
│   └── test_dynamodb_manager.py     # Database tests
├── app.py                           # CDK app entry point
├── cdk.json                         # CDK configuration
├── requirements.txt                 # Python dependencies
├── API_DOCUMENTATION.md             # Detailed API docs
└── README.md                        # This file
```

## 🔧 Setup and Installation

### Prerequisites
- Python 3.12 or higher
- Node.js 18.x or higher
- AWS CLI configured
- AWS CDK v2 installed globally

### Installation Steps

1. **Clone and navigate to project**
   ```bash
   cd Project_2
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install AWS CDK (if not already installed)**
   ```bash
   npm install -g aws-cdk
   ```

5. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap
   ```

## 🚀 Deployment

### Deploy the Stack
```bash
# Synthesize CloudFormation template (optional)
cdk synth

# Deploy to AWS
cdk deploy

# View outputs (API URL, table name, etc.)
cdk deploy --outputs-file outputs.json
```

## 🧪 Testing

### Run All Tests
```bash
# Run CDK stack tests
pytest tests/unit/ -v

# Run Lambda function tests
pytest tests/test_crud_api_handler.py -v

# Run DynamoDB tests
pytest tests/test_dynamodb_manager.py -v

# Run all tests with coverage
pytest --cov=Module tests/ -v
```

## 📊 Data Model

### Target Object Schema
```json
{
  "target_id": "string",           // Auto-generated unique ID
  "url": "string",                 // Website URL (required)
  "title": "string",               // Display title
  "description": "string",         // Description
  "status": "string",              // active|inactive|pending|error
  "priority": "number",            // Priority level (1-5)
  "tags": ["string"],              // Category tags
  "crawl_frequency": "number",     // Hours between crawls
  "created_at": "string",          // ISO timestamp
  "updated_at": "string"           // ISO timestamp
}
```

## 🎯 Usage Examples

### Create a new target
```bash
curl -X POST https://api-url/targets \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "title": "Example Website",
    "description": "Sample website for testing",
    "priority": 1,
    "tags": ["test", "example"]
  }'
```

### List active targets
```bash
curl "https://api-url/targets?status=active&limit=10"
```

### Update a target
```bash
curl -X PUT https://api-url/targets/target-123 \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

For complete API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).

---

**Last Updated**: January 2024  
**CDK Version**: 2.160.0  
**Python Version**: 3.12+
   .venv\Scripts\activate.bat
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Bootstrap CDK (first time only):**
   ```bash
   cdk bootstrap
   ```

## Usage

### Deploy the stack
```bash
cdk deploy
```

### Run tests
```bash
python -m pytest tests/ -v
```

### Synthesize CloudFormation
```bash
cdk synth
```

### Destroy the stack
```bash
cdk destroy
```

## API Endpoints

After deployment, you'll get an API Gateway URL. The endpoints are:

- `GET /` - Welcome message
- `GET /items` - List items in S3 bucket
- `POST /items` - Create new item in S3 bucket

## Testing the API

```bash
# Test GET endpoint
curl https://your-api-id.execute-api.region.amazonaws.com/prod/

# Test POST endpoint
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/items \
  -H "Content-Type: application/json" \
  -d '{"name": "test item", "value": "test value"}'
```

## Development

- Add new AWS resources in `project_2/project_2_stack.py`
- Modify Lambda function in `lambda/lambda_function.py`
- Add tests in `tests/unit/`

## Useful Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk deploy` - Deploy stack
- `cdk diff` - Compare deployed stack with current state
- `cdk docs` - Open CDK documentation
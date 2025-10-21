# Website Monitoring System# Web Crawler and Website Monitoring System



A simple AWS CDK-based solution for monitoring website availability and latency with automated alerts.A comprehensive AWS CDK-based solution for website monitoring, web crawling, and automated deployment with rollback capabilities.



## 🏗️ Architecture Overview## 🏗️ Architecture Overview



### Core Components### Project 1: Web Crawler and Monitoring Canary

- **Website Monitor Lambda**: Checks website availability and latency every 5 minutes

- **DynamoDB Tables**: #### Core Components

  - `Website_Table`: Stores website configurations- **Website Monitor Lambda**: Performs availability checks and web crawling

  - `AlarmHistory`: Logs alarm events- **CloudWatch Metrics**: Tracks availability, latency, and operational health

- **CloudWatch Metrics**: Tracks availability (0 or 1), latency (ms), and status codes- **CloudWatch Alarms**: Automated alerting for availability and performance issues

- **CloudWatch Alarms**: - **SNS/SQS Notifications**: Tagged notifications for alarm filtering

  - Availability alarm: Triggers when website is down (availability = 0)- **DynamoDB**: Alarm history logging and website configuration storage

  - Latency alarm: Triggers when response time > 400ms

- **SNS Topic**: Sends email notifications when alarms trigger#### Key Features

- **API Gateway**: REST API for managing websites (CRUD operations)- **Multi-stage Pipeline**: Beta → Gamma → Production with test blockers

- **Automated Rollback**: Triggers on alarm conditions or health check failures

### How It Works- **Operational Metrics**: Memory usage, crawl time, and processing health

1. Add websites via REST API → Stored in DynamoDB- **Comprehensive Testing**: Unit, integration, and performance tests

2. EventBridge triggers Lambda every 5 minutes

3. Lambda checks each enabled website### Project 2: CRUD API for Website Management

4. Metrics sent to CloudWatch (Availability, Latency, StatusCode)

5. Alarms trigger immediately when:#### API Gateway Endpoints

   - Website is down (availability = 0)- `GET/POST/PUT/DELETE /websites` - Website configuration management

   - Latency exceeds 400ms- `GET /crawler/status` - Real-time crawler status

6. SNS sends email notification- `POST /crawler/start` - Manual crawler execution

7. Alarm handler Lambda logs event to DynamoDB

#### Features

## 🚀 Quick Start- **Dynamic Website Management**: Add/remove websites without code changes

- **Real-time Monitoring**: Live crawler status and metrics

### Prerequisites- **Performance Tracking**: DynamoDB read/write time monitoring

```bash

# Install Python dependencies## 🚀 Quick Start

pip install -r requirements.txt -r requirements-dev.txt

### Prerequisites

# Install AWS CDK```bash

npm install -g aws-cdk# Install dependencies

pip install -r requirements.txt -r requirements-dev.txt

# Configure AWS credentials

aws configure# Install AWS CDK

```npm install -g aws-cdk



### Deploy the System# Configure AWS credentials

```bashaws configure

# Synthesize CloudFormation templates```

cdk synth

### Deployment

# Deploy all stacks

cdk deploy --all#### Single Environment Deployment

```bash

# Confirm SNS email subscription (check your email)# Synthesize CloudFormation templates

```cdk synth



After deployment, you'll see outputs including:# Deploy to default account/region

- API Gateway URLcdk deploy

- DynamoDB table names```

- SNS topic ARN

#### Multi-Stage Pipeline Deployment

## 📖 How to Use the API```bash

# Bootstrap CDK (one-time setup)

### 1. Get Your API Endpointcdk bootstrap



After deployment, find your API Gateway URL:# Deploy pipeline

```bashcdk deploy WebCrawlerPipelineStack

# From CDK deployment output, or:

aws cloudformation describe-stacks \# Monitor pipeline execution

  --stack-name ApiStack \aws codepipeline get-pipeline-state --name WebCrawlerPipeline

  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \```

  --output text

```### Testing

```bash

Your API endpoint will look like:# Run unit tests

```pytest tests/unit/ -v

https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/

```# Run integration tests

pytest tests/integration/ -v

### 2. Create a New Website

# Run performance tests

Add a website to start monitoring:pytest tests/performance/ -v



```bash# Run all tests with coverage

curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites \pytest --cov=manh_dev_ops_project --cov-report=html

  -H "Content-Type: application/json" \```

  -d '{

    "name": "Google",## � How to Use

    "url": "https://www.google.com",

    "enabled": true### Getting Started with Website Monitoring

  }'

```After deploying the system, you can start monitoring websites by adding them through the API.



**Successful Response (201 Created):**#### 1. Find Your API Endpoint

```json

{After deployment, get your API Gateway URL:

  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",```bash

  "name": "Google",# Get API Gateway URL

  "url": "https://www.google.com",aws apigateway get-rest-apis --query 'items[?name==`Website Management API`].id' --output text

  "enabled": true,

  "createdAt": "2025-10-14T10:00:00.000Z",# The full URL will be: https://{api-id}.execute-api.{region}.amazonaws.com/prod

  "updatedAt": "2025-10-14T10:00:00.000Z"```

}

```#### 2. Add Your First Website



**Add more websites:**Use the following curl command to add a website for monitoring:

```bash

# Add GitHub```bash

curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites \curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites \

  -H "Content-Type: application/json" \  -H "Content-Type: application/json" \

  -d '{"name": "GitHub", "url": "https://github.com", "enabled": true}'  -d '{

    "name": "Google",

# Add Amazon    "url": "https://www.google.com",

curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites \    "enabled": true

  -H "Content-Type: application/json" \  }'

  -d '{"name": "Amazon", "url": "https://www.amazon.com", "enabled": true}'```

```

**Response:**

### 3. List All Websites```json

{

View all websites being monitored:  "id": "550e8400-e29b-41d4-a716-446655440000",

  "name": "Google",

```bash  "url": "https://www.google.com",

curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites  "enabled": true,

```  "createdAt": "2024-01-15T10:00:00.000Z",

  "updatedAt": "2024-01-15T10:00:00.000Z"

**Response:**}

```json```

[

  {#### 3. Add More Websites

    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",

    "name": "Google",Add additional websites to monitor:

    "url": "https://www.google.com",

    "enabled": true,```bash

    "createdAt": "2025-10-14T10:00:00.000Z",# Add Facebook

    "updatedAt": "2025-10-14T10:00:00.000Z"curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites \

  },  -H "Content-Type: application/json" \

  {  -d '{

    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",    "name": "Facebook",

    "name": "GitHub",    "url": "https://www.facebook.com",

    "url": "https://github.com",    "enabled": true

    "enabled": true,  }'

    "createdAt": "2025-10-14T10:05:00.000Z",

    "updatedAt": "2025-10-14T10:05:00.000Z"# Add GitHub

  }curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites \

]  -H "Content-Type: application/json" \

```  -d '{

    "name": "GitHub",

### 4. Get a Specific Website    "url": "https://github.com",

    "enabled": true

Retrieve details of a single website:  }'

```

```bash

curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites/a1b2c3d4-e5f6-7890-abcd-ef1234567890#### 4. List All Websites

```

View all websites currently being monitored:

**Response (200 OK):**

```json```bash

{curl https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites

  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",```

  "name": "Google",

  "url": "https://www.google.com",**Response:**

  "enabled": true,```json

  "createdAt": "2025-10-14T10:00:00.000Z",[

  "updatedAt": "2025-10-14T10:00:00.000Z"  {

}    "id": "550e8400-e29b-41d4-a716-446655440000",

```    "name": "Google",

    "url": "https://www.google.com",

### 5. Update a Website    "enabled": true,

    "createdAt": "2024-01-15T10:00:00.000Z",

Modify website configuration:    "updatedAt": "2024-01-15T10:00:00.000Z"

  },

```bash  {

# Disable monitoring for a website    "id": "550e8400-e29b-41d4-a716-446655440001",

curl -X PUT https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \    "name": "Facebook",

  -H "Content-Type: application/json" \    "url": "https://www.facebook.com",

  -d '{    "enabled": true,

    "name": "Google Search Engine",    "createdAt": "2024-01-15T10:05:00.000Z",

    "url": "https://www.google.com",    "updatedAt": "2024-01-15T10:05:00.000Z"

    "enabled": false  }

  }']

``````



**Response (200 OK):**#### 5. Update a Website

```json

{Modify website settings:

  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",

  "name": "Google Search Engine",```bash

  "url": "https://www.google.com",curl -X PUT https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites/550e8400-e29b-41d4-a716-446655440000 \

  "enabled": false,  -H "Content-Type: application/json" \

  "createdAt": "2025-10-14T10:00:00.000Z",  -d '{

  "updatedAt": "2025-10-14T12:30:00.000Z"    "name": "Google Search",

}    "enabled": false

```  }'

```

### 6. Delete a Website

#### 6. Delete a Website

Remove a website from monitoring:

Remove a website from monitoring:

```bash

curl -X DELETE https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites/a1b2c3d4-e5f6-7890-abcd-ef1234567890```bash

```curl -X DELETE https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/websites/550e8400-e29b-41d4-a716-446655440000

```

**Response (204 No Content):**

```#### 7. Monitor Your Websites

(empty response body)

```Once websites are added, the system will automatically:



The website is permanently deleted from the system and will no longer be monitored.- **Check availability every 5 minutes** (via EventBridge scheduled Lambda)

- **Send metrics to CloudWatch** (availability, latency, status codes)

## 📊 Monitoring After Adding Websites- **Create alarms** for each website (availability < 95%, latency > 2000ms)

- **Send notifications** via SNS when alarms trigger

Once you've added websites via the API, the monitoring system automatically:

**View metrics in CloudWatch:**

### Immediate Actions:```bash

1. **Website stored in DynamoDB** - Configuration saved# Check recent metrics

2. **Next monitoring cycle** - Lambda checks website within 5 minutesaws cloudwatch get-metric-statistics \

3. **CloudWatch alarms created** - Per-website alarms automatically configured  --namespace WebsiteMonitoring \

  --metric-name Availability \

### Continuous Monitoring:  --start-time 2024-01-15T00:00:00Z \

- **Every 5 minutes**: Lambda function checks all enabled websites  --end-time 2024-01-15T23:59:59Z \

- **Metrics sent to CloudWatch**: Availability (0/1), Latency (ms), StatusCode  --period 300 \

- **Dashboard updated**: Real-time visualization in CloudWatch  --statistics Average

```

### When Alarms Trigger:

- **Availability = 0** (website down):**Check alarm status:**

  - Alarm triggers immediately```bash

  - Email sent via SNSaws cloudwatch describe-alarms --alarm-name-prefix "Google-"

  - Event logged to AlarmHistory table```

  

- **Latency > 400ms** (slow response):## �📊 Monitoring and Observability

  - Alarm triggers immediately

  - Email sent via SNS### CloudWatch Dashboards

  - Event logged to AlarmHistory table- **Website Monitoring**: Availability and latency metrics per website

- **Crawler Operations**: Memory usage, crawl time, pages processed

### View Monitoring Data:- **Pipeline Health**: Deployment status and rollback events



**Check CloudWatch metrics:**### Key Metrics

```bash```javascript

aws cloudwatch get-metric-statistics \// Website Monitoring Namespace

  --namespace WebsiteMonitoring \{

  --metric-name Availability \  "Namespace": "WebsiteMonitoring",

  --dimensions Name=WebsiteName,Value=Google \  "Metrics": ["Availability", "Latency", "StatusCode"]

  --start-time 2025-10-14T00:00:00Z \}

  --end-time 2025-10-14T23:59:59Z \

  --period 300 \// Crawler Operations Namespace

  --statistics Minimum,Average{

```  "Namespace": "WebCrawler/Operational",

  "Metrics": ["CrawlTime", "PagesCrawled", "MemoryUsage"]

**Check alarm status:**}

```bash```

aws cloudwatch describe-alarms --alarm-name-prefix "Google-"

```### Alarms and Notifications

- **Availability Alarm**: Triggers when uptime < 95%

**View alarm history:**- **Latency Alarm**: Triggers when response time > 2000ms

```bash- **Memory Alarm**: Triggers when Lambda memory > 80%

aws dynamodb scan --table-name AlarmHistory-XXXXX- **Crawl Time Alarm**: Triggers when crawling takes > 30 seconds

```

## 🔧 Configuration

## 🧪 Testing

### Environment Variables

Run the test suite to verify everything works:```bash

# Crawler Configuration

```bashMAX_CRAWL_DEPTH=2          # Maximum link depth to crawl

# Run all testsMAX_PAGES_PER_SITE=10      # Maximum pages per website

python -m pytest tests/ -vCRAWL_TIMEOUT=30           # HTTP request timeout in seconds



# Expected output: 8 passed# Pipeline Configuration

# - 3 unit tests (API validation)PIPELINE_NAME=WebCrawlerPipeline

# - 1 unit test (Monitor initialization)ROLLBACK_TIMEOUT=30        # Minutes to wait for rollback completion

# - 2 integration tests (API CRUD)

# - 2 integration tests (Monitor structure)# Monitoring Configuration

```ALARM_EMAIL=your-email@example.com

HEALTH_CHECK_TIMEOUT=300   # Seconds for health checks

## 📈 API Reference Summary```



| Method | Endpoint | Description | Request Body |### Website Configuration

|--------|----------|-------------|--------------|```json

| `POST` | `/websites` | Create new website | `{"name": "string", "url": "string", "enabled": boolean}` |{

| `GET` | `/websites` | List all websites | None |  "id": "unique-website-id",

| `GET` | `/websites/{id}` | Get specific website | None |  "name": "Example Website",

| `PUT` | `/websites/{id}` | Update website | `{"name": "string", "url": "string", "enabled": boolean}` |  "url": "https://example.com",

| `DELETE` | `/websites/{id}` | Delete website | None |  "enabled": true,

  "createdAt": "2024-01-15T10:00:00Z",

### Response Codes:  "updatedAt": "2024-01-15T10:00:00Z"

- `200 OK` - Successful GET/PUT}

- `201 Created` - Successful POST```

- `204 No Content` - Successful DELETE

- `400 Bad Request` - Invalid input## 🧪 Testing Strategy

- `404 Not Found` - Website not found

- `500 Internal Server Error` - Server error### Unit Tests

- Lambda function logic

## 🔧 Configuration- API validation and error handling

- CloudWatch metrics publishing

### Alarm Thresholds (Configurable in CDK):- DynamoDB operations

- **Availability**: Triggers when value < 1 (i.e., = 0)

- **Latency**: Triggers when > 400ms### Integration Tests

- **Evaluation**: Immediate (1 period, 1 datapoint)- End-to-end API workflows

- CloudWatch alarm publishing

### Monitoring Frequency:- SNS/SQS message processing

- Lambda runs every 5 minutes (EventBridge schedule)- Multi-website crawling scenarios

- Each check includes: HTTP request, metric publishing, alarm verification

### Performance Tests

### Email Notifications:- Crawler speed and memory usage

- Configured in `manh_dev_ops_project/monitor.py`- DynamoDB read/write performance

- Update SNS subscription email: `long.nm187254@gmail.com`- Concurrent website processing

- Large content handling

## 🛠️ Project Structure

### Pipeline Tests

```- CDK synthesis validation

ManhDevOpsProject/- Security scanning (Bandit, Safety)

├── app.py                          # CDK app entry point- Health check validation

├── manh_dev_ops_project/- Rollback functionality

│   ├── monitor.py                  # Monitoring stack (Lambda, DynamoDB, Alarms)

│   └── api.py                      # API stack (API Gateway, CRUD Lambda)## 🔄 CI/CD Pipeline

├── modules/

│   ├── monitor/### Stages

│   │   └── monitor.py              # Website monitoring Lambda code1. **Source**: GitHub webhook triggers

│   ├── api/2. **Beta**: Unit tests, security scans

│   │   └── api_handler.py          # API CRUD Lambda code3. **Gamma**: Integration tests, performance validation

│   └── alarm/4. **Production**: Manual approval, health checks, automated rollback

│       └── alarm_handler.py        # Alarm notification handler

├── tests/### Test Blockers

│   ├── unit/                       # Unit tests (4 tests)- Unit test failure rate > 0%

│   └── integration/                # Integration tests (4 tests)- Security vulnerabilities found

├── buildspec.build.yml             # Build and test pipeline- Performance regression > 10%

├── buildspec.deploy.yml            # Deployment pipeline- Health check failures

├── buildspec.rollback.yml          # Rollback pipeline

└── requirements.txt                # Python dependencies### Automated Rollback Triggers

```- CloudWatch alarms in ALARM state

- Health check failures

## 🔒 Security- Memory usage > 85%

- Deployment timeouts

- **IAM Roles**: Least privilege access for Lambda functions

- **API Gateway**: Public endpoint (add authentication if needed)## 📈 API Reference

- **DynamoDB**: Encrypted at rest

- **SNS**: Email verification required### Website Management

- **No hardcoded credentials**: All access via IAM roles```http

GET    /websites           # List all websites

## 📚 TroubleshootingPOST   /websites           # Create website

GET    /websites/{id}      # Get website details

### Website Not Being MonitoredPUT    /websites/{id}      # Update website

```bashDELETE /websites/{id}      # Delete website

# Check if website exists and is enabled```

curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/websites

### Crawler Management

# Verify Lambda is running```http

aws logs tail /aws/lambda/monitorWeb-WebsiteMonitorFunction --followGET    /crawler/status     # Get crawler status

```POST   /crawler/start      # Trigger manual crawl

```

### Not Receiving Email Notifications

1. Check SNS subscription confirmation in email### Response Format

2. Verify alarm is in ALARM state:```json

   ```bash{

   aws cloudwatch describe-alarms  "websites": [

   ```    {

3. Check SNS topic subscriptions:      "id": "string",

   ```bash      "name": "string",

   aws sns list-subscriptions      "url": "string",

   ```      "enabled": true,

      "createdAt": "ISO8601",

### API Errors      "updatedAt": "ISO8601"

- `400 Bad Request`: Check JSON format and required fields (name, url)    }

- `404 Not Found`: Verify website ID exists  ]

- `500 Internal Server Error`: Check CloudWatch logs for Lambda errors}

```

## 📄 License

## 🛠️ Development

This project is licensed under the MIT License.

### Project Structure

---```

manh_dev_ops_project/

**Quick Start Checklist:**├── website_monitor_stack.py     # Main infrastructure

- ✅ Deploy: `cdk deploy --all`├── api_stack.py                 # API Gateway and Lambda

- ✅ Confirm SNS email subscription├── web_crawler_pipeline.py      # CI/CD pipeline

- ✅ Get API endpoint from output├── pipeline_stack.py           # Legacy pipeline (deprecated)

- ✅ Add websites via POST /websitesmodules/

- ✅ Wait 5 minutes for first monitoring cycle├── monitor/                    # Website monitoring Lambda

- ✅ Check CloudWatch dashboard for metrics├── api_handler/               # API Lambda functions

├── alarm_handler/             # Alarm processing Lambda
tests/
├── unit/                      # Unit tests
├── integration/              # Integration tests
├── performance/              # Performance tests
scripts/
├── health_check.py           # Deployment health validation
├── rollback_manager.py       # Automated rollback logic
```

### Adding New Websites
```bash
# Via API
curl -X POST https://your-api.com/websites \
  -H "Content-Type: application/json" \
  -d '{"name": "New Site", "url": "https://newsite.com", "enabled": true}'
```

### Customizing Crawler Behavior
```python
# In monitor/monitor.py
class WebsiteMonitor:
    def __init__(self):
        self.max_crawl_depth = int(os.environ.get('MAX_CRAWL_DEPTH', '2'))
        self.max_pages_per_site = int(os.environ.get('MAX_PAGES_PER_SITE', '10'))
        # Add custom crawling logic here
```

## 🔒 Security

### Best Practices
- **IAM Least Privilege**: Minimal required permissions
- **VPC Deployment**: Resources in private subnets
- **Encryption**: Data encrypted at rest and in transit
- **Security Scanning**: Automated vulnerability detection

### Compliance
- **SOC 2**: Infrastructure security controls
- **GDPR**: Data minimization and consent
- **HIPAA**: Protected health information handling (if applicable)

## 📚 Troubleshooting

### Common Issues

#### Pipeline Failures
```bash
# Check pipeline status
aws codepipeline get-pipeline-state --name WebCrawlerPipeline

# View CloudWatch logs
aws logs tail /aws/codebuild/WebCrawlerPipeline
```

#### Lambda Timeouts
```bash
# Increase timeout in CDK
timeout=Duration.minutes(15)

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace WebCrawler/Operational \
  --metric-name CrawlTime
```

#### Alarm Not Triggering
```bash
# Check alarm configuration
aws cloudwatch describe-alarms --alarm-names WebsiteAvailabilityAlarm

# Verify metrics are publishing
aws cloudwatch list-metrics --namespace WebsiteMonitoring
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Standards
- **Python**: PEP 8 with type hints
- **Testing**: pytest with >= 80% coverage
- **Documentation**: Inline docstrings and README updates
- **Security**: No hardcoded secrets or credentials

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting guide
2. Review CloudWatch logs and metrics
3. Open an issue with detailed information
4. Include relevant log snippets and configuration

---

**Note**: This system is designed for monitoring and crawling publicly accessible websites only. Ensure compliance with website terms of service and robots.txt directives.
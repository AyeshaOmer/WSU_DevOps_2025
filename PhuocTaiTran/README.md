
# AWS CDK Multi-Stage CI/CD Pipeline Project

## Project Overview

This project implements a comprehensive multi-stage CI/CD pipeline using AWS CDK (Cloud Development Kit) with Python. The pipeline automates the deployment of a serverless web monitoring application across multiple environments with built-in testing, monitoring, and rollback capabilities.

### Key Features

- **Multi-Stage Deployment Pipeline**: Automated deployment across 5 environments (alpha, beta, gamma, preprod, prod)
- **Serverless Web Monitoring**: Lambda-based URL monitoring with availability and latency metrics
- **Comprehensive Testing**: Unit tests, functional tests, integration tests, performance tests, and security tests
- **Real-time Monitoring**: CloudWatch dashboards, alarms, and SNS notifications
- **Blue-Green Deployments**: AWS CodeDeploy for zero-downtime deployments
- **Automatic Rollback**: CloudWatch alarm-triggered rollbacks on deployment failures
- **Infrastructure as Code**: Complete infrastructure defined using AWS CDK

## Architecture

### Pipeline Architecture

```
GitHub Repository (main branch)
    ↓
Source Stage → Build Stage → UpdatePipeline Stage → Assets Stage
    ↓
Alpha Stage (Unit Tests → Deploy → Functional Tests → Rollback Monitor)
    ↓
Beta Stage (Deploy → Integration Tests → Rollback Monitor)
    ↓
Gamma Stage (Deploy → Performance Tests)
    ↓
PreProd Stage (Deploy → Security Tests)
    ↓
Production Stage (Manual Approval → Deploy → Rollback Monitor)
```

### Application Architecture

Each deployment stage creates the following AWS resources:

#### Core Infrastructure
- **AWS Lambda Functions**: 
  - Web monitoring function (monitors URLs for availability/latency)
  - Database insertion function (stores monitoring data)
  - Hello function (API endpoint)
- **Amazon DynamoDB GlobalTable**: Stores alarm notifications and monitoring data
- **Amazon SNS Topic**: Sends notifications for alarm events
- **Amazon API Gateway**: REST API endpoints for the application

#### Monitoring & Observability
- **CloudWatch Dashboard**: Real-time monitoring metrics (unique per environment)
- **CloudWatch Alarms**: Availability and latency thresholds for monitored URLs
- **CloudWatch Metrics**: Custom metrics for URL monitoring

#### Deployment & Security
- **AWS CodeDeploy**: Blue-green deployment configuration for Lambda functions
- **IAM Roles**: Least privilege access for Lambda execution and CodeDeploy
- **AWS CodePipeline**: Multi-stage deployment orchestration
- **AWS CodeBuild**: Build, test, and deployment execution

### Monitored URLs
The application monitors the following websites:
- https://www.skipq.org
- https://www.bbc.com
- https://www.facebook.com

## Project Structure

```
PhuocTaiTran/
├── app.py                              # CDK app entry point
├── cdk.json                           # CDK configuration
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── README.md                         # This file
├── phuoc_tai_tran/
│   ├── phuoc_tai_tran_stack.py       # Main pipeline stack
│   ├── phuoc_tai_tran_lambda_stack.py # Application infrastructure stack
│   └── pipeline_stage_22121066.py    # Pipeline stage definition
├── Module/
│   ├── constantSource.py             # Configuration constants
│   ├── helloLambda.py                # Hello function code
│   ├── ObtainMetrics.py              # Web monitoring function code
│   ├── DBLambda.py                   # Database function code
│   ├── alarm.py                      # Alarm configuration
│   ├── dashBoard.py                  # Dashboard configuration
│   └── publish_metric.py             # Metric publishing utilities
└── tests/
    └── unit/
        └── test_phuoc_tai_tran_stack.py # Unit tests
```

## Prerequisites

### AWS Account Setup
1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Configured with credentials
   ```bash
   aws configure
   ```
3. **AWS CDK**: Installed globally
   ```bash
   npm install -g aws-cdk
   ```

### GitHub Integration
1. **GitHub Repository**: Access to `https://github.com/Vallad1122/WSU_DevOps_2025`
2. **GitHub Token**: Personal access token stored in AWS Secrets Manager as `myToken`

### Local Development Environment
- **Python 3.8+**: Required for CDK development
- **Node.js**: Required for CDK CLI
- **Git**: For version control

## Setup and Installation

### 1. Clone and Setup

```bash
# Navigate to project directory
cd WSU_DevOps_2025/PhuocTaiTran

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate.bat

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure AWS Secrets Manager

Create a GitHub token in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
    --name myToken \
    --description "GitHub Personal Access Token for CodePipeline" \
    --secret-string "your-github-token-here"
```

### 3. Bootstrap CDK (First time only)

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

## Usage

### Deploy the Pipeline

```bash
# Synthesize CloudFormation templates
cdk synth

# Deploy the pipeline stack
cdk deploy --require-approval never
```

### Running Tests

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/unit/test_phuoc_tai_tran_stack.py::test_lambda -v
```

### Pipeline Operations

#### Manual Pipeline Trigger
```bash
aws codepipeline start-pipeline-execution \
    --name PhuocTaiTranStack-PhuocTaiTranPipeline774DD699-BJeCNuSFnTZe \
    --region ap-southeast-2
```

#### Monitor Pipeline Status
```bash
aws codepipeline get-pipeline-state \
    --name PhuocTaiTranStack-PhuocTaiTranPipeline774DD699-BJeCNuSFnTZe \
    --region ap-southeast-2
```

#### View Pipeline Executions
```bash
aws codepipeline list-pipeline-executions \
    --pipeline-name PhuocTaiTranStack-PhuocTaiTranPipeline774DD699-BJeCNuSFnTZe \
    --region ap-southeast-2
```

### Environment-Specific Resources

Each environment creates uniquely named resources:
- **Alpha**: `PhuocTaiTranDashboard-alpha`
- **Beta**: `PhuocTaiTranDashboard-beta`
- **Gamma**: `PhuocTaiTranDashboard-gamma`
- **PreProd**: `PhuocTaiTranDashboard-preprod`
- **Production**: `PhuocTaiTranDashboard-prod`

## Pipeline Stages

### 1. **Alpha Stage**
- **Purpose**: Initial development testing
- **Tests**: Unit tests before deployment, functional tests after
- **Auto-rollback**: Enabled with CloudWatch monitoring

### 2. **Beta Stage** 
- **Purpose**: Integration testing environment
- **Tests**: Integration tests with external dependencies
- **Auto-rollback**: Enabled with comprehensive monitoring

### 3. **Gamma Stage**
- **Purpose**: Performance and load testing
- **Tests**: Performance benchmarks and load testing
- **Monitoring**: Enhanced performance metrics

### 4. **PreProd Stage**
- **Purpose**: Security and compliance testing
- **Tests**: Security scans and compliance checks
- **Validation**: Production-like environment validation

### 5. **Production Stage**
- **Purpose**: Live production environment
- **Approval**: Manual approval gate before deployment
- **Monitoring**: Full production monitoring and alerting
- **Rollback**: Immediate rollback capability

## Monitoring and Alerting

### CloudWatch Dashboards
- Real-time monitoring for each monitored URL
- Availability and latency metrics visualization
- Environment-specific dashboards

### CloudWatch Alarms
- **Availability Alarms**: Trigger when availability drops below 100%
- **Latency Alarms**: Trigger when response time exceeds thresholds
- **SNS Integration**: Automatic notifications to administrators

### SNS Notifications
- Real-time alerts for alarm state changes
- Integration with DynamoDB for alarm logging
- Configurable notification endpoints

## Troubleshooting

### Common Issues

#### 1. CloudFormation Stack Conflicts
**Error**: Dashboard already exists in another stack
**Solution**: Ensure unique resource names per environment (implemented in current version)

#### 2. Pipeline Permission Issues
**Error**: Access denied during pipeline execution
**Solution**: Verify IAM roles and AWS CLI credentials

#### 3. GitHub Integration Issues
**Error**: Unable to access repository
**Solution**: Verify GitHub token in AWS Secrets Manager

### Pipeline Failure Recovery

```bash
# Delete failed stack
aws cloudformation delete-stack --stack-name STACK_NAME --region REGION

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name STACK_NAME --region REGION

# Retry pipeline execution
aws codepipeline start-pipeline-execution --name PIPELINE_NAME --region REGION
```

## Development

### Adding New Environments
1. Add new stage in `phuoc_tai_tran_stack.py`
2. Configure stage-specific tests
3. Update pipeline configuration
4. Deploy changes

### Modifying Monitored URLs
1. Update `Module/constantSource.py`
2. Modify dashboard and alarm configurations
3. Test changes in alpha environment
4. Deploy through pipeline

### Adding New Tests
1. Create test functions in appropriate test files
2. Configure test execution in pipeline stages
3. Validate test results in CodeBuild

## Useful CDK Commands

 * `cdk ls`          # List all stacks in the app
 * `cdk synth`       # Emits the synthesized CloudFormation template
 * `cdk deploy`      # Deploy this stack to your default AWS account/region
 * `cdk diff`        # Compare deployed stack with current state
 * `cdk docs`        # Open CDK documentation
 * `cdk destroy`     # Delete the stack

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Run local tests: `python -m pytest tests/ -v`
4. Create pull request to `main`
5. Pipeline will automatically test and deploy changes

## License

This project is part of the WSU DevOps 2025 coursework.

---

**Author**: Phuoc Tai Tran  
**Project**: WSU DevOps 2025 Pipeline Sprint  
**Repository**: https://github.com/Vallad1122/WSU_DevOps_2025

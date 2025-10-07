
# PhuocTai-Pipelines: Web Health Monitoring CI/CD Pipeline

## 📋 Project Overview

This project implements a comprehensive **5-stage CI/CD pipeline** for deploying a **Web Health Monitoring System** using AWS CDK, similar to Eugene's WHLambda functionality but with enhanced monitoring and auto-rollback capabilities.

## 🏗️ Architecture

### **Pipeline Stages:**
1. **Alpha** - Unit testing and functional validation
2. **Beta** - Integration testing 
3. **Gamma** - Performance testing
4. **PreProd** - Security and compliance testing
5. **Production** - Manual approval with rollback protection

### **AWS Resources Deployed:**
- **3 Lambda Functions**: Web health monitoring, database logging, hello world
- **DynamoDB Global Table**: Alarm storage (`WebsiteAlarmsTableF8DFBCDD`)
- **API Gateway**: REST endpoint for health checks
- **CloudWatch**: 8 alarms + dashboard for monitoring
- **SNS Topic**: Notification system
- **IAM Roles**: Security permissions (3 roles)

## 🔄 Auto Rollback Features

- **CloudFormation-level**: Automatic rollback on deployment failures
- **CloudWatch Integration**: Alarm-triggered rollbacks
- **Health Monitoring**: Post-deployment validation
- **Manual Gates**: Production approval with rollback info

## 🚀 Deployment

### **Prerequisites:**
- AWS CLI configured
- CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.12+

### **Setup:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Deploy pipeline
cdk deploy PhuocTaiTranStack
```

### **Pipeline Execution:**
1. Push code to trigger pipeline
2. Automated progression through stages
3. Manual approval required for production
4. Auto rollback on failures

## 📊 Monitoring & Testing

### **Test Coverage:**
- ✅ 8/8 unit tests passing
- ✅ Lambda function validation
- ✅ DynamoDB table verification  
- ✅ CloudWatch alarms testing
- ✅ API Gateway integration

### **Health Metrics:**
- Website availability monitoring
- Response time tracking
- Error rate thresholds
- Performance benchmarks

## 📁 Project Structure

```
PhuocTai-Pipelines/
├── app.py                 # CDK entry point
├── cdk.json              # CDK configuration
├── requirements.txt      # Python dependencies
├── requirements-dev.txt  # Development dependencies
├── phuoc_tai_tran/       # Pipeline infrastructure
│   ├── phuoc_tai_tran_stack.py        # Pipeline definition
│   ├── phuoc_tai_tran_lambda_stack.py # Lambda application
│   └── pipeline_stage_22121066.py     # Stage definitions
├── Module/               # Lambda function code
│   ├── ObtainMetrics.py  # Web health monitoring
│   ├── DBLambda.py       # Database operations
│   ├── helloLambda.py    # Hello world function
│   └── publish_metric.py # CloudWatch integration
└── tests/               # Unit tests
    └── unit/
        └── test_phuoc_tai_tran_stack.py
```

## 🎯 Key Features

### **Web Health Monitoring (wh_lambda equivalent):**
- Website availability checks
- Latency monitoring  
- Error detection and alerting
- Performance metrics collection

### **Enterprise-Grade Pipeline:**
- Multi-environment deployment
- Automated testing at each stage
- Security validation
- Performance benchmarking
- Auto rollback protection

### **Observability:**
- CloudWatch dashboard
- 8 comprehensive alarms
- SNS notifications
- DynamoDB logging

## 👥 Team Member

**Phuoc Tai Tran** - WSU DevOps 2025
- Student ID: 22121066
- Web Health Monitoring System
- 5-Stage CI/CD Pipeline with Auto Rollback

## 🔗 Repository Structure

This project follows the same organizational pattern as other team members:
- `Ayesha-Pipelines/` - Ayesha's pipeline project
- `Eugene/` - Eugene's pipeline project  
- `PhuocTai-Pipelines/` - This project

## 📈 Success Metrics

- ✅ Pipeline deployed successfully
- ✅ All 5 stages functional
- ✅ Auto rollback implemented
- ✅ 100% test coverage (8/8 tests passing)
- ✅ Multi-environment monitoring active
- ✅ Production-ready with manual approval gates

## 🚨 Monitoring Alerts

The system monitors:
- Lambda function errors
- DynamoDB operation failures  
- API Gateway response times
- CloudWatch alarm states
- Overall system health

**Auto rollback triggers** activate when critical thresholds are exceeded, ensuring system reliability across all deployment stages.


# Website Health Monitoring System

A scalable web application monitoring system built with AWS Lambda, CloudWatch, and CDK that crawls websites periodically and tracks their health metrics.

## 🏗️ Architecture Overview

This project implements a serverless website monitoring solution that:

- **Crawls multiple websites** from a configurable JSON list
- **Measures availability and latency** for each website
- **Publishes metrics to CloudWatch** every 5 minutes
- **Provides real-time dashboard** for monitoring website health
- **Scales automatically** with AWS Lambda

## 📊 Features

### Web Crawler
- Monitors multiple websites simultaneously
- Measures availability (up/down status)
- Records response latency in milliseconds
- Tracks HTTP status codes
- Handles errors gracefully with error metrics

### CloudWatch Integration
- Custom metrics namespace: `WebsiteMonitoring`
- Metrics published every 5 minutes
- Comprehensive dashboard with widgets for:
  - Website availability trends
  - Latency monitoring
  - Error tracking

### Scalability Features
- Serverless architecture with AWS Lambda
- Event-driven execution via EventBridge
- Configurable website list via JSON
- Auto-scaling based on demand

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.9+
- AWS CDK installed
- Node.js for CDK

### Installation

1. **Clone and Setup**
   ```bash
   cd Dan
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap
   ```

3. **Deploy the Stack**
   ```bash
   cdk deploy
   ```

### Configuration

Edit `modules/websites.json` to monitor your websites:

```json
{
  "websites": [
    {
      "name": "Google",
      "url": "https://www.google.com",
      "timeout": 10
    },
    {
      "name": "Your Website",
      "url": "https://yourwebsite.com",
      "timeout": 15
    }
  ]
}
```

## 📈 Monitoring and Dashboards

### CloudWatch Dashboard
Access your dashboard at: AWS Console → CloudWatch → Dashboards → `Website-Health-Monitor`

The dashboard includes:
- **Availability Widget**: Shows uptime percentage over time
- **Latency Widget**: Displays response times in milliseconds
- **Error Widget**: Tracks failed requests and timeouts

### Metrics Available
- `Availability`: 1 (up) or 0 (down)
- `Latency`: Response time in milliseconds
- `StatusCode`: HTTP response codes
- `Errors`: Count of failed monitoring attempts

## 🛠️ Development

### Project Structure
```
Dan/
├── dan/
│   └── dan_stack.py          # CDK infrastructure code
├── modules/
│   ├── Metrix.py            # Web crawler Lambda function
│   ├── websites.json        # Website configuration
│   └── requirements.txt     # Lambda dependencies
├── app.py                   # CDK app entry point
├── requirements.txt         # CDK dependencies
└── README.md               # This file
```

### Adding New Websites
1. Edit `modules/websites.json`
2. Add website object with name, url, and timeout
3. Deploy changes: `cdk deploy`

### Modifying Crawl Frequency
Edit `dan/dan_stack.py` and change the schedule:
```python
schedule=events.Schedule.rate(Duration.minutes(5))  # Change to desired interval
```

## 🔧 Troubleshooting

### Common Issues

1. **No metrics appearing in CloudWatch**
   - Verify Lambda function has executed (check CloudWatch Logs)
   - Ensure IAM permissions for CloudWatch PutMetricData
   - Check for errors in Lambda logs

2. **Lambda timeout errors**
   - Increase timeout in `dan_stack.py`
   - Reduce number of websites or timeout values
   - Check network connectivity issues

3. **Permission errors**
   - Verify Lambda execution role has CloudWatch permissions
   - Check AWS credentials configuration

### Logs and Debugging
- Lambda logs: CloudWatch → Log groups → `/aws/lambda/DanStack-WebCrawlerFunction`
- CDK logs: Check terminal output during deployment
- Metrics: CloudWatch → Metrics → WebsiteMonitoring namespace

## 📚 Learning Concepts

This project demonstrates:

### AWS Services Integration
- **AWS Lambda**: Serverless compute for web crawling
- **CloudWatch**: Metrics storage and dashboard visualization
- **EventBridge**: Scheduled event triggering
- **IAM**: Secure service-to-service communication

### Monitoring Best Practices
- Custom metrics design and implementation
- Dashboard creation for operational visibility
- Error handling and alerting strategies
- Scalable monitoring architecture

### DevOps Principles
- Infrastructure as Code with CDK
- Automated deployment pipelines
- Configuration management
- Documentation and runbooks

## 🔄 User Stories and Features

### Current Features ✅
- [x] Basic website availability monitoring
- [x] Latency measurement and tracking
- [x] CloudWatch metrics integration
- [x] Automated 5-minute crawling schedule
- [x] Configurable website list
- [x] Real-time dashboard visualization
- [x] Error tracking and reporting

### Planned Features 🚧
- [ ] Email/SNS alerting for downtime
- [ ] Multi-region monitoring
- [ ] Historical data analysis
- [ ] API Gateway for manual triggers
- [ ] Slack/Teams integration
- [ ] Custom alarm thresholds
- [ ] Website content validation

### Future Enhancements 🔮
- [ ] Machine learning for anomaly detection
- [ ] Predictive analytics for performance trends
- [ ] Integration with external monitoring services
- [ ] Mobile app for monitoring alerts
- [ ] Advanced reporting and analytics

## 📖 CDK Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk deploy` - Deploy stack to AWS
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy` - Remove all resources
- `cdk docs` - Open CDK documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with ❤️ using AWS CDK and Python*

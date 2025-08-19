# Website Monitoring Runbook

## 🚨 Emergency Procedures

### Alert: Website Down
**Symptoms**: Availability metric = 0 for a website
**Immediate Actions**:
1. Check CloudWatch Logs for Lambda errors
2. Verify website is actually down (manual check)
3. Check DNS resolution issues
4. Escalate to website team if confirmed outage

### Alert: High Latency
**Symptoms**: Latency metric > 5000ms consistently
**Immediate Actions**:
1. Check network connectivity
2. Verify if issue is widespread or specific to monitored site
3. Check CloudWatch metrics for patterns
4. Monitor for 15 minutes before escalating

### Alert: Lambda Function Failures
**Symptoms**: Error metrics increasing, no new data points
**Immediate Actions**:
1. Check Lambda function logs in CloudWatch
2. Verify IAM permissions
3. Check function timeout and memory settings
4. Redeploy if necessary

## 🔧 Operational Procedures

### Adding New Websites
1. Edit `modules/websites.json`
2. Add new website object:
   ```json
   {
     "name": "New Site",
     "url": "https://newsite.com",
     "timeout": 10
   }
   ```
3. Deploy: `cdk deploy`
4. Monitor first execution in CloudWatch Logs

### Removing Websites
1. Remove entry from `modules/websites.json`
2. Deploy: `cdk deploy`
3. Historical metrics will remain in CloudWatch

### Changing Monitoring Frequency
1. Edit `dan/dan_stack.py`
2. Modify: `schedule=events.Schedule.rate(Duration.minutes(X))`
3. Deploy: `cdk deploy`
4. Verify new schedule in EventBridge console

### Updating Lambda Code
1. Modify `modules/Metrix.py`
2. Test locally if possible
3. Deploy: `cdk deploy`
4. Monitor first execution for errors

## 📊 Monitoring Health Checks

### Daily Checks
- [ ] Verify all websites are being monitored (check CloudWatch metrics)
- [ ] Review error rates in dashboard
- [ ] Check Lambda function execution logs
- [ ] Validate no missing data points

### Weekly Checks
- [ ] Review average latency trends
- [ ] Check for any timeout issues
- [ ] Verify dashboard widgets are displaying correctly
- [ ] Review costs in AWS Billing

### Monthly Checks
- [ ] Update website list if needed
- [ ] Review historical trends
- [ ] Check for any performance degradation
- [ ] Update documentation

## 🛠️ Troubleshooting Guide

### Issue: No Metrics in CloudWatch
**Possible Causes**:
- Lambda function not executing
- IAM permission issues
- Code errors in Lambda function

**Resolution Steps**:
1. Check EventBridge rule is enabled
2. Review Lambda logs for errors
3. Verify IAM role has CloudWatch:PutMetricData permission
4. Test Lambda function manually

### Issue: Inconsistent Metrics
**Possible Causes**:
- Network issues
- Website intermittent problems
- Lambda cold starts

**Resolution Steps**:
1. Check Lambda duration metrics
2. Review website status independently
3. Consider increasing Lambda memory if cold start issues
4. Check for any network connectivity patterns

### Issue: High Lambda Costs
**Possible Causes**:
- Too frequent execution
- Long execution times
- High memory allocation

**Resolution Steps**:
1. Review execution frequency needs
2. Optimize code for faster execution
3. Adjust memory allocation if over-provisioned
4. Consider batching multiple website checks

## 📞 Escalation Contacts

### Technical Issues
- **DevOps Team**: Monitor Lambda and CloudWatch issues
- **Network Team**: DNS and connectivity problems
- **Security Team**: IAM and permissions issues

### Business Issues
- **Website Owners**: Site-specific availability issues
- **Management**: Service level impacts
- **Incident Response**: Critical outages

## 🔍 Useful AWS Console Links

- **Lambda Function**: AWS Console → Lambda → Functions → WebCrawlerFunction
- **CloudWatch Dashboard**: AWS Console → CloudWatch → Dashboards → Website-Health-Monitor
- **EventBridge Rules**: AWS Console → EventBridge → Rules → WebCrawlerSchedule
- **CloudWatch Logs**: AWS Console → CloudWatch → Log groups → /aws/lambda/DanStack-WebCrawlerFunction
- **CloudWatch Metrics**: AWS Console → CloudWatch → Metrics → WebsiteMonitoring

## 📋 Maintenance Windows

### Planned Maintenance
- **When**: During low-traffic hours (typically 2-4 AM local time)
- **Process**: 
  1. Announce maintenance window
  2. Disable EventBridge rule temporarily
  3. Perform updates
  4. Test functionality
  5. Re-enable monitoring
  6. Confirm normal operation

### Emergency Maintenance
- **When**: Critical issues affecting monitoring
- **Process**:
  1. Identify issue severity
  2. Implement immediate fix if possible
  3. Document changes made
  4. Schedule proper fix during maintenance window
  5. Post-incident review

## 📚 Reference Documentation

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [CloudWatch Metrics Documentation](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/working_with_metrics.html)
- [AWS CDK Python Documentation](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)

---

*Last Updated: August 2025*
*Next Review: September 2025*

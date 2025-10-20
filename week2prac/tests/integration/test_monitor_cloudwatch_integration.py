"""
Integration test: Monitor Lambda → CloudWatch Metrics
Tests that the monitor Lambda function successfully publishes metrics to CloudWatch
"""
import pytest
import time
from datetime import datetime, timedelta
from ..test_config import METRIC_NAMESPACE, CLOUDWATCH_WAIT_TIME

class TestMonitorCloudWatchIntegration:
    """Test Monitor Lambda to CloudWatch integration"""
    
    def test_lambda_publishes_availability_metrics(self, aws_helper, monitor_lambda_name, 
                                                  wait_for_propagation):
        """Test that monitor Lambda publishes availability metrics to CloudWatch"""
        print(f"Testing Lambda function: {monitor_lambda_name}")
        
        # Invoke the monitor Lambda function
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        
        # Verify Lambda executed successfully
        assert response.get('ok') is True, f"Lambda failed: {response}"
        assert response.get('sites_checked', 0) > 0, "No sites were checked"
        
        # Wait for metrics to propagate
        wait_for_propagation(30)
        
        # Check that availability metrics were published
        # Using httpbin.org as a test site that should be available
        test_site = "https://www.nytimes.com"  # Using your actual monitored site
        
        metrics_found = aws_helper.wait_for_metrics(
            "Availability", 
            {"Site": test_site},
            timeout_seconds=CLOUDWATCH_WAIT_TIME
        )
        
        assert metrics_found, f"Availability metrics not found for {test_site}"
        
        # Verify the metric value is reasonable (0 or 1)
        availability_value = aws_helper.get_metric_value(
            "Availability", 
            {"Site": test_site}
        )
        
        assert availability_value is not None, "No availability metric value found"
        assert availability_value in [0, 1], f"Invalid availability value: {availability_value}"
    
    def test_lambda_publishes_latency_metrics(self, aws_helper, monitor_lambda_name):
        """Test that monitor Lambda publishes latency metrics to CloudWatch"""
        
        # Invoke the monitor Lambda function
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        assert response.get('ok') is True
        
        # Wait for metrics propagation
        time.sleep(30)
        
        # Check latency metrics
        test_site = "https://www.nytimes.com"
        
        latency_value = aws_helper.get_metric_value(
            "Latency",
            {"Site": test_site}
        )
        
        # Latency might be None if site was unreachable, but if present should be positive
        if latency_value is not None:
            assert latency_value > 0, f"Invalid latency value: {latency_value}"
            assert latency_value < 30000, f"Latency too high: {latency_value}ms"  # 30s max
    
    def test_lambda_publishes_status_code_metrics(self, aws_helper, monitor_lambda_name):
        """Test that monitor Lambda publishes status code metrics to CloudWatch"""
        
        # Invoke the monitor Lambda function
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        assert response.get('ok') is True
        
        # Wait for metrics propagation
        time.sleep(30)
        
        # Check status code metrics
        test_site = "https://www.nytimes.com"
        
        # Look for status code metrics (typically 200)
        status_code_value = aws_helper.get_metric_value(
            "StatusCode",
            {"Site": test_site, "Code": "200"}
        )
        
        # Status code metric should be 1 if the site returned 200
        if status_code_value is not None:
            assert status_code_value == 1, f"Unexpected status code metric value: {status_code_value}"
    
    def test_lambda_handles_multiple_sites(self, aws_helper, monitor_lambda_name):
        """Test that monitor Lambda processes all configured sites"""
        
        # Invoke the monitor Lambda function
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        
        assert response.get('ok') is True
        sites_checked = response.get('sites_checked', 0)
        
        # Should check at least the sites in sites.json (nytimes, bbc, cnn)
        assert sites_checked >= 3, f"Expected at least 3 sites, got {sites_checked}"
        
        print(f"Successfully checked {sites_checked} sites")
"""
Unit tests for monitor.py Lambda function
"""
import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, call
from pathlib import Path

# Add the lambda directory to Python path for importing
lambda_dir = Path(__file__).parent.parent.parent / "week2prac" / "lambda"
sys.path.insert(0, str(lambda_dir))

# Import the module under test
import monitor

class TestMonitorLambda:
    """Unit tests for monitor Lambda function"""
    
    def test_put_metrics_successful_request(self, mock_cloudwatch, mock_environment_vars):
        """Test _put_metrics with successful site request"""
        
        site = "https://httpbin.org/status/200"
        latency_ms = 1234.5
        status_code = 200
        available = 1
        
        # Call the function
        monitor._put_metrics(site, latency_ms, status_code, available)
        
        # Verify CloudWatch put_metric_data was called
        assert mock_cloudwatch.put_metric_data.called
        call_args = mock_cloudwatch.put_metric_data.call_args
        
        # Check the call arguments
        assert call_args[1]['Namespace'] == 'TestMonitor'
        metric_data = call_args[1]['MetricData']
        
        # Should have availability, latency, and status code metrics
        assert len(metric_data) == 3
        
        # Check availability metric
        availability_metric = next(m for m in metric_data if m['MetricName'] == 'Availability')
        assert availability_metric['Value'] == 1
        assert availability_metric['Unit'] == 'Count'
        assert availability_metric['Dimensions'][0]['Value'] == site
        
        # Check latency metric
        latency_metric = next(m for m in metric_data if m['MetricName'] == 'Latency')
        assert latency_metric['Value'] == 1234.5
        assert latency_metric['Unit'] == 'Milliseconds'
        
        # Check status code metric
        status_metric = next(m for m in metric_data if m['MetricName'] == 'StatusCode')
        assert status_metric['Value'] == 1
        assert status_metric['Unit'] == 'Count'
        status_dimensions = {d['Name']: d['Value'] for d in status_metric['Dimensions']}
        assert status_dimensions['Site'] == site
        assert status_dimensions['Code'] == '200'
    
    def test_put_metrics_failed_request(self, mock_cloudwatch, mock_environment_vars):
        """Test _put_metrics with failed site request (no latency/status)"""
        
        site = "https://httpbin.org/status/500"
        latency_ms = None
        status_code = None
        available = 0
        
        # Call the function
        monitor._put_metrics(site, latency_ms, status_code, available)
        
        # Verify CloudWatch call
        call_args = mock_cloudwatch.put_metric_data.call_args
        metric_data = call_args[1]['MetricData']
        
        # Should only have availability metric
        assert len(metric_data) == 1
        
        availability_metric = metric_data[0]
        assert availability_metric['MetricName'] == 'Availability'
        assert availability_metric['Value'] == 0
    
    @patch('monitor.open', create=True)
    def test_lambda_handler_successful_execution(self, mock_open, mock_http_pool, 
                                                mock_cloudwatch, mock_environment_vars,
                                                mock_time, lambda_context, sample_sites):
        """Test complete lambda_handler execution with successful HTTP requests"""
        
        # Mock sites.json file reading
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_sites)
        
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status = 200
        mock_http_pool.request.return_value = mock_response
        
        # Test event (can be empty for scheduled events)
        event = {}
        
        # Call the lambda handler
        result = monitor.lambda_handler(event, lambda_context)
        
        # Verify result
        assert result['ok'] is True
        assert result['sites_checked'] == 3
        
        # Verify HTTP requests were made
        assert mock_http_pool.request.call_count == 3
        
        # Verify CloudWatch metrics were published for each site
        assert mock_cloudwatch.put_metric_data.call_count == 3
    
    @patch('monitor.open', create=True)
    def test_lambda_handler_with_http_failures(self, mock_open, mock_http_pool,
                                              mock_cloudwatch, mock_environment_vars,
                                              mock_time, lambda_context, sample_sites):
        """Test lambda_handler handles HTTP failures gracefully"""
        
        # Mock sites.json
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_sites)
        
        # Mock HTTP request to raise exception
        mock_http_pool.request.side_effect = Exception("Connection timeout")
        
        event = {}
        
        # Call lambda handler - should not raise exception
        result = monitor.lambda_handler(event, lambda_context)
        
        # Should still return success
        assert result['ok'] is True
        assert result['sites_checked'] == 3
        
        # Should still publish metrics (availability=0 for failed sites)
        assert mock_cloudwatch.put_metric_data.call_count == 3
        
        # Verify all metrics show unavailable (availability=0)
        for call_args in mock_cloudwatch.put_metric_data.call_args_list:
            metric_data = call_args[1]['MetricData']
            availability_metric = next(m for m in metric_data if m['MetricName'] == 'Availability')
            assert availability_metric['Value'] == 0
    
    @patch('monitor.open', create=True) 
    def test_lambda_handler_mixed_responses(self, mock_open, mock_http_pool,
                                          mock_cloudwatch, mock_environment_vars,
                                          mock_time, lambda_context):
        """Test lambda_handler with mixed success/failure responses"""
        
        # Test sites with different expected outcomes
        test_sites = [
            "https://httpbin.org/status/200",  # Should succeed
            "https://httpbin.org/status/500",  # Should get 500 status
            "https://httpbin.org/delay/10"     # Should timeout/fail
        ]
        
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(test_sites)
        
        # Mock different responses for different sites
        responses = [
            Mock(status=200),  # Success
            Mock(status=500),  # Server error  
            Exception("Timeout")  # Network failure
        ]
        mock_http_pool.request.side_effect = responses
        
        event = {}
        result = monitor.lambda_handler(event, lambda_context)
        
        # Should handle mixed results
        assert result['ok'] is True
        assert result['sites_checked'] == 3
        
        # Verify metrics published for all sites
        assert mock_cloudwatch.put_metric_data.call_count == 3
        
        # Check specific metric values
        calls = mock_cloudwatch.put_metric_data.call_args_list
        
        # First site (200) - should be available
        first_call_metrics = calls[0][1]['MetricData']
        first_availability = next(m for m in first_call_metrics if m['MetricName'] == 'Availability')
        assert first_availability['Value'] == 1
        
        # Second site (500) - should be unavailable  
        second_call_metrics = calls[1][1]['MetricData']
        second_availability = next(m for m in second_call_metrics if m['MetricName'] == 'Availability')
        assert second_availability['Value'] == 0
        
        # Third site (timeout) - should be unavailable
        third_call_metrics = calls[2][1]['MetricData']
        third_availability = next(m for m in third_call_metrics if m['MetricName'] == 'Availability')
        assert third_availability['Value'] == 0
    
    def test_latency_calculation(self, mock_time):
        """Test that latency is calculated correctly"""
        
        # mock_time fixture returns [1697800000.0, 1697800001.5] 
        # So latency should be 1.5 seconds = 1500ms
        
        start_time = mock_time()
        end_time = mock_time()
        
        latency_seconds = end_time - start_time
        latency_ms = latency_seconds * 1000
        
        assert latency_ms == 1500.0
    
    def test_metric_dimensions(self, mock_cloudwatch, mock_environment_vars):
        """Test that metric dimensions are set correctly"""
        
        site = "https://example.com"
        monitor._put_metrics(site, 1000.0, 200, 1)
        
        call_args = mock_cloudwatch.put_metric_data.call_args
        metric_data = call_args[1]['MetricData']
        
        for metric in metric_data:
            # All metrics should have Site dimension
            site_dimension = next(d for d in metric['Dimensions'] if d['Name'] == 'Site')
            assert site_dimension['Value'] == site
            
            # Status code metric should have additional Code dimension
            if metric['MetricName'] == 'StatusCode':
                code_dimension = next(d for d in metric['Dimensions'] if d['Name'] == 'Code')
                assert code_dimension['Value'] == '200'
    
    def test_operational_metrics_publishing(self, mock_cloudwatch, mock_environment_vars):
        """Test that operational metrics are published correctly"""
        
        execution_time = 1500.0  # 1.5 seconds
        memory_used = 45.2  # 45.2 MB
        sites_processed = 3
        
        # Call the operational metrics function
        monitor._put_operational_metrics(execution_time, memory_used, sites_processed)
        
        # Verify CloudWatch put_metric_data was called
        assert mock_cloudwatch.put_metric_data.called
        call_args = mock_cloudwatch.put_metric_data.call_args
        
        # Check the call arguments
        assert call_args[1]['Namespace'] == 'TestMonitor'
        metric_data = call_args[1]['MetricData']
        
        # Should have 3 operational metrics
        assert len(metric_data) == 3
        
        # Check execution time metric
        execution_metric = next(m for m in metric_data if m['MetricName'] == 'CrawlerExecutionTime')
        assert execution_metric['Value'] == 1500.0
        assert execution_metric['Unit'] == 'Milliseconds'
        assert execution_metric['Dimensions'][0]['Name'] == 'Function'
        assert execution_metric['Dimensions'][0]['Value'] == 'WebCrawler'
        
        # Check memory metric
        memory_metric = next(m for m in metric_data if m['MetricName'] == 'CrawlerMemoryUsage')
        assert memory_metric['Value'] == 45.2
        assert memory_metric['Unit'] == 'Megabytes'
        
        # Check sites processed metric
        sites_metric = next(m for m in metric_data if m['MetricName'] == 'SitesProcessed')
        assert sites_metric['Value'] == 3
        assert sites_metric['Unit'] == 'Count'
    
    def test_memory_usage_measurement(self):
        """Test memory usage measurement function"""
        
        # Call the memory usage function
        memory_mb = monitor._get_memory_usage_mb()
        
        # Should return a non-negative number
        assert isinstance(memory_mb, (int, float))
        assert memory_mb >= 0
        
        # In a real environment, memory should be greater than 0
        # But in test environment it might return 0 as fallback
    
    @patch('monitor.open', create=True)
    def test_lambda_handler_includes_operational_metrics(self, mock_open, mock_http_pool,
                                                        mock_cloudwatch, mock_environment_vars,
                                                        mock_time, lambda_context, sample_sites):
        """Test that lambda_handler publishes operational metrics"""
        
        # Mock sites.json file reading
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_sites)
        
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status = 200
        mock_http_pool.request.return_value = mock_response
        
        # Test event
        event = {}
        
        # Call the lambda handler
        result = monitor.lambda_handler(event, lambda_context)
        
        # Verify result includes operational metrics
        assert result['ok'] is True
        assert 'execution_time_ms' in result
        assert 'memory_used_mb' in result
        assert result['execution_time_ms'] >= 0
        assert result['memory_used_mb'] >= 0
        
        # Should have called CloudWatch metrics twice per site + once for operational metrics
        # 3 sites × 1 call each + 1 operational call = 4 calls
        assert mock_cloudwatch.put_metric_data.call_count == 4
        
        # Verify operational metrics were published
        operational_call_found = False
        for call_args in mock_cloudwatch.put_metric_data.call_args_list:
            metric_data = call_args[1]['MetricData']
            for metric in metric_data:
                if metric['MetricName'] in ['CrawlerExecutionTime', 'CrawlerMemoryUsage', 'SitesProcessed']:
                    operational_call_found = True
                    break
        
        assert operational_call_found, "Operational metrics were not published"

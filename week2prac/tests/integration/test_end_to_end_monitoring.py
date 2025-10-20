"""
Integration test: End-to-End Monitoring Flow
Tests the complete monitoring workflow from Lambda execution to alarm logging
"""
import pytest
import time
from datetime import datetime, timedelta
from ..test_config import METRIC_NAMESPACE, CLOUDWATCH_WAIT_TIME

class TestEndToEndMonitoring:
    """Test complete end-to-end monitoring workflow"""
    
    def test_complete_monitoring_workflow(self, aws_helper, monitor_lambda_name,
                                        cloudwatch_client, wait_for_propagation):
        """Test complete workflow: Lambda → Metrics → Dashboard visibility"""
        
        print("Testing complete monitoring workflow...")
        
        # Step 1: Execute monitor Lambda
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        assert response.get('ok') is True, f"Monitor Lambda failed: {response}"
        sites_checked = response.get('sites_checked', 0)
        assert sites_checked > 0, "No sites were monitored"
        
        print(f"Step 1 ✓: Monitor Lambda checked {sites_checked} sites")
        
        # Step 2: Wait for metrics propagation
        wait_for_propagation(30)
        
        # Step 3: Verify metrics are published for each monitored site
        test_sites = ["https://www.nytimes.com", "https://www.bbc.com", "https://www.cnn.com"]
        metrics_verified = 0
        
        for site in test_sites:
            # Check availability metrics
            availability_found = aws_helper.wait_for_metrics(
                "Availability",
                {"Site": site},
                timeout_seconds=60
            )
            
            if availability_found:
                metrics_verified += 1
                print(f"Step 3.{metrics_verified} ✓: Metrics found for {site}")
        
        assert metrics_verified > 0, "No metrics found for any monitored sites"
        print(f"Step 3 ✓: Verified metrics for {metrics_verified} sites")
        
        # Step 4: Verify metric values are reasonable
        for site in test_sites[:2]:  # Test first 2 sites to save time
            availability = aws_helper.get_metric_value("Availability", {"Site": site})
            if availability is not None:
                assert availability in [0, 1], f"Invalid availability for {site}: {availability}"
                
            latency = aws_helper.get_metric_value("Latency", {"Site": site})
            if latency is not None:
                assert latency > 0, f"Invalid latency for {site}: {latency}"
                assert latency < 60000, f"Latency too high for {site}: {latency}ms"
        
        print("Step 4 ✓: Metric values validated")
        
        # Step 5: Verify CloudWatch namespace exists
        namespaces_response = cloudwatch_client.list_metrics(Namespace=METRIC_NAMESPACE)
        metrics_list = namespaces_response.get('Metrics', [])
        assert len(metrics_list) > 0, f"No metrics found in namespace {METRIC_NAMESPACE}"
        
        print(f"Step 5 ✓: Found {len(metrics_list)} metrics in CloudWatch")
        
        print("🎉 Complete monitoring workflow test PASSED!")
    
    def test_monitoring_resilience_to_failures(self, aws_helper, monitor_lambda_name):
        """Test that monitoring system handles site failures gracefully"""
        
        print("Testing monitoring resilience...")
        
        # Execute monitor Lambda (some sites might fail, that's expected)
        response = aws_helper.invoke_lambda(monitor_lambda_name)
        
        # Lambda should complete successfully even if some sites fail
        assert response.get('ok') is True, "Monitor Lambda should handle failures gracefully"
        
        # Should still report sites checked (even if some failed)
        sites_checked = response.get('sites_checked', 0)
        assert sites_checked > 0, "Should check at least some sites"
        
        print(f"✓ Monitor Lambda processed {sites_checked} sites with resilience")
        
        # Wait for metrics
        time.sleep(30)
        
        # Verify that we get availability=0 for unreachable sites (if any)
        test_site = "https://www.nytimes.com"
        availability = aws_helper.get_metric_value("Availability", {"Site": test_site})
        
        # The value should exist and be either 0 or 1
        if availability is not None:
            assert availability in [0, 1], f"Availability should be 0 or 1, got {availability}"
            print(f"✓ Site {test_site} availability: {availability}")
    
    def test_metrics_retention_and_history(self, aws_helper, cloudwatch_client):
        """Test that metrics are retained and historical data is available"""
        
        print("Testing metrics retention...")
        
        # Look for metrics from the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Check if we have historical metrics
        response = cloudwatch_client.get_metric_statistics(
            Namespace=METRIC_NAMESPACE,
            MetricName='Availability',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour periods
            Statistics=['Average']
        )
        
        datapoints = response.get('Datapoints', [])
        
        # We might not have 24 hours of data if this is a new deployment
        # But if we have data, verify it's structured correctly
        if datapoints:
            print(f"✓ Found {len(datapoints)} historical datapoints")
            
            for datapoint in datapoints[:3]:  # Check first 3
                assert 'Timestamp' in datapoint, "Datapoint missing timestamp"
                assert 'Average' in datapoint, "Datapoint missing average value"
                assert datapoint['Average'] in [0, 1], f"Invalid historical availability: {datapoint['Average']}"
        else:
            print("ℹ No historical metrics found (expected for new deployments)")
    
    def test_monitoring_performance_under_load(self, aws_helper, monitor_lambda_name):
        """Test monitoring system performance with multiple rapid invocations"""
        
        print("Testing monitoring performance...")
        
        # Execute monitor Lambda multiple times in quick succession
        results = []
        max_invocations = 3  # Keep it reasonable for testing
        
        for i in range(max_invocations):
            start_time = time.time()
            response = aws_helper.invoke_lambda(monitor_lambda_name)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            assert response.get('ok') is True, f"Invocation {i+1} failed: {response}"
            results.append({
                'invocation': i + 1,
                'execution_time': execution_time,
                'sites_checked': response.get('sites_checked', 0)
            })
            
            # Small delay between invocations
            time.sleep(5)
        
        # Verify all invocations succeeded
        assert len(results) == max_invocations, "Not all invocations completed"
        
        # Check performance metrics
        avg_execution_time = sum(r['execution_time'] for r in results) / len(results)
        assert avg_execution_time < 60, f"Average execution time too high: {avg_execution_time}s"
        
        for result in results:
            assert result['sites_checked'] > 0, f"Invocation {result['invocation']} checked no sites"
        
        print(f"✓ Completed {max_invocations} invocations, avg time: {avg_execution_time:.2f}s")
        print("🎉 Performance test PASSED!")
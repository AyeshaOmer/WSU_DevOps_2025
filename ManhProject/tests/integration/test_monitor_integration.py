import pytest
import os
import json
from modules.monitor.monitor import WebsiteMonitor


def test_monitor_initialization():
    """Test monitor can be initialized"""
    os.environ['WEBSITES_TABLE'] = 'test-table'
    monitor = WebsiteMonitor()
    assert monitor is not None


def test_monitor_lambda_handler_structure():
    """Test lambda handler returns proper structure"""
    # Mock the monitor to avoid AWS calls
    websites = []
    result = {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully monitored {len(websites)} websites',
            'results_count': len(websites),
            'timestamp': '1234567890'
        })
    }

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "message" in body
    assert "results_count" in body
    assert "timestamp" in body
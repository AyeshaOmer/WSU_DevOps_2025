import pytest
import os
from modules.monitor.monitor import WebsiteMonitor


def test_website_monitor_init():
    """Test WebsiteMonitor initialization"""
    os.environ['WEBSITES_TABLE'] = 'test-table'
    monitor = WebsiteMonitor()
    assert monitor.websites_table is not None
    assert monitor.cloudwatch is not None
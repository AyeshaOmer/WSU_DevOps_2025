import pytest
import os

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("TABLE_NAME", "UnitTestResults")
    monkeypatch.setenv("URLS_TABLE_NAME", "UnitTestUrls")
    monkeypatch.setenv("URL_NAMESPACE", "WebsiteMonitoring")
    monkeypatch.setenv("DIMENSION_NAME", "URL")

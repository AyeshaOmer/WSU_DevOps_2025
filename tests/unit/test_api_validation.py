import pytest
from modules.api.api_handler import validate_website


def test_validate_website_valid():
    """Test valid website validation"""
    website = {"name": "Test Site", "url": "https://example.com"}
    error = validate_website(website)
    assert error is None


def test_validate_website_missing_name():
    """Test website validation with missing name"""
    website = {"url": "https://example.com"}
    error = validate_website(website)
    assert error == "Missing required field: name"


def test_validate_website_invalid_url():
    """Test website validation with invalid URL"""
    website = {"name": "Test Site", "url": "invalid-url"}
    error = validate_website(website)
    assert error == "URL must start with http:// or https://"
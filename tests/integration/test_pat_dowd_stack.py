import pytest
import requests
import json
import os

# You might want to store this in environment variables or config file
API_ENDPOINT = "https://zx8itp7b79.execute-api.ap-southeast-2.amazonaws.com/prod/urls"
TEST_URL = "www.example.com"

def test_initial_empty_urls():
    """Test that initially there are no URLs in the system"""
    response = requests.get(API_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert len(data["urls"]) == 0

def test_add_url():
    """Test adding a new URL"""
    payload = {"url": TEST_URL}
    response = requests.post(API_ENDPOINT, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert TEST_URL in data["message"]

def test_url_exists():
    """Test that the added URL is in the list"""
    response = requests.get(API_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert TEST_URL in data["urls"]

def test_delete_url():
    """Test deleting a URL"""
    response = requests.delete(f"{API_ENDPOINT}/{TEST_URL}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert TEST_URL in data["message"]

def test_url_is_gone():
    """Test that the URL is no longer in the list"""
    response = requests.get(API_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert TEST_URL not in data["urls"]

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup any remaining test URLs after each test"""
    yield
    # Clean up any test URLs that might remain
    response = requests.get(API_ENDPOINT)
    if response.status_code == 200:
        data = response.json()
        if "urls" in data and TEST_URL in data["urls"]:
            requests.delete(f"{API_ENDPOINT}/{TEST_URL}")
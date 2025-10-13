import pytest
import requests
import json
import os
import urllib3

http = urllib3.PoolManager()

# You might want to store this in environment variables or config file
API_ENDPOINT = "https://gyefqsoe42.execute-api.ap-southeast-2.amazonaws.com/prod/urls"
TEST_URL = "www.example.com"

def test_initial_empty_urls():
    """Test that initially there are no URLs in the system"""
    response = http.request('GET', API_ENDPOINT)
    assert response.status == 200
    data = response.json()
    assert len(data) == 0

def test_add_url():
    """Test adding a new URL"""
    encoded_data = json.dumps({"url": TEST_URL}).encode('utf-8')
    response = http.request('POST', API_ENDPOINT, body=encoded_data)
    assert response.status == 201
    data = response.json()
    assert "message" in data
    assert TEST_URL in data["message"]

def test_url_exists():
    """Test that the added URL is in the list"""
    response = http.request('GET', API_ENDPOINT)
    assert response.status == 200
    data = response.json()
    assert TEST_URL in data

def test_delete_url():
    """Test deleting a URL"""
    response = http.request('delete', API_ENDPOINT+'/'+TEST_URL)
    assert response.status == 200
    data = response.json()
    assert "message" in data
    assert TEST_URL in data["message"]

def test_url_is_gone():
    """Test that the URL is no longer in the list"""
    response = http.request('GET', API_ENDPOINT)
    assert response.status == 200
    data = response.json()
    assert TEST_URL not in data



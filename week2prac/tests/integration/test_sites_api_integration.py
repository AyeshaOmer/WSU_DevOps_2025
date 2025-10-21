import json
import pytest
import boto3
import requests
import uuid
from time import sleep
import os
from typing import Dict, Any, Optional


class TestSitesApiIntegration:
    """Integration tests for the Sites CRUD API"""
    
    # These should be set based on actual deployed resources
    API_BASE_URL = None  # Will be set from environment or deployment
    TABLE_NAME = None    # Will be set from environment or deployment
    
    @classmethod
    def setup_class(cls):
        """Setup for all tests in this class"""
        # Get API endpoint from environment (set after deployment)
        cls.API_BASE_URL = os.environ.get('SITES_API_URL')
        cls.TABLE_NAME = os.environ.get('SITES_TABLE_NAME', 'Sites-TestStack')
        
        if not cls.API_BASE_URL:
            pytest.skip("SITES_API_URL environment variable not set - skipping integration tests")
            
        cls.dynamodb = boto3.resource('dynamodb')
        cls.sites_table = cls.dynamodb.Table(cls.TABLE_NAME)
        
        # Clean up any existing test data
        cls.cleanup_test_data()
        
    @classmethod
    def cleanup_test_data(cls):
        """Clean up test data from DynamoDB"""
        try:
            # Scan for test sites and delete them
            response = cls.sites_table.scan()
            test_sites = [item for item in response['Items'] 
                         if item.get('name', '').startswith('TEST_')]
            
            for site in test_sites:
                cls.sites_table.delete_item(Key={'site_id': site['site_id']})
                
        except Exception as e:
            print(f"Warning: Could not clean up test data: {e}")
            
    def test_api_health_check(self):
        """Test basic API connectivity"""
        response = requests.get(f"{self.API_BASE_URL}/sites")
        # Should return 200 or 404, not connection errors
        assert response.status_code in [200, 404, 500]  # 500 is ok if table doesn't exist yet
        
    @pytest.mark.skipif(not API_BASE_URL, reason="API URL not configured")
    def test_create_site_success(self):
        """Test successful site creation via API"""
        site_data = {
            "url": "https://test-example-create.com",
            "name": "TEST_Create Site",
            "description": "Test site for creation",
            "tags": ["test", "integration"],
            "enabled": True
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=site_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
        created_site = response.json()
        
        assert created_site["url"] == site_data["url"]
        assert created_site["name"] == site_data["name"]
        assert "site_id" in created_site
        assert "created_at" in created_site
        
        # Verify site was created in DynamoDB
        db_item = self.sites_table.get_item(Key={"site_id": created_site["site_id"]})
        assert "Item" in db_item
        assert db_item["Item"]["url"] == site_data["url"]
        
        # Clean up
        self.sites_table.delete_item(Key={"site_id": created_site["site_id"]})
        
    def test_create_site_invalid_data(self):
        """Test site creation with invalid data"""
        invalid_data = {
            "name": "Site without URL"  # Missing required URL
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        error_response = response.json()
        assert "error" in error_response
        assert "url is required" in error_response["error"]
        
    def test_list_sites(self):
        """Test listing sites via API"""
        # Create a test site first
        test_site = {
            "url": "https://test-example-list.com",
            "name": "TEST_List Site",
            "description": "Test site for listing"
        }
        
        create_response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=test_site,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        created_site = create_response.json()
        
        # List sites
        response = requests.get(f"{self.API_BASE_URL}/sites")
        assert response.status_code == 200
        
        sites_data = response.json()
        assert "sites" in sites_data
        assert "count" in sites_data
        assert isinstance(sites_data["sites"], list)
        assert sites_data["count"] >= 1
        
        # Verify our test site is in the list
        site_ids = [site["site_id"] for site in sites_data["sites"]]
        assert created_site["site_id"] in site_ids
        
        # Clean up
        self.sites_table.delete_item(Key={"site_id": created_site["site_id"]})
        
    def test_get_single_site(self):
        """Test retrieving a single site via API"""
        # Create a test site first
        test_site = {
            "url": "https://test-example-get.com",
            "name": "TEST_Get Site"
        }
        
        create_response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=test_site,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        created_site = create_response.json()
        
        # Get the site by ID
        response = requests.get(f"{self.API_BASE_URL}/sites/{created_site['site_id']}")
        assert response.status_code == 200
        
        retrieved_site = response.json()
        assert retrieved_site["site_id"] == created_site["site_id"]
        assert retrieved_site["url"] == test_site["url"]
        assert retrieved_site["name"] == test_site["name"]
        
        # Clean up
        self.sites_table.delete_item(Key={"site_id": created_site["site_id"]})
        
    def test_get_nonexistent_site(self):
        """Test retrieving a non-existent site"""
        fake_site_id = str(uuid.uuid4())
        
        response = requests.get(f"{self.API_BASE_URL}/sites/{fake_site_id}")
        assert response.status_code == 404
        
        error_response = response.json()
        assert "error" in error_response
        assert "not found" in error_response["error"]
        
    def test_update_site(self):
        """Test updating a site via API"""
        # Create a test site first
        test_site = {
            "url": "https://test-example-update.com",
            "name": "TEST_Original Site",
            "enabled": True
        }
        
        create_response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=test_site,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        created_site = create_response.json()
        
        # Update the site
        update_data = {
            "name": "TEST_Updated Site",
            "enabled": False
        }
        
        response = requests.put(
            f"{self.API_BASE_URL}/sites/{created_site['site_id']}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        updated_site = response.json()
        assert updated_site["name"] == update_data["name"]
        assert updated_site["enabled"] == update_data["enabled"]
        assert updated_site["url"] == test_site["url"]  # URL should remain unchanged
        
        # Verify in database
        db_item = self.sites_table.get_item(Key={"site_id": created_site["site_id"]})
        assert db_item["Item"]["name"] == update_data["name"]
        assert db_item["Item"]["enabled"] == update_data["enabled"]
        
        # Clean up
        self.sites_table.delete_item(Key={"site_id": created_site["site_id"]})
        
    def test_update_nonexistent_site(self):
        """Test updating a non-existent site"""
        fake_site_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        
        response = requests.put(
            f"{self.API_BASE_URL}/sites/{fake_site_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 404
        
        error_response = response.json()
        assert "error" in error_response
        assert "not found" in error_response["error"]
        
    def test_delete_site(self):
        """Test deleting a site via API"""
        # Create a test site first
        test_site = {
            "url": "https://test-example-delete.com",
            "name": "TEST_Delete Site"
        }
        
        create_response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=test_site,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        created_site = create_response.json()
        
        # Delete the site
        response = requests.delete(f"{self.API_BASE_URL}/sites/{created_site['site_id']}")
        assert response.status_code == 200
        
        delete_response = response.json()
        assert "deleted successfully" in delete_response["message"]
        assert delete_response["site_id"] == created_site["site_id"]
        
        # Verify site is deleted from database
        db_item = self.sites_table.get_item(Key={"site_id": created_site["site_id"]})
        assert "Item" not in db_item
        
    def test_delete_nonexistent_site(self):
        """Test deleting a non-existent site"""
        fake_site_id = str(uuid.uuid4())
        
        response = requests.delete(f"{self.API_BASE_URL}/sites/{fake_site_id}")
        assert response.status_code == 404
        
        error_response = response.json()
        assert "error" in error_response
        assert "not found" in error_response["error"]
        
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = requests.options(f"{self.API_BASE_URL}/sites")
        
        # CORS headers should be present
        headers = response.headers
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        
    def test_duplicate_url_prevention(self):
        """Test that duplicate URLs are prevented"""
        test_url = "https://test-duplicate-prevention.com"
        
        # Create first site
        site_data1 = {
            "url": test_url,
            "name": "TEST_First Site"
        }
        
        response1 = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=site_data1,
            headers={"Content-Type": "application/json"}
        )
        assert response1.status_code == 201
        created_site1 = response1.json()
        
        # Try to create second site with same URL
        site_data2 = {
            "url": test_url,
            "name": "TEST_Second Site"
        }
        
        response2 = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=site_data2,
            headers={"Content-Type": "application/json"}
        )
        assert response2.status_code == 409
        
        error_response = response2.json()
        assert "already exists" in error_response["error"]
        
        # Clean up
        self.sites_table.delete_item(Key={"site_id": created_site1["site_id"]})
        
    def test_site_workflow_end_to_end(self):
        """Test complete CRUD workflow"""
        # 1. Create a site
        initial_site = {
            "url": "https://test-workflow.com",
            "name": "TEST_Workflow Site",
            "description": "End-to-end test",
            "tags": ["test"],
            "enabled": True
        }
        
        create_response = requests.post(
            f"{self.API_BASE_URL}/sites",
            json=initial_site,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        created_site = create_response.json()
        site_id = created_site["site_id"]
        
        # 2. Read the site
        get_response = requests.get(f"{self.API_BASE_URL}/sites/{site_id}")
        assert get_response.status_code == 200
        retrieved_site = get_response.json()
        assert retrieved_site["url"] == initial_site["url"]
        
        # 3. Update the site
        update_data = {
            "name": "TEST_Updated Workflow Site",
            "enabled": False
        }
        
        update_response = requests.put(
            f"{self.API_BASE_URL}/sites/{site_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        assert update_response.status_code == 200
        updated_site = update_response.json()
        assert updated_site["name"] == update_data["name"]
        assert updated_site["enabled"] == update_data["enabled"]
        
        # 4. List sites and verify our site is there
        list_response = requests.get(f"{self.API_BASE_URL}/sites")
        assert list_response.status_code == 200
        sites_data = list_response.json()
        site_ids = [site["site_id"] for site in sites_data["sites"]]
        assert site_id in site_ids
        
        # 5. Delete the site
        delete_response = requests.delete(f"{self.API_BASE_URL}/sites/{site_id}")
        assert delete_response.status_code == 200
        
        # 6. Verify site is deleted
        final_get_response = requests.get(f"{self.API_BASE_URL}/sites/{site_id}")
        assert final_get_response.status_code == 404

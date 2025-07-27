#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date
from typing import Dict, Any

class PurchaseTrackerAPITester:
    def __init__(self, base_url="https://bca401d0-5daa-428a-8abb-f3d7bd02c38e.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {
            'purchases': [],
            'stores': []
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            try:
                response_data = response.json()
            except:
                response_data = {}
                
            return response.status_code < 400, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, data, status = self.make_request('GET', 'dashboard/stats')
        
        if success and 'total_purchases' in data:
            self.log_test("Dashboard Stats", True, f"- Total purchases: {data.get('total_purchases', 0)}")
            return True
        else:
            self.log_test("Dashboard Stats", False, f"- Status: {status}, Data: {data}")
            return False

    def test_create_store(self):
        """Test store creation"""
        store_data = {
            "name": "Test Store",
            "url": "https://teststore.com"
        }
        
        success, data, status = self.make_request('POST', 'stores', store_data)
        
        if success and 'id' in data:
            self.created_items['stores'].append(data['id'])
            self.log_test("Create Store", True, f"- Store ID: {data['id']}")
            return data['id']
        else:
            self.log_test("Create Store", False, f"- Status: {status}, Data: {data}")
            return None

    def test_get_stores(self):
        """Test getting all stores"""
        success, data, status = self.make_request('GET', 'stores')
        
        if success and isinstance(data, list):
            self.log_test("Get Stores", True, f"- Found {len(data)} stores")
            return True
        else:
            self.log_test("Get Stores", False, f"- Status: {status}, Data: {data}")
            return False

    def test_create_purchase(self):
        """Test purchase creation"""
        purchase_data = {
            "store_name": "Amazon",
            "store_url": "https://amazon.com",
            "product_name": "Test Product",
            "price": 29.99,
            "payment_method": "PayPal",
            "order_date": "2024-01-15",
            "expected_delivery": "2024-01-20",
            "status": "Ordered",
            "notes": "Test purchase"
        }
        
        success, data, status = self.make_request('POST', 'purchases', purchase_data)
        
        if success and 'id' in data:
            self.created_items['purchases'].append(data['id'])
            self.log_test("Create Purchase", True, f"- Purchase ID: {data['id']}")
            return data['id']
        else:
            self.log_test("Create Purchase", False, f"- Status: {status}, Data: {data}")
            return None

    def test_get_purchases(self):
        """Test getting all purchases"""
        success, data, status = self.make_request('GET', 'purchases')
        
        if success and isinstance(data, list):
            self.log_test("Get Purchases", True, f"- Found {len(data)} purchases")
            return True
        else:
            self.log_test("Get Purchases", False, f"- Status: {status}, Data: {data}")
            return False

    def test_get_purchase_by_id(self, purchase_id: str):
        """Test getting single purchase"""
        success, data, status = self.make_request('GET', f'purchases/{purchase_id}')
        
        if success and data.get('id') == purchase_id:
            self.log_test("Get Purchase by ID", True, f"- Product: {data.get('product_name')}")
            return True
        else:
            self.log_test("Get Purchase by ID", False, f"- Status: {status}, Data: {data}")
            return False

    def test_update_purchase(self, purchase_id: str):
        """Test updating purchase"""
        update_data = {
            "status": "Shipped",
            "notes": "Updated test purchase"
        }
        
        success, data, status = self.make_request('PUT', f'purchases/{purchase_id}', update_data)
        
        if success and data.get('status') == 'Shipped':
            self.log_test("Update Purchase", True, f"- Status updated to: {data.get('status')}")
            return True
        else:
            self.log_test("Update Purchase", False, f"- Status: {status}, Data: {data}")
            return False

    def test_purchase_filtering(self):
        """Test purchase filtering by status"""
        success, data, status = self.make_request('GET', 'purchases', params={'status': 'Ordered'})
        
        if success and isinstance(data, list):
            self.log_test("Purchase Filtering", True, f"- Found {len(data)} ordered purchases")
            return True
        else:
            self.log_test("Purchase Filtering", False, f"- Status: {status}, Data: {data}")
            return False

    def test_archive_purchase(self, purchase_id: str):
        """Test archiving purchase"""
        success, data, status = self.make_request('POST', f'purchases/{purchase_id}/archive')
        
        if success:
            self.log_test("Archive Purchase", True, f"- Message: {data.get('message', 'Archived')}")
            return True
        else:
            self.log_test("Archive Purchase", False, f"- Status: {status}, Data: {data}")
            return False

    def test_delete_purchase(self, purchase_id: str):
        """Test deleting purchase"""
        success, data, status = self.make_request('DELETE', f'purchases/{purchase_id}')
        
        if success:
            self.log_test("Delete Purchase", True, f"- Message: {data.get('message', 'Deleted')}")
            if purchase_id in self.created_items['purchases']:
                self.created_items['purchases'].remove(purchase_id)
            return True
        else:
            self.log_test("Delete Purchase", False, f"- Status: {status}, Data: {data}")
            return False

    def test_delete_store(self, store_id: str):
        """Test deleting store"""
        success, data, status = self.make_request('DELETE', f'stores/{store_id}')
        
        if success:
            self.log_test("Delete Store", True, f"- Message: {data.get('message', 'Deleted')}")
            if store_id in self.created_items['stores']:
                self.created_items['stores'].remove(store_id)
            return True
        else:
            self.log_test("Delete Store", False, f"- Status: {status}, Data: {data}")
            return False

    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Clean up purchases
        for purchase_id in self.created_items['purchases'][:]:
            self.test_delete_purchase(purchase_id)
        
        # Clean up stores
        for store_id in self.created_items['stores'][:]:
            self.test_delete_store(store_id)

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting Purchase Tracker API Tests")
        print(f"📡 Testing API at: {self.api_url}")
        print("=" * 60)

        # Test dashboard stats (should work even with empty data)
        self.test_dashboard_stats()

        # Test store operations
        store_id = self.test_create_store()
        self.test_get_stores()

        # Test purchase operations
        purchase_id = self.test_create_purchase()
        if purchase_id:
            self.test_get_purchases()
            self.test_get_purchase_by_id(purchase_id)
            self.test_update_purchase(purchase_id)
            self.test_purchase_filtering()
            
            # Test archiving (creates a second purchase for this test)
            archive_purchase_id = self.test_create_purchase()
            if archive_purchase_id:
                self.test_archive_purchase(archive_purchase_id)

        # Test dashboard stats again (should show updated data)
        self.test_dashboard_stats()

        # Cleanup
        self.cleanup()

        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    tester = PurchaseTrackerAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date

class DateSerializationTester:
    def __init__(self, base_url="https://bca401d0-5daa-428a-8abb-f3d7bd02c38e.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_purchases = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data=None):
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
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

    def test_purchase_creation_with_dates(self):
        """Test purchase creation with various date formats - this was the main failing test"""
        print("\n🔍 Testing Purchase Creation with Date Fields (Previously Failing)")
        
        purchase_data = {
            "store_name": "Date Test Store",
            "store_url": "https://datetest.com",
            "product_name": "Date Test Product",
            "price": 99.99,
            "payment_method": "Visa",
            "order_date": "2024-02-15",
            "expected_delivery": "2024-02-20",
            "delivered_date": "2024-02-18",
            "status": "Delivered",
            "notes": "Testing date serialization fix"
        }
        
        success, data, status = self.make_request('POST', 'purchases', purchase_data)
        
        if success and 'id' in data:
            self.created_purchases.append(data['id'])
            # Verify dates are properly returned
            order_date_ok = 'order_date' in data and data['order_date'] is not None
            expected_delivery_ok = 'expected_delivery' in data and data['expected_delivery'] is not None
            delivered_date_ok = 'delivered_date' in data and data['delivered_date'] is not None
            
            if order_date_ok and expected_delivery_ok and delivered_date_ok:
                self.log_test("Purchase Creation with Dates", True, 
                            f"- ID: {data['id']}, Order: {data['order_date']}, Expected: {data['expected_delivery']}, Delivered: {data['delivered_date']}")
                return data['id']
            else:
                self.log_test("Purchase Creation with Dates", False, 
                            f"- Missing date fields in response: {data}")
                return None
        else:
            self.log_test("Purchase Creation with Dates", False, 
                        f"- Status: {status}, Error: {data}")
            return None

    def test_purchase_date_updates(self, purchase_id):
        """Test updating purchase with new dates"""
        print("\n🔍 Testing Purchase Date Updates")
        
        update_data = {
            "order_date": "2024-02-16",
            "expected_delivery": "2024-02-22",
            "delivered_date": "2024-02-19",
            "status": "Delivered",
            "notes": "Updated dates test"
        }
        
        success, data, status = self.make_request('PUT', f'purchases/{purchase_id}', update_data)
        
        if success and data.get('id') == purchase_id:
            # Check if dates were updated correctly
            dates_updated = (
                data.get('order_date') and 
                data.get('expected_delivery') and 
                data.get('delivered_date')
            )
            
            if dates_updated:
                self.log_test("Purchase Date Updates", True, 
                            f"- Updated dates: Order: {data['order_date']}, Expected: {data['expected_delivery']}, Delivered: {data['delivered_date']}")
                return True
            else:
                self.log_test("Purchase Date Updates", False, 
                            f"- Date fields missing or null in response: {data}")
                return False
        else:
            self.log_test("Purchase Date Updates", False, 
                        f"- Status: {status}, Error: {data}")
            return False

    def test_purchase_retrieval_with_dates(self, purchase_id):
        """Test retrieving purchase and verifying date formatting"""
        print("\n🔍 Testing Purchase Retrieval with Date Formatting")
        
        success, data, status = self.make_request('GET', f'purchases/{purchase_id}')
        
        if success and data.get('id') == purchase_id:
            # Verify all date fields are present and properly formatted
            date_fields = ['order_date', 'expected_delivery', 'delivered_date']
            all_dates_present = all(field in data and data[field] for field in date_fields)
            
            if all_dates_present:
                self.log_test("Purchase Retrieval with Dates", True, 
                            f"- All date fields present and formatted")
                return True
            else:
                missing_fields = [field for field in date_fields if not data.get(field)]
                self.log_test("Purchase Retrieval with Dates", False, 
                            f"- Missing or null date fields: {missing_fields}")
                return False
        else:
            self.log_test("Purchase Retrieval with Dates", False, 
                        f"- Status: {status}, Error: {data}")
            return False

    def test_dashboard_stats_with_dates(self):
        """Test dashboard stats showing recent purchases with proper date formatting"""
        print("\n🔍 Testing Dashboard Stats with Date Formatting")
        
        success, data, status = self.make_request('GET', 'dashboard/stats')
        
        if success and 'recent_purchases' in data:
            recent_purchases = data['recent_purchases']
            if recent_purchases:
                # Check if recent purchases have properly formatted dates
                first_purchase = recent_purchases[0]
                has_dates = 'order_date' in first_purchase and first_purchase['order_date']
                
                if has_dates:
                    self.log_test("Dashboard Stats with Dates", True, 
                                f"- Recent purchases show formatted dates: {first_purchase['order_date']}")
                    return True
                else:
                    self.log_test("Dashboard Stats with Dates", False, 
                                f"- Recent purchases missing date formatting")
                    return False
            else:
                self.log_test("Dashboard Stats with Dates", True, 
                            f"- No recent purchases to test (empty state)")
                return True
        else:
            self.log_test("Dashboard Stats with Dates", False, 
                        f"- Status: {status}, Error: {data}")
            return False

    def test_purchases_list_with_dates(self):
        """Test getting all purchases with proper date formatting"""
        print("\n🔍 Testing Purchases List with Date Formatting")
        
        success, data, status = self.make_request('GET', 'purchases')
        
        if success and isinstance(data, list):
            if data:  # If there are purchases
                # Check first purchase for date formatting
                first_purchase = data[0]
                has_order_date = 'order_date' in first_purchase and first_purchase['order_date']
                
                if has_order_date:
                    self.log_test("Purchases List with Dates", True, 
                                f"- Purchases list shows formatted dates: {first_purchase['order_date']}")
                    return True
                else:
                    self.log_test("Purchases List with Dates", False, 
                                f"- Purchases list missing date formatting")
                    return False
            else:
                self.log_test("Purchases List with Dates", True, 
                            f"- No purchases to test (empty state)")
                return True
        else:
            self.log_test("Purchases List with Dates", False, 
                        f"- Status: {status}, Error: {data}")
            return False

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        for purchase_id in self.created_purchases:
            success, data, status = self.make_request('DELETE', f'purchases/{purchase_id}')
            if success:
                print(f"✅ Deleted purchase {purchase_id}")
            else:
                print(f"❌ Failed to delete purchase {purchase_id}")

    def run_date_serialization_tests(self):
        """Run focused tests on date serialization issues"""
        print("🚀 Starting Date Serialization Tests")
        print("🎯 Focus: Testing the BSON date serialization fix")
        print(f"📡 Testing API at: {self.api_url}")
        print("=" * 70)

        # Test the main issue: Purchase creation with dates (was failing before)
        purchase_id = self.test_purchase_creation_with_dates()
        
        if purchase_id:
            # Test date updates
            self.test_purchase_date_updates(purchase_id)
            
            # Test date retrieval
            self.test_purchase_retrieval_with_dates(purchase_id)
            
            # Test dashboard stats with dates
            self.test_dashboard_stats_with_dates()
            
            # Test purchases list with dates
            self.test_purchases_list_with_dates()

        # Cleanup
        self.cleanup()

        # Print results
        print("\n" + "=" * 70)
        print(f"📊 Date Serialization Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All date serialization tests passed! The BSON fix is working correctly.")
            return 0
        else:
            print("⚠️  Some date serialization tests failed!")
            return 1

def main():
    tester = DateSerializationTester()
    return tester.run_date_serialization_tests()

if __name__ == "__main__":
    sys.exit(main())
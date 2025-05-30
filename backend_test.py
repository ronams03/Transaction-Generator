
import requests
import json
import time
from datetime import datetime

class PayPalMockAPITester:
    def __init__(self, base_url="https://62877d42-3d49-4e20-ac60-3297ca55f69f.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.text else {}
                    return True, response_data
                except json.JSONDecodeError:
                    # For non-JSON responses (like blobs)
                    return True, response.content
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_api_info(self):
        """Test the API info endpoint"""
        success, data = self.run_test(
            "API Info Endpoint",
            "GET",
            "",
            200
        )
        
        if success:
            print(f"API Version: {data.get('version')}")
            print(f"Available Endpoints: {', '.join(data.get('endpoints', []))}")
        
        self.test_results.append({
            "name": "API Info Endpoint",
            "success": success
        })
        return success

    def test_generate_transactions(self, count=10, transaction_type=None, status=None):
        """Test transaction generation"""
        data = {
            "count": count
        }
        
        if transaction_type:
            data["transaction_type"] = transaction_type
        
        if status:
            data["status"] = status
            
        success, response = self.run_test(
            f"Generate {count} Transactions" + 
            (f" of type '{transaction_type}'" if transaction_type else "") +
            (f" with status '{status}'" if status else ""),
            "POST",
            "transactions/generate",
            200,
            data=data
        )
        
        if success:
            print(f"Generated {len(response)} transactions")
            if response and len(response) > 0:
                sample = response[0]
                print(f"Sample Transaction ID: {sample.get('transaction_id')}")
                print(f"Sample Type: {sample.get('transaction_type')}")
                print(f"Sample Status: {sample.get('status')}")
                
                # Verify transaction type if specified
                if transaction_type and sample.get('transaction_type') != transaction_type:
                    print(f"❌ Transaction type mismatch: expected {transaction_type}, got {sample.get('transaction_type')}")
                    success = False
                
                # Verify status if specified
                if status and sample.get('status') != status:
                    print(f"❌ Status mismatch: expected {status}, got {sample.get('status')}")
                    success = False
        
        self.test_results.append({
            "name": f"Generate Transactions ({count})" + 
                  (f" of type '{transaction_type}'" if transaction_type else "") +
                  (f" with status '{status}'" if status else ""),
            "success": success
        })
        return success

    def test_get_transactions(self, limit=50, skip=0, transaction_type=None, status=None):
        """Test fetching transactions"""
        params = {
            "limit": limit,
            "skip": skip
        }
        
        if transaction_type:
            params["transaction_type"] = transaction_type
        
        if status:
            params["status"] = status
            
        success, response = self.run_test(
            "Get Transactions" + 
            (f" of type '{transaction_type}'" if transaction_type else "") +
            (f" with status '{status}'" if status else ""),
            "GET",
            "transactions",
            200,
            params=params
        )
        
        if success:
            print(f"Retrieved {len(response)} transactions")
            
            # Verify filters if specified
            if transaction_type or status:
                for tx in response:
                    if transaction_type and tx.get('transaction_type') != transaction_type:
                        print(f"❌ Transaction type filter not working: found {tx.get('transaction_type')}")
                        success = False
                        break
                    
                    if status and tx.get('status') != status:
                        print(f"❌ Status filter not working: found {tx.get('status')}")
                        success = False
                        break
        
        self.test_results.append({
            "name": "Get Transactions" + 
                  (f" of type '{transaction_type}'" if transaction_type else "") +
                  (f" with status '{status}'" if status else ""),
            "success": success
        })
        return success

    def test_get_stats(self):
        """Test getting transaction statistics"""
        success, data = self.run_test(
            "Get Transaction Stats",
            "GET",
            "transactions/stats",
            200
        )
        
        if success:
            print(f"Total Transactions: {data.get('total_transactions')}")
            print(f"Recent Transactions (7 days): {data.get('recent_transactions')}")
            print(f"Transaction Types: {', '.join(data.get('by_type', {}).keys())}")
            print(f"Transaction Statuses: {', '.join(data.get('by_status', {}).keys())}")
        
        self.test_results.append({
            "name": "Get Transaction Stats",
            "success": success
        })
        return success

    def test_export_transactions(self, format="json"):
        """Test exporting transactions"""
        data = {
            "format": format
        }
        
        success, response = self.run_test(
            f"Export Transactions as {format.upper()}",
            "POST",
            "transactions/export",
            200,
            data=data
        )
        
        if success:
            if format == "json":
                try:
                    # For JSON, we should be able to parse it
                    if isinstance(response, bytes):
                        json_data = json.loads(response.decode('utf-8'))
                        print(f"Successfully exported {len(json_data)} transactions as JSON")
                    else:
                        print(f"Successfully exported transactions as JSON")
                except Exception as e:
                    print(f"❌ Failed to parse JSON response: {str(e)}")
                    success = False
            else:
                # For CSV, just check if we got data
                if response:
                    print(f"Successfully exported transactions as CSV")
                else:
                    print("❌ Empty CSV response")
                    success = False
        
        self.test_results.append({
            "name": f"Export Transactions as {format.upper()}",
            "success": success
        })
        return success

    def test_clear_transactions(self):
        """Test clearing all transactions"""
        success, data = self.run_test(
            "Clear All Transactions",
            "DELETE",
            "transactions",
            200
        )
        
        if success:
            print(f"Cleared {data.get('message', '')}")
            
            # Verify transactions were actually cleared
            verify_success, verify_data = self.run_test(
                "Verify Transactions Cleared",
                "GET",
                "transactions",
                200
            )
            
            if verify_success:
                if len(verify_data) == 0:
                    print("✅ Verified all transactions were cleared")
                else:
                    print(f"❌ Transactions not cleared, found {len(verify_data)} remaining")
                    success = False
        
        self.test_results.append({
            "name": "Clear All Transactions",
            "success": success
        })
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting PayPal Mock API Tests")
        print("=" * 50)
        
        # Test API info
        self.test_api_info()
        
        # Clear any existing transactions to start fresh
        self.test_clear_transactions()
        
        # Test generating transactions with different parameters
        self.test_generate_transactions(count=10)
        self.test_generate_transactions(count=5, transaction_type="payment")
        self.test_generate_transactions(count=5, transaction_type="refund")
        self.test_generate_transactions(count=5, status="completed")
        self.test_generate_transactions(count=5, status="pending")
        
        # Test fetching transactions with filters
        self.test_get_transactions()
        self.test_get_transactions(transaction_type="payment")
        self.test_get_transactions(status="completed")
        
        # Test statistics
        self.test_get_stats()
        
        # Test exports
        self.test_export_transactions(format="json")
        self.test_export_transactions(format="csv")
        
        # Test clearing transactions
        self.test_clear_transactions()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run} ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = PayPalMockAPITester()
    tester.run_all_tests()
      
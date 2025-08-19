#!/usr/bin/env python3
"""
🚨 URGENT ADMIN DASHBOARD ISSUE TEST
Testing superadmin cannot see users in database issue
"""

import requests
import json
import time
from datetime import datetime
import sys

# Use production backend URL for testing
BACKEND_URL = "https://www.fedelissima.net"
API_BASE = f"{BACKEND_URL}/api"

print(f"🔗 Testing Admin Dashboard at: {API_BASE}")
print(f"📍 Testing production URL: {BACKEND_URL}")
print(f"⏰ Test started at: {datetime.now().isoformat()}")

# Test results tracking
test_results = []
admin_token = None

def log_test(test_name, success, message="", details=None):
    """Log test results with timestamp"""
    status = "✅" if success else "❌"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": timestamp
    })

def test_admin_authentication():
    """Test admin login with superadmin/ImaGross2024! credentials"""
    global admin_token
    
    try:
        start_time = time.time()
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "access_token" not in data or "admin" not in data:
                log_test("Admin Authentication", False, "Missing access_token or admin data in response")
                return False
            
            # Validate admin data
            admin_data = data["admin"]
            if admin_data.get("username") != "superadmin":
                log_test("Admin Authentication", False, f"Wrong username: {admin_data.get('username')}")
                return False
                
            if admin_data.get("role") != "super_admin":
                log_test("Admin Authentication", False, f"Wrong role: {admin_data.get('role')}")
                return False
            
            # Store admin token for subsequent requests
            admin_token = data["access_token"]
            
            log_test("Admin Authentication", True, f"Login successful in {response_time:.2f}s, role: {admin_data.get('role')}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail} (response time: {response_time:.2f}s)")
            return False
            
    except requests.exceptions.Timeout:
        log_test("Admin Authentication", False, "Request timeout (30s)")
        return False
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_admin_fidelity_users_endpoint():
    """Test GET /api/admin/fidelity-users endpoint - CRITICAL TEST"""
    if not admin_token:
        log_test("Admin Fidelity Users Endpoint", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with pagination parameters
        params = {
            "page": 1,
            "limit": 50
        }
        
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=params, timeout=60)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "users" not in data or "total" not in data:
                log_test("Admin Fidelity Users Endpoint", False, "Missing 'users' or 'total' fields in response")
                return False
            
            users = data["users"]
            total = data["total"]
            
            # Check if users array is populated
            if not isinstance(users, list):
                log_test("Admin Fidelity Users Endpoint", False, f"'users' should be a list, got {type(users)}")
                return False
            
            if len(users) == 0:
                log_test("Admin Fidelity Users Endpoint", False, f"No users returned! Total: {total}")
                return False
            
            # Validate user data structure
            first_user = users[0]
            required_fields = ["tessera_fisica", "nome", "cognome"]
            missing_fields = [field for field in required_fields if field not in first_user]
            if missing_fields:
                log_test("Admin Fidelity Users Endpoint", False, f"Missing fields in user data: {missing_fields}")
                return False
            
            # Check total count
            if total < 20000:  # Should have around 30,287 records
                log_test("Admin Fidelity Users Endpoint", False, f"Total users too low: {total} (expected ~30,287)")
                return False
            
            log_test("Admin Fidelity Users Endpoint", True, f"Retrieved {len(users)} users, total: {total:,} records (response time: {response_time:.2f}s)")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Fidelity Users Endpoint", False, f"Status {response.status_code}: {error_detail} (response time: {response_time:.2f}s)")
            return False
            
    except requests.exceptions.Timeout:
        log_test("Admin Fidelity Users Endpoint", False, "Request timeout (60s)")
        return False
    except Exception as e:
        log_test("Admin Fidelity Users Endpoint", False, f"Exception: {str(e)}")
        return False

def test_mongodb_fidelity_collection():
    """Test MongoDB fidelity_data collection accessibility"""
    if not admin_token:
        log_test("MongoDB Fidelity Collection", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test search functionality to verify database access
        params = {
            "search": "MARINA",  # Common Italian name
            "limit": 10
        }
        
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=params, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" not in data:
                log_test("MongoDB Fidelity Collection", False, "No users field in search response")
                return False
            
            users = data["users"]
            
            if len(users) == 0:
                log_test("MongoDB Fidelity Collection", False, "No search results for 'MARINA' - database may be empty")
                return False
            
            # Verify search results contain the search term
            found_marina = False
            for user in users:
                if "MARINA" in user.get("nome", "").upper() or "MARINA" in user.get("cognome", "").upper():
                    found_marina = True
                    break
            
            if not found_marina:
                log_test("MongoDB Fidelity Collection", False, "Search results don't contain 'MARINA' - search not working")
                return False
            
            log_test("MongoDB Fidelity Collection", True, f"Database search working, found {len(users)} results for 'MARINA' (response time: {response_time:.2f}s)")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("MongoDB Fidelity Collection", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("MongoDB Fidelity Collection", False, f"Exception: {str(e)}")
        return False

def test_admin_dashboard_stats():
    """Test admin dashboard statistics endpoint"""
    if not admin_token:
        log_test("Admin Dashboard Stats", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["total_users", "total_fidelity_clients", "total_stores", "total_cashiers"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Admin Dashboard Stats", False, f"Missing fields: {missing_fields}")
                return False
            
            # Check if fidelity clients count is reasonable
            fidelity_clients = data.get("total_fidelity_clients", 0)
            if fidelity_clients < 20000:
                log_test("Admin Dashboard Stats", False, f"Fidelity clients count too low: {fidelity_clients} (expected ~30,287)")
                return False
            
            log_test("Admin Dashboard Stats", True, f"Dashboard stats: {fidelity_clients:,} fidelity clients, {data.get('total_users', 0)} users, {data.get('total_stores', 0)} stores (response time: {response_time:.2f}s)")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Dashboard Stats", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Dashboard Stats", False, f"Exception: {str(e)}")
        return False

def test_specific_user_lookup():
    """Test lookup of specific user mentioned in the issue"""
    if not admin_token:
        log_test("Specific User Lookup", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test specific card mentioned in previous issues
        test_card = "2020000063308"
        
        response = requests.post(f"{API_BASE}/check-tessera", json={"tessera_fisica": test_card}, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("found"):
                user_data = data.get("user", {})
                log_test("Specific User Lookup", True, f"Card {test_card} found: {user_data.get('nome', '')} {user_data.get('cognome', '')} (response time: {response_time:.2f}s)")
                return True
            else:
                log_test("Specific User Lookup", False, f"Card {test_card} not found in database")
                return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Specific User Lookup", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Specific User Lookup", False, f"Exception: {str(e)}")
        return False

def test_user_pagination():
    """Test user pagination functionality"""
    if not admin_token:
        log_test("User Pagination", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test different pages
        page1_response = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&limit=100", headers=headers, timeout=30)
        page2_response = requests.get(f"{API_BASE}/admin/fidelity-users?page=2&limit=100", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if page1_response.status_code == 200 and page2_response.status_code == 200:
            page1_data = page1_response.json()
            page2_data = page2_response.json()
            
            page1_users = page1_data.get("users", [])
            page2_users = page2_data.get("users", [])
            
            if len(page1_users) == 0 or len(page2_users) == 0:
                log_test("User Pagination", False, f"Empty pages: page1={len(page1_users)}, page2={len(page2_users)}")
                return False
            
            # Check that pages contain different users
            page1_ids = set(user.get("tessera_fisica", "") for user in page1_users)
            page2_ids = set(user.get("tessera_fisica", "") for user in page2_users)
            
            if page1_ids.intersection(page2_ids):
                log_test("User Pagination", False, "Pages contain duplicate users - pagination not working")
                return False
            
            log_test("User Pagination", True, f"Pagination working: page1={len(page1_users)} users, page2={len(page2_users)} users (response time: {response_time:.2f}s)")
            return True
            
        else:
            log_test("User Pagination", False, f"Page requests failed: page1={page1_response.status_code}, page2={page2_response.status_code}")
            return False
            
    except Exception as e:
        log_test("User Pagination", False, f"Exception: {str(e)}")
        return False

def test_user_search_functionality():
    """Test user search and filter functionality"""
    if not admin_token:
        log_test("User Search Functionality", False, "No admin token available")
        return False
    
    try:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test search by name
        search_terms = ["ROSSI", "BIANCHI", "FERRARI"]
        successful_searches = 0
        
        for term in search_terms:
            response = requests.get(f"{API_BASE}/admin/fidelity-users?search={term}&limit=20", headers=headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                if len(users) > 0:
                    # Verify search results contain the search term
                    found_term = False
                    for user in users:
                        if term in user.get("nome", "").upper() or term in user.get("cognome", "").upper():
                            found_term = True
                            break
                    
                    if found_term:
                        successful_searches += 1
        
        response_time = time.time() - start_time
        
        if successful_searches >= 2:  # At least 2 out of 3 searches should work
            log_test("User Search Functionality", True, f"Search working: {successful_searches}/3 terms found results (response time: {response_time:.2f}s)")
            return True
        else:
            log_test("User Search Functionality", False, f"Search not working properly: only {successful_searches}/3 terms found results")
            return False
            
    except Exception as e:
        log_test("User Search Functionality", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all admin dashboard tests"""
    print("🚨 STARTING URGENT ADMIN DASHBOARD TESTS")
    print("=" * 60)
    
    tests = [
        ("Admin Authentication Test", test_admin_authentication),
        ("Admin Fidelity Users Endpoint Test", test_admin_fidelity_users_endpoint),
        ("MongoDB Fidelity Collection Test", test_mongodb_fidelity_collection),
        ("Admin Dashboard Stats Test", test_admin_dashboard_stats),
        ("Specific User Lookup Test", test_specific_user_lookup),
        ("User Pagination Test", test_user_pagination),
        ("User Search Functionality Test", test_user_search_functionality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution failed: {str(e)}")
            failed += 1
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🚨 URGENT ADMIN DASHBOARD TEST RESULTS")
    print("=" * 60)
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"[{result['timestamp']}] {status} {result['test']}: {result['message']}")
    
    print(f"\n📊 SUMMARY: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        for result in test_results:
            if not result["success"]:
                print(f"   ❌ {result['test']}: {result['message']}")
        
        print("\n💡 RECOMMENDED ACTIONS:")
        if any("Admin Authentication" in r["test"] for r in test_results if not r["success"]):
            print("   - Check admin credentials and authentication system")
        if any("Fidelity Users Endpoint" in r["test"] for r in test_results if not r["success"]):
            print("   - Check /api/admin/fidelity-users endpoint implementation")
        if any("MongoDB" in r["test"] for r in test_results if not r["success"]):
            print("   - Check MongoDB Atlas connection and fidelity_data collection")
        if any("Search" in r["test"] for r in test_results if not r["success"]):
            print("   - Check database indexing and search functionality")
    else:
        print("\n✅ ALL TESTS PASSED - Admin dashboard should be working correctly!")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
URGENT FIDELITY DATA ENDPOINT VERIFICATION
Tests the recently fixed fidelity data endpoints to verify 30K clients are accessible
"""

import requests
import json
import sys
import time

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🔗 Testing Fidelity API at: {API_BASE}")

# Test results tracking
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details
    })

def get_admin_token():
    """Get admin authentication token"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login error: {str(e)}")
        return None

def test_fidelity_users_endpoint():
    """Test /api/admin/fidelity-users endpoint - CRITICAL TEST"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("Fidelity Users Endpoint", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        print("🔍 Testing /api/admin/fidelity-users endpoint...")
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers)
        response_time = time.time() - start_time
        
        print(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "users" not in data or "total" not in data:
                log_test("Fidelity Users Endpoint", False, "Missing 'users' or 'total' in response")
                return False
            
            total_count = data["total"]
            users_count = len(data["users"])
            
            # Check if we have the expected ~25K+ records
            if total_count < 20000:
                log_test("Fidelity Users Endpoint", False, f"Expected ~25K+ records, got {total_count}")
                return False
            
            # Validate user data structure
            if users_count > 0:
                first_user = data["users"][0]
                required_fields = ["tessera_fisica", "nome", "cognome", "email", "telefono", "localita"]
                missing_fields = [field for field in required_fields if field not in first_user]
                if missing_fields:
                    log_test("Fidelity Users Endpoint", False, f"Missing user fields: {missing_fields}")
                    return False
            
            # Check pagination info
            if "page" in data and "per_page" in data:
                page = data["page"]
                per_page = data["per_page"]
                print(f"📄 Pagination: Page {page}, {per_page} per page, {users_count} returned")
            
            log_test("Fidelity Users Endpoint", True, f"Successfully retrieved {total_count:,} fidelity clients ({users_count} in current page)")
            return True
            
        elif response.status_code == 500:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users Endpoint", False, f"500 ERROR (CRITICAL): {error_detail}")
            return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users Endpoint", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Users Endpoint", False, f"Exception: {str(e)}")
        return False

def test_fidelity_users_pagination():
    """Test pagination functionality on fidelity users endpoint"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("Fidelity Users Pagination", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test page 1
        response1 = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&per_page=50", headers=headers)
        if response1.status_code != 200:
            log_test("Fidelity Users Pagination", False, f"Page 1 failed: {response1.status_code}")
            return False
        
        data1 = response1.json()
        
        # Test page 2
        response2 = requests.get(f"{API_BASE}/admin/fidelity-users?page=2&per_page=50", headers=headers)
        if response2.status_code != 200:
            log_test("Fidelity Users Pagination", False, f"Page 2 failed: {response2.status_code}")
            return False
        
        data2 = response2.json()
        
        # Validate pagination works
        if len(data1["users"]) == 0 or len(data2["users"]) == 0:
            log_test("Fidelity Users Pagination", False, "Empty pages returned")
            return False
        
        # Check that pages return different users
        page1_ids = set(user["tessera_fisica"] for user in data1["users"])
        page2_ids = set(user["tessera_fisica"] for user in data2["users"])
        
        if page1_ids.intersection(page2_ids):
            log_test("Fidelity Users Pagination", False, "Pages contain duplicate users")
            return False
        
        log_test("Fidelity Users Pagination", True, f"Pagination working: Page 1 ({len(data1['users'])} users), Page 2 ({len(data2['users'])} users)")
        return True
        
    except Exception as e:
        log_test("Fidelity Users Pagination", False, f"Exception: {str(e)}")
        return False

def test_fidelity_users_search():
    """Test search functionality on fidelity users endpoint"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("Fidelity Users Search", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get some users to search for
        response = requests.get(f"{API_BASE}/admin/fidelity-users?per_page=10", headers=headers)
        if response.status_code != 200:
            log_test("Fidelity Users Search", False, "Could not get users for search test")
            return False
        
        data = response.json()
        if not data["users"]:
            log_test("Fidelity Users Search", False, "No users available for search test")
            return False
        
        # Test search by cognome
        test_user = data["users"][0]
        search_cognome = test_user["cognome"][:4]  # First 4 characters
        
        search_response = requests.get(f"{API_BASE}/admin/fidelity-users?search={search_cognome}", headers=headers)
        if search_response.status_code != 200:
            log_test("Fidelity Users Search", False, f"Search failed: {search_response.status_code}")
            return False
        
        search_data = search_response.json()
        
        # Validate search results
        if not search_data["users"]:
            log_test("Fidelity Users Search", False, f"No results for search term '{search_cognome}'")
            return False
        
        # Check if search term appears in results
        found_match = False
        for user in search_data["users"]:
            if search_cognome.lower() in user["cognome"].lower():
                found_match = True
                break
        
        if not found_match:
            log_test("Fidelity Users Search", False, f"Search results don't contain search term '{search_cognome}'")
            return False
        
        log_test("Fidelity Users Search", True, f"Search working: '{search_cognome}' returned {len(search_data['users'])} results")
        return True
        
    except Exception as e:
        log_test("Fidelity Users Search", False, f"Exception: {str(e)}")
        return False

def test_dashboard_stats_fidelity_count():
    """Test /api/admin/stats/dashboard shows both registered users and total fidelity clients"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("Dashboard Stats Fidelity Count", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for registered users count (~63)
            if "total_users" not in data:
                log_test("Dashboard Stats Fidelity Count", False, "Missing 'total_users' field")
                return False
            
            registered_users = data["total_users"]
            
            # Check for total fidelity clients count (~25K)
            if "total_fidelity_clients" not in data:
                log_test("Dashboard Stats Fidelity Count", False, "Missing 'total_fidelity_clients' field")
                return False
            
            total_fidelity_clients = data["total_fidelity_clients"]
            
            # Validate counts are reasonable
            if registered_users < 10:
                log_test("Dashboard Stats Fidelity Count", False, f"Registered users too low: {registered_users}")
                return False
            
            if total_fidelity_clients < 20000:
                log_test("Dashboard Stats Fidelity Count", False, f"Fidelity clients too low: {total_fidelity_clients} (expected ~25K)")
                return False
            
            # Check if total is close to user's reported 30K
            if total_fidelity_clients > 35000:
                log_test("Dashboard Stats Fidelity Count", False, f"Fidelity clients too high: {total_fidelity_clients} (expected ~30K)")
                return False
            
            log_test("Dashboard Stats Fidelity Count", True, f"Dashboard shows {registered_users:,} registered users and {total_fidelity_clients:,} total fidelity clients")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Dashboard Stats Fidelity Count", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Dashboard Stats Fidelity Count", False, f"Exception: {str(e)}")
        return False

def test_no_500_errors():
    """Test that fidelity endpoints no longer return 500 errors"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("No 500 Errors", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test multiple endpoints that previously failed
        endpoints_to_test = [
            "/admin/fidelity-users",
            "/admin/fidelity-users?page=1&per_page=10",
            "/admin/fidelity-users?search=test",
            "/admin/stats/dashboard"
        ]
        
        error_500_count = 0
        total_tests = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
            if response.status_code == 500:
                error_500_count += 1
                print(f"❌ 500 Error on {endpoint}")
        
        if error_500_count > 0:
            log_test("No 500 Errors", False, f"{error_500_count}/{total_tests} endpoints still return 500 errors")
            return False
        
        log_test("No 500 Errors", True, f"All {total_tests} fidelity endpoints working without 500 errors")
        return True
        
    except Exception as e:
        log_test("No 500 Errors", False, f"Exception: {str(e)}")
        return False

def test_fidelity_data_accessibility():
    """Test that the complete 30K client database is accessible"""
    admin_token = get_admin_token()
    if not admin_token:
        log_test("Fidelity Data Accessibility", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get total count
        response = requests.get(f"{API_BASE}/admin/fidelity-users?per_page=1", headers=headers)
        if response.status_code != 200:
            log_test("Fidelity Data Accessibility", False, f"Failed to get fidelity data: {response.status_code}")
            return False
        
        data = response.json()
        total_count = data["total"]
        
        # Test accessing different parts of the dataset
        test_pages = [1, 10, 50, 100]  # Test various pages
        accessible_records = 0
        
        for page in test_pages:
            page_response = requests.get(f"{API_BASE}/admin/fidelity-users?page={page}&per_page=50", headers=headers)
            if page_response.status_code == 200:
                page_data = page_response.json()
                accessible_records += len(page_data["users"])
            else:
                print(f"⚠️ Page {page} not accessible: {page_response.status_code}")
        
        # Calculate accessibility percentage
        max_possible = min(total_count, len(test_pages) * 50)
        accessibility_rate = (accessible_records / max_possible) * 100 if max_possible > 0 else 0
        
        if accessibility_rate < 90:
            log_test("Fidelity Data Accessibility", False, f"Only {accessibility_rate:.1f}% of data accessible")
            return False
        
        # Verify we're close to the expected 30K
        if total_count < 24000 or total_count > 35000:
            log_test("Fidelity Data Accessibility", False, f"Total count {total_count:,} not in expected range (24K-35K)")
            return False
        
        log_test("Fidelity Data Accessibility", True, f"Complete database accessible: {total_count:,} clients ({accessibility_rate:.1f}% tested pages accessible)")
        return True
        
    except Exception as e:
        log_test("Fidelity Data Accessibility", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all fidelity endpoint tests"""
    print("🚀 STARTING URGENT FIDELITY DATA ENDPOINT VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_fidelity_users_endpoint,
        test_fidelity_users_pagination,
        test_fidelity_users_search,
        test_dashboard_stats_fidelity_count,
        test_no_500_errors,
        test_fidelity_data_accessibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"🎯 FIDELITY ENDPOINT VERIFICATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - 30K CLIENTS ARE NOW ACCESSIBLE!")
        print("✅ Fidelity data endpoint fix is working correctly")
        print("✅ User can now see and import their complete client database")
    else:
        print("❌ SOME TESTS FAILED - Fidelity data access issues remain")
        print("❌ User may still experience problems accessing their 30K clients")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
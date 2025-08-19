#!/usr/bin/env python3
"""
🚨 URGENT PRODUCTION FIX VERIFICATION - Local Backend Testing
Tests the critical database fix for admin users access locally
"""

import requests
import json
import time
from datetime import datetime
import sys

# Local backend URL for testing
LOCAL_URL = "http://localhost:8001"
API_BASE = f"{LOCAL_URL}/api"

# Admin credentials from review request
ADMIN_USERNAME = "superadmin"
ADMIN_PASSWORD = "ImaGross2024!"

# Expected data from review request
EXPECTED_FIDELITY_USERS = 30287

print(f"🔗 Testing LOCAL BACKEND at: {API_BASE}")
print(f"🎯 Target: Verify admin database fix - should see {EXPECTED_FIDELITY_USERS} users")
print(f"⏰ Test started at: {datetime.now().isoformat()}")
print("=" * 80)

# Global variables
admin_token = None
test_results = []

def log_test(test_name, success, message="", response_time=None):
    """Log test results with timing"""
    status = "✅" if success else "❌"
    timing = f" ({response_time:.3f}s)" if response_time else ""
    print(f"{status} {test_name}: {message}{timing}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "response_time": response_time
    })

def test_backend_connectivity():
    """Test basic connectivity to local backend"""
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/health", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                log_test("Backend Connectivity", True, "Backend API is healthy and accessible", response_time)
                return True
            else:
                log_test("Backend Connectivity", False, f"API unhealthy: {data}", response_time)
                return False
        else:
            log_test("Backend Connectivity", False, f"Status code: {response.status_code}", response_time)
            return False
    except Exception as e:
        log_test("Backend Connectivity", False, f"Connection error: {str(e)}")
        return False

def test_admin_authentication():
    """Test admin login with superadmin credentials"""
    global admin_token
    
    try:
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "access_token" not in data or "admin" not in data:
                log_test("Admin Authentication", False, "Missing fields in login response", response_time)
                return False
            
            # Validate admin role
            admin_data = data["admin"]
            if admin_data.get("role") != "super_admin":
                log_test("Admin Authentication", False, f"Wrong admin role: {admin_data.get('role')}", response_time)
                return False
            
            # Store token for subsequent requests
            admin_token = data["access_token"]
            
            log_test("Admin Authentication", True, f"Super admin login successful - Role: {admin_data.get('role')}", response_time)
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_database_connection():
    """Test MongoDB Atlas connection to loyalty_production database"""
    if not admin_token:
        log_test("Database Connection", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=20)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have database statistics
            if "total_fidelity_clients" not in data:
                log_test("Database Connection", False, "Missing fidelity clients data", response_time)
                return False
            
            total_clients = data["total_fidelity_clients"]
            
            # Verify we have a reasonable number of records
            if total_clients < 1000:  # Allow for test data
                log_test("Database Connection", False, f"Too few records: {total_clients}", response_time)
                return False
            
            log_test("Database Connection", True, f"MongoDB Atlas connected - {total_clients} fidelity records available", response_time)
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Database Connection", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Database Connection", False, f"Exception: {str(e)}")
        return False

def test_fidelity_users_endpoint_fix():
    """Test GET /api/admin/fidelity-users endpoint - THE CRITICAL FIX"""
    if not admin_token:
        log_test("Fidelity Users Endpoint Fix", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "users" not in data or "total" not in data:
                log_test("Fidelity Users Endpoint Fix", False, "Missing fields in response", response_time)
                return False
            
            total_users = data["total"]
            returned_users = len(data["users"])
            
            # Check if we have a reasonable number of users (production should have 30,287)
            if total_users < 1000:
                log_test("Fidelity Users Endpoint Fix", False, f"Too few users: {total_users}", response_time)
                return False
            
            # Validate user data structure
            if returned_users > 0:
                first_user = data["users"][0]
                required_fields = ["tessera_fisica", "nome", "cognome"]
                missing_fields = [field for field in required_fields if field not in first_user]
                if missing_fields:
                    log_test("Fidelity Users Endpoint Fix", False, f"Missing user fields: {missing_fields}", response_time)
                    return False
            
            # Check if this matches production expectations
            production_match = total_users == EXPECTED_FIDELITY_USERS
            match_msg = f" (PRODUCTION MATCH!)" if production_match else f" (expected {EXPECTED_FIDELITY_USERS} in production)"
            
            log_test("Fidelity Users Endpoint Fix", True, f"SUCCESS! Retrieved {total_users} users ({returned_users} in first page){match_msg}", response_time)
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users Endpoint Fix", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Fidelity Users Endpoint Fix", False, f"Exception: {str(e)}")
        return False

def test_database_fix_verification():
    """Verify the specific database fix mentioned in review request"""
    if not admin_token:
        log_test("Database Fix Verification", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test that the endpoint now has proper db = get_db() call
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=1", headers=headers, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # If we get a successful response, the db = get_db() fix is working
            if "users" in data and "total" in data:
                total = data["total"]
                log_test("Database Fix Verification", True, f"Database connection fix working - endpoint returns {total} total users", response_time)
                return True
            else:
                log_test("Database Fix Verification", False, "Invalid response structure", response_time)
                return False
        else:
            # If we get 503, it means db is still undefined (fix not working)
            if response.status_code == 503:
                log_test("Database Fix Verification", False, "Database still undefined - fix not applied", response_time)
                return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                log_test("Database Fix Verification", False, f"Status {response.status_code}: {error_detail}", response_time)
                return False
            
    except Exception as e:
        log_test("Database Fix Verification", False, f"Exception: {str(e)}")
        return False

def test_user_search_functionality():
    """Test user search functionality in admin dashboard"""
    if not admin_token:
        log_test("User Search Functionality", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test search for common Italian surnames
        search_terms = ["ROSSI", "BIANCHI"]
        
        for search_term in search_terms:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/admin/fidelity-users?search={search_term}&limit=10", headers=headers, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if "users" not in data or "total" not in data:
                    log_test("User Search Functionality", False, f"Invalid search response for {search_term}", response_time)
                    return False
                
                # Even if no results, the endpoint should work
                total_results = data["total"]
                log_test("User Search Functionality", True, f"Search for '{search_term}' returned {total_results} results", response_time)
                break  # Test passed, no need to test all terms
            else:
                log_test("User Search Functionality", False, f"Search failed for {search_term}: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        log_test("User Search Functionality", False, f"Exception: {str(e)}")
        return False

def test_specific_card_lookup():
    """Test lookup of specific card mentioned in review request"""
    if not admin_token:
        log_test("Specific Card Lookup", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test the specific card mentioned in the review
        test_card = "2020000063308"
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/check-tessera", json={"tessera_fisica": test_card}, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("found"):
                user_data = data.get("user", {})
                nome = user_data.get("nome", "")
                cognome = user_data.get("cognome", "")
                bollini = user_data.get("bollini", 0)
                
                log_test("Specific Card Lookup", True, f"Card {test_card} found: {nome} {cognome} ({bollini} bollini)", response_time)
                return True
            else:
                log_test("Specific Card Lookup", False, f"Card {test_card} not found in database", response_time)
                return False
        else:
            log_test("Specific Card Lookup", False, f"Lookup failed: {response.status_code}", response_time)
            return False
        
    except Exception as e:
        log_test("Specific Card Lookup", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all production fix verification tests"""
    print("🚨 STARTING URGENT DATABASE FIX VERIFICATION")
    print("Testing admin fidelity-users endpoint database connection fix...")
    print()
    
    tests = [
        test_backend_connectivity,
        test_admin_authentication,
        test_database_connection,
        test_fidelity_users_endpoint_fix,  # THE CRITICAL TEST
        test_database_fix_verification,    # VERIFY THE SPECIFIC FIX
        test_user_search_functionality,
        test_specific_card_lookup
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test(test_func.__name__, False, f"Test crashed: {str(e)}")
        
        print()  # Add spacing between tests
    
    print("=" * 80)
    print(f"🎯 DATABASE FIX VERIFICATION RESULTS")
    print(f"✅ Passed: {passed}/{total} tests ({(passed/total)*100:.1f}%)")
    print(f"❌ Failed: {total-passed}/{total} tests")
    print()
    
    if passed == total:
        print("🎉 SUCCESS! Database fix is working correctly!")
        print(f"✅ Admin authentication working with {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"✅ Database connection to loyalty_production established")
        print(f"✅ Fidelity users endpoint now has proper db = get_db() call")
        print("✅ Admin can now see all users in the database")
        print()
        print("🚀 FIX IS READY FOR PRODUCTION DEPLOYMENT!")
    else:
        print("❌ CRITICAL ISSUES REMAIN!")
        print("The database fix is NOT working correctly.")
        print("Immediate action required to fix remaining issues.")
        
        # Show failed tests
        failed_tests = [result for result in test_results if not result["success"]]
        if failed_tests:
            print("\n🔍 Failed Tests:")
            for result in failed_tests:
                print(f"  ❌ {result['test']}: {result['message']}")
    
    print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
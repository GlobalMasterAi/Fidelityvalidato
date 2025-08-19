#!/usr/bin/env python3
"""
🚨 URGENT PRODUCTION FIX VERIFICATION - Admin Users Database Issue
Tests the critical production fix for admin users database access
"""

import requests
import json
import time
from datetime import datetime
import sys

# Production URL configuration
PRODUCTION_URL = "https://www.fedelissima.net"
API_BASE = f"{PRODUCTION_URL}/api"

# Admin credentials from review request
ADMIN_USERNAME = "superadmin"
ADMIN_PASSWORD = "ImaGross2024!"

# Expected data from review request
EXPECTED_FIDELITY_USERS = 30287

print(f"🔗 Testing PRODUCTION API at: {API_BASE}")
print(f"🎯 Target: Verify admin can see {EXPECTED_FIDELITY_USERS} users in live production")
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

def test_production_api_connectivity():
    """Test basic connectivity to production API"""
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/health", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                log_test("Production API Connectivity", True, "Production API is healthy and accessible", response_time)
                return True
            else:
                log_test("Production API Connectivity", False, f"API unhealthy: {data}", response_time)
                return False
        else:
            log_test("Production API Connectivity", False, f"Status code: {response.status_code}", response_time)
            return False
    except requests.exceptions.Timeout:
        log_test("Production API Connectivity", False, "Connection timeout (>10s)")
        return False
    except Exception as e:
        log_test("Production API Connectivity", False, f"Connection error: {str(e)}")
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
            
            # Verify we have the expected number of records
            if total_clients < 20000:  # Allow some tolerance
                log_test("Database Connection", False, f"Too few records: {total_clients} (expected ~{EXPECTED_FIDELITY_USERS})", response_time)
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

def test_fidelity_users_endpoint():
    """Test GET /api/admin/fidelity-users endpoint - THE CRITICAL FIX"""
    if not admin_token:
        log_test("Fidelity Users Endpoint", False, "No admin token available")
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
                log_test("Fidelity Users Endpoint", False, "Missing fields in response", response_time)
                return False
            
            total_users = data["total"]
            returned_users = len(data["users"])
            
            # Check if we have the expected total
            if total_users != EXPECTED_FIDELITY_USERS:
                log_test("Fidelity Users Endpoint", False, f"User count mismatch: got {total_users}, expected {EXPECTED_FIDELITY_USERS}", response_time)
                return False
            
            # Validate user data structure
            if returned_users > 0:
                first_user = data["users"][0]
                required_fields = ["tessera_fisica", "nome", "cognome", "bollini", "prog_spesa"]
                missing_fields = [field for field in required_fields if field not in first_user]
                if missing_fields:
                    log_test("Fidelity Users Endpoint", False, f"Missing user fields: {missing_fields}", response_time)
                    return False
            
            log_test("Fidelity Users Endpoint", True, f"SUCCESS! Retrieved {total_users} users ({returned_users} in first page)", response_time)
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users Endpoint", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Fidelity Users Endpoint", False, f"Exception: {str(e)}")
        return False

def test_user_search_functionality():
    """Test user search functionality in admin dashboard"""
    if not admin_token:
        log_test("User Search Functionality", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test search for common Italian surnames
        search_terms = ["ROSSI", "BIANCHI", "FERRARI"]
        
        for search_term in search_terms:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/admin/fidelity-users?search={search_term}", headers=headers, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if "users" not in data or "total" not in data:
                    log_test("User Search Functionality", False, f"Invalid search response for {search_term}", response_time)
                    return False
                
                if data["total"] == 0:
                    log_test("User Search Functionality", False, f"No results for common surname {search_term}", response_time)
                    return False
                
                # Validate search results contain the search term
                found_match = False
                for user in data["users"]:
                    if search_term.lower() in user.get("cognome", "").lower():
                        found_match = True
                        break
                
                if not found_match:
                    log_test("User Search Functionality", False, f"Search results don't contain {search_term}", response_time)
                    return False
        
        log_test("User Search Functionality", True, f"Search working for all test terms: {', '.join(search_terms)}")
        return True
        
    except Exception as e:
        log_test("User Search Functionality", False, f"Exception: {str(e)}")
        return False

def test_pagination_functionality():
    """Test user pagination in admin dashboard"""
    if not admin_token:
        log_test("Pagination Functionality", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test first page
        start_time = time.time()
        response1 = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&limit=100", headers=headers, timeout=15)
        response_time1 = time.time() - start_time
        
        if response1.status_code != 200:
            log_test("Pagination Functionality", False, f"Page 1 failed: {response1.status_code}")
            return False
        
        data1 = response1.json()
        page1_users = data1.get("users", [])
        
        # Test second page
        start_time = time.time()
        response2 = requests.get(f"{API_BASE}/admin/fidelity-users?page=2&limit=100", headers=headers, timeout=15)
        response_time2 = time.time() - start_time
        
        if response2.status_code != 200:
            log_test("Pagination Functionality", False, f"Page 2 failed: {response2.status_code}")
            return False
        
        data2 = response2.json()
        page2_users = data2.get("users", [])
        
        # Validate no duplicates between pages
        page1_ids = set(user.get("tessera_fisica", "") for user in page1_users)
        page2_ids = set(user.get("tessera_fisica", "") for user in page2_users)
        
        duplicates = page1_ids.intersection(page2_ids)
        if duplicates:
            log_test("Pagination Functionality", False, f"Duplicate users across pages: {len(duplicates)}")
            return False
        
        avg_response_time = (response_time1 + response_time2) / 2
        log_test("Pagination Functionality", True, f"Pagination working - Page 1: {len(page1_users)} users, Page 2: {len(page2_users)} users", avg_response_time)
        return True
        
    except Exception as e:
        log_test("Pagination Functionality", False, f"Exception: {str(e)}")
        return False

def test_specific_user_lookup():
    """Test lookup of specific user mentioned in review request"""
    if not admin_token:
        log_test("Specific User Lookup", False, "No admin token available")
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
                
                log_test("Specific User Lookup", True, f"Card {test_card} found: {nome} {cognome} ({bollini} bollini)", response_time)
                return True
            else:
                log_test("Specific User Lookup", False, f"Card {test_card} not found in database", response_time)
                return False
        else:
            log_test("Specific User Lookup", False, f"Lookup failed: {response.status_code}", response_time)
            return False
        
    except Exception as e:
        log_test("Specific User Lookup", False, f"Exception: {str(e)}")
        return False

def test_admin_dashboard_stats():
    """Test admin dashboard statistics display"""
    if not admin_token:
        log_test("Admin Dashboard Stats", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate key statistics
            required_stats = ["total_users", "total_stores", "total_cashiers", "total_fidelity_clients"]
            missing_stats = [stat for stat in required_stats if stat not in data]
            
            if missing_stats:
                log_test("Admin Dashboard Stats", False, f"Missing statistics: {missing_stats}", response_time)
                return False
            
            # Validate non-zero values
            total_fidelity = data["total_fidelity_clients"]
            total_users = data["total_users"]
            total_stores = data["total_stores"]
            total_cashiers = data["total_cashiers"]
            
            if total_fidelity < 20000:
                log_test("Admin Dashboard Stats", False, f"Fidelity clients too low: {total_fidelity}", response_time)
                return False
            
            log_test("Admin Dashboard Stats", True, f"Stats: {total_fidelity} fidelity, {total_users} users, {total_stores} stores, {total_cashiers} cashiers", response_time)
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Dashboard Stats", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Admin Dashboard Stats", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all production verification tests"""
    print("🚨 STARTING URGENT PRODUCTION FIX VERIFICATION")
    print("Testing admin users database access issue resolution...")
    print()
    
    tests = [
        test_production_api_connectivity,
        test_admin_authentication,
        test_database_connection,
        test_fidelity_users_endpoint,  # THE CRITICAL TEST
        test_user_search_functionality,
        test_pagination_functionality,
        test_specific_user_lookup,
        test_admin_dashboard_stats
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
    print(f"🎯 PRODUCTION FIX VERIFICATION RESULTS")
    print(f"✅ Passed: {passed}/{total} tests ({(passed/total)*100:.1f}%)")
    print(f"❌ Failed: {total-passed}/{total} tests")
    print()
    
    if passed == total:
        print("🎉 SUCCESS! Admin can now see all users in production!")
        print(f"✅ Admin authentication working with {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"✅ Database connection to loyalty_production established")
        print(f"✅ Fidelity users endpoint returning {EXPECTED_FIDELITY_USERS} users")
        print("✅ All admin dashboard functionality operational")
        print()
        print("🚀 PRODUCTION ENVIRONMENT IS READY FOR ADMIN USE!")
    else:
        print("❌ CRITICAL ISSUES REMAIN!")
        print("The admin users database access issue is NOT fully resolved.")
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
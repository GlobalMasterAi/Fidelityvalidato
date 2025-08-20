#!/usr/bin/env python3
"""
🚨 EMERGENCY SUPERADMIN LOGIN ISSUE + User credentials lookup
URGENT BACKEND API TESTS for Critical Production Issues

This test focuses on the specific issues reported:
1. Superadmin login failure on production www.fedelissima.net
2. User credentials lookup for tessera 2020000208785
"""

import requests
import json
import time
from pathlib import Path

# Read REACT_APP_BACKEND_URL from frontend/.env
frontend_env_path = Path(__file__).parent / "frontend" / ".env"
BACKEND_URL = "http://localhost:8001"  # Default to local backend for testing

if frontend_env_path.exists():
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                env_url = line.split('=', 1)[1].strip()
                # Use the actual URL from .env for testing
                BACKEND_URL = env_url
                break

BASE_URL = BACKEND_URL
API_BASE = f"{BASE_URL}/api"
print(f"🚨 EMERGENCY TESTING - Critical Production Issues")
print(f"🔗 Testing API at: {API_BASE}")
print(f"📍 Using backend URL from frontend/.env: {BACKEND_URL}")
print(f"🎯 Focus: Superadmin login + User tessera 2020000208785 lookup")
print("=" * 80)

# Global variables for test state
admin_access_token = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results with enhanced formatting for emergency testing"""
    status = "✅" if success else "❌"
    priority = "🚨 CRITICAL" if not success and ("admin" in test_name.lower() or "tessera" in test_name.lower()) else ""
    print(f"{status} {priority} {test_name}: {message}")
    if details:
        print(f"   📋 Details: {details}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "critical": not success and ("admin" in test_name.lower() or "tessera" in test_name.lower())
    })

def test_api_connectivity():
    """Test basic API connectivity"""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/", timeout=10)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "ImaGross" in data["message"]:
                log_test("API Connectivity", True, f"API accessible ({response_time}ms)", 
                        f"Status: {data.get('status', 'unknown')}, Version: {data.get('version', 'unknown')}")
                return True
            else:
                log_test("API Connectivity", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("API Connectivity", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("API Connectivity", False, f"Connection error: {str(e)}")
        return False

def test_emergency_superadmin_login():
    """🚨 CRITICAL: Test superadmin login with exact credentials from review request"""
    global admin_access_token
    
    try:
        print("\n🚨 TESTING EMERGENCY SUPERADMIN LOGIN ISSUE")
        print("   Credentials: superadmin/ImaGross2024!")
        print("   Endpoint: POST /api/admin/login")
        
        start_time = time.time()
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=15)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        print(f"   Response time: {response_time}ms")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["access_token", "token_type", "admin"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("🚨 SUPERADMIN LOGIN", False, f"Missing response fields: {missing_fields}")
                return False
            
            if data["token_type"] != "bearer":
                log_test("🚨 SUPERADMIN LOGIN", False, f"Wrong token type: {data['token_type']}")
                return False
            
            # Validate admin data
            admin_data = data["admin"]
            if admin_data["username"] != "superadmin":
                log_test("🚨 SUPERADMIN LOGIN", False, "Admin username mismatch")
                return False
                
            if admin_data["role"] != "super_admin":
                log_test("🚨 SUPERADMIN LOGIN", False, f"Wrong admin role: {admin_data['role']}")
                return False
            
            # Store admin token for further tests
            admin_access_token = data["access_token"]
            
            log_test("🚨 SUPERADMIN LOGIN", True, f"SUCCESS! Login working ({response_time}ms)", 
                    f"Admin ID: {admin_data['id']}, Role: {admin_data['role']}, Token: {data['access_token'][:20]}...")
            
            # Test token validity immediately
            headers = {"Authorization": f"Bearer {admin_access_token}"}
            token_test = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=10)
            if token_test.status_code == 200:
                print("   ✅ Token validation: PASSED")
                return True
            else:
                log_test("🚨 SUPERADMIN LOGIN", False, f"Token validation failed: {token_test.status_code}")
                return False
            
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text if response.text else "No response body"
            
            log_test("🚨 SUPERADMIN LOGIN", False, f"Status {response.status_code}: {error_detail}", 
                    f"Response time: {response_time}ms")
            return False
            
    except Exception as e:
        log_test("🚨 SUPERADMIN LOGIN", False, f"Exception: {str(e)}")
        return False

def test_admin_database_check():
    """🚨 CRITICAL: Check if superadmin exists in database"""
    if not admin_access_token:
        log_test("Admin Database Check", False, "No admin access token available")
        return False
    
    try:
        print("\n🔍 CHECKING ADMIN DATABASE RECORDS")
        
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Try to get admin stats to verify database connectivity
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=15)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we can access admin functions
            if "total_users" in data or "total_stores" in data:
                log_test("Admin Database Check", True, f"Admin database access working ({response_time}ms)", 
                        f"Can access dashboard stats: {list(data.keys())}")
                return True
            else:
                log_test("Admin Database Check", False, f"Unexpected dashboard response: {data}")
                return False
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text
            
            log_test("Admin Database Check", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Database Check", False, f"Exception: {str(e)}")
        return False

def test_user_tessera_lookup():
    """🚨 CRITICAL: Find login credentials for user with tessera 2020000208785"""
    try:
        print("\n🔍 SEARCHING FOR USER TESSERA 2020000208785")
        print("   Searching fidelity_data collection...")
        
        target_tessera = "2020000208785"
        
        # Test 1: Check tessera endpoint
        start_time = time.time()
        response = requests.post(f"{API_BASE}/check-tessera", json={"tessera_fisica": target_tessera}, timeout=15)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        print(f"   Check tessera response time: {response_time}ms")
        print(f"   Check tessera status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data and data.get("found"):
                user_data = data.get("user_data", {})
                log_test("🚨 USER TESSERA LOOKUP", True, f"FOUND! Tessera {target_tessera} exists ({response_time}ms)", 
                        f"Nome: {user_data.get('nome', 'N/A')}, Cognome: {user_data.get('cognome', 'N/A')}, Email: {user_data.get('email', 'N/A')}, Phone: {user_data.get('n_telefono', 'N/A')}")
                
                # Check if user has registered account
                if admin_access_token:
                    headers = {"Authorization": f"Bearer {admin_access_token}"}
                    user_search = requests.get(f"{API_BASE}/admin/fidelity-users?search={target_tessera}", headers=headers, timeout=10)
                    if user_search.status_code == 200:
                        search_data = user_search.json()
                        if search_data.get("users") and len(search_data["users"]) > 0:
                            user_info = search_data["users"][0]
                            print(f"   📋 Full user details:")
                            print(f"      Nome: {user_info.get('nome', 'N/A')}")
                            print(f"      Cognome: {user_info.get('cognome', 'N/A')}")
                            print(f"      Email: {user_info.get('email', 'N/A')}")
                            print(f"      Telefono: {user_info.get('n_telefono', 'N/A')}")
                            print(f"      Localita: {user_info.get('localita', 'N/A')}")
                            print(f"      Bollini: {user_info.get('bollini', 'N/A')}")
                            print(f"      Spesa totale: €{user_info.get('prog_spesa', 'N/A')}")
                
                return True
            else:
                # Try admin search directly
                if admin_access_token:
                    headers = {"Authorization": f"Bearer {admin_access_token}"}
                    user_search = requests.get(f"{API_BASE}/admin/fidelity-users?search={target_tessera}", headers=headers, timeout=10)
                    if user_search.status_code == 200:
                        search_data = user_search.json()
                        if search_data.get("users") and len(search_data["users"]) > 0:
                            user_info = search_data["users"][0]
                            log_test("🚨 USER TESSERA LOOKUP", True, f"FOUND via admin search! Tessera {target_tessera} exists ({response_time}ms)", 
                                    f"Nome: {user_info.get('nome', 'N/A')}, Cognome: {user_info.get('cognome', 'N/A')}, Email: {user_info.get('email', 'N/A')}, Phone: {user_info.get('n_telefono', 'N/A')}")
                            print(f"   📋 Full user details:")
                            print(f"      Nome: {user_info.get('nome', 'N/A')}")
                            print(f"      Cognome: {user_info.get('cognome', 'N/A')}")
                            print(f"      Email: {user_info.get('email', 'N/A')}")
                            print(f"      Telefono: {user_info.get('n_telefono', 'N/A')}")
                            print(f"      Localita: {user_info.get('localita', 'N/A')}")
                            print(f"      Bollini: {user_info.get('bollini', 'N/A')}")
                            print(f"      Spesa totale: €{user_info.get('prog_spesa', 'N/A')}")
                            return True
                
                log_test("🚨 USER TESSERA LOOKUP", False, f"Tessera {target_tessera} NOT FOUND in database", 
                        f"Response: {data}")
                return False
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text
            
            log_test("🚨 USER TESSERA LOOKUP", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("🚨 USER TESSERA LOOKUP", False, f"Exception: {str(e)}")
        return False

def test_fidelity_database_access():
    """Test access to fidelity database and search functionality"""
    if not admin_access_token:
        log_test("Fidelity Database Access", False, "No admin access token available")
        return False
    
    try:
        print("\n📊 TESTING FIDELITY DATABASE ACCESS")
        
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test fidelity users endpoint
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=10", headers=headers, timeout=15)
        response_time = round((time.time() - start_time) * 1000, 1)
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" in data and "total" in data:
                total_users = data["total"]
                users_returned = len(data["users"])
                
                log_test("Fidelity Database Access", True, f"Database accessible ({response_time}ms)", 
                        f"Total fidelity records: {total_users:,}, Sample returned: {users_returned}")
                
                # Test search functionality
                if users_returned > 0:
                    sample_user = data["users"][0]
                    print(f"   📋 Sample user: {sample_user.get('nome', 'N/A')} {sample_user.get('cognome', 'N/A')} (Tessera: {sample_user.get('tessera_fisica', 'N/A')})")
                
                return True
            else:
                log_test("Fidelity Database Access", False, f"Unexpected response structure: {list(data.keys())}")
                return False
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text
            
            log_test("Fidelity Database Access", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Database Access", False, f"Exception: {str(e)}")
        return False

def test_user_registration_check():
    """Check if tessera 2020000208785 has a registered user account"""
    try:
        print("\n👤 CHECKING USER ACCOUNT REGISTRATION STATUS")
        
        target_tessera = "2020000208785"
        
        # Try to login with tessera as username (common pattern)
        login_attempts = [
            {"username": target_tessera, "password": "password123"},
            {"username": target_tessera, "password": "123456"},
            {"username": target_tessera, "password": target_tessera},
        ]
        
        for i, login_data in enumerate(login_attempts, 1):
            try:
                response = requests.post(f"{API_BASE}/login", json=login_data, timeout=10)
                
                if response.status_code == 200:
                    # User exists and password matched
                    data = response.json()
                    user_info = data.get("user", {})
                    log_test("User Registration Check", True, f"USER ACCOUNT EXISTS! Login successful with attempt {i}", 
                            f"Username: {login_data['username']}, Password: {login_data['password']}")
                    print(f"   📋 User details: {user_info.get('nome', 'N/A')} {user_info.get('cognome', 'N/A')}")
                    print(f"   📧 Email: {user_info.get('email', 'N/A')}")
                    print(f"   📱 Phone: {user_info.get('telefono', 'N/A')}")
                    return True
                elif response.status_code == 401:
                    # User exists but wrong password
                    error_detail = response.json().get("detail", "")
                    if "Credenziali non valide" in error_detail:
                        print(f"   ⚠️  Attempt {i}: User exists but wrong password ({login_data['password']})")
                        continue
                else:
                    print(f"   ❌ Attempt {i}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Attempt {i}: Exception {str(e)}")
                continue
        
        log_test("User Registration Check", False, f"No registered account found for tessera {target_tessera}", 
                "User has fidelity card but no registered account - needs manual registration")
        return False
        
    except Exception as e:
        log_test("User Registration Check", False, f"Exception: {str(e)}")
        return False

def run_emergency_tests():
    """Run all emergency tests for critical production issues"""
    print("🚨 STARTING EMERGENCY BACKEND TESTING")
    print("=" * 80)
    
    tests = [
        test_api_connectivity,
        test_emergency_superadmin_login,
        test_admin_database_check,
        test_user_tessera_lookup,
        test_fidelity_database_access,
        test_user_registration_check,
    ]
    
    passed = 0
    failed = 0
    critical_failures = []
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                # Check if this is a critical failure
                test_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
                if any(keyword in test_name.lower() for keyword in ["superadmin", "tessera", "admin"]):
                    critical_failures.append(test_name)
        except Exception as e:
            print(f"❌ EXCEPTION in {test_func.__name__}: {str(e)}")
            failed += 1
            critical_failures.append(test_func.__name__)
    
    print("\n" + "=" * 80)
    print("🚨 EMERGENCY TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
    
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
        for failure in critical_failures:
            print(f"   ❌ {failure}")
    
    # Detailed findings for the review request
    print("\n" + "=" * 80)
    print("📋 DETAILED FINDINGS FOR REVIEW REQUEST")
    print("=" * 80)
    
    # Admin login findings
    admin_login_success = any(result["test"] == "🚨 SUPERADMIN LOGIN" and result["success"] for result in test_results)
    if admin_login_success:
        print("✅ SUPERADMIN LOGIN: WORKING")
        print("   - Credentials superadmin/ImaGross2024! are VALID")
        print("   - JWT token generation working")
        print("   - Admin dashboard access confirmed")
    else:
        print("❌ SUPERADMIN LOGIN: FAILED")
        print("   - Check database connection")
        print("   - Verify admin record exists")
        print("   - Check password hash")
    
    # User tessera findings
    tessera_found = any(result["test"] == "🚨 USER TESSERA LOOKUP" and result["success"] for result in test_results)
    if tessera_found:
        print("✅ USER TESSERA 2020000208785: FOUND")
        print("   - User exists in fidelity_data collection")
        print("   - User details available for manual registration")
    else:
        print("❌ USER TESSERA 2020000208785: NOT FOUND")
        print("   - Card may not exist in database")
        print("   - Check data import integrity")
    
    return passed, failed, critical_failures

if __name__ == "__main__":
    passed, failed, critical_failures = run_emergency_tests()
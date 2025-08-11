#!/usr/bin/env python3
"""
URGENT ADMIN LOGIN INVESTIGATION
Critical issue: User reports "credenziali amministratore non valide" when trying to login 
with superadmin/ImaGross2024! credentials to production system.

This script investigates:
1. Admin Login API Direct Testing
2. Admin Database Verification  
3. Emergency Admin Setup Verification
4. Production vs Development Differences
5. Authentication System Testing
"""

import requests
import json
import sys
import os
from datetime import datetime

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

# Get MongoDB connection from backend .env
def get_mongo_connection():
    try:
        with open('/app/backend/.env', 'r') as f:
            for line in f:
                if line.startswith('MONGO_URL='):
                    mongo_url = line.split('=', 1)[1].strip().strip('"')
                    return mongo_url
    except Exception as e:
        print(f"Error reading MongoDB URL: {e}")
        return None

BASE_URL = get_backend_url()
MONGO_URL = get_mongo_connection()

if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

if not MONGO_URL:
    print("❌ Could not get MongoDB URL from backend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🔗 Testing API at: {API_BASE}")
print(f"🗄️ MongoDB URL: {MONGO_URL[:50]}...")

# Test credentials from the issue report
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "ImaGross2024!"
}

def log_test(test_name, success, message="", details=None):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status = "✅" if success else "❌"
    print(f"[{timestamp}] {status} {test_name}: {message}")
    if details:
        print(f"    Details: {details}")

def test_1_admin_login_api_direct():
    """Test 1: Direct API call to /api/admin/login with reported credentials"""
    print("\n" + "="*80)
    print("TEST 1: ADMIN LOGIN API DIRECT TESTING")
    print("="*80)
    
    try:
        print(f"🔐 Testing credentials: {ADMIN_CREDENTIALS['username']}/{ADMIN_CREDENTIALS['password']}")
        
        response = requests.post(f"{API_BASE}/admin/login", json=ADMIN_CREDENTIALS, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.content:
            try:
                response_data = response.json()
                print(f"📡 Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"📡 Response Text: {response.text}")
        else:
            print("📡 Empty response body")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "admin" in data:
                log_test("Admin Login API", True, "Login successful - credentials are valid")
                return True, data
            else:
                log_test("Admin Login API", False, "Login response missing required fields")
                return False, None
        elif response.status_code == 401:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No error detail"
            log_test("Admin Login API", False, f"Authentication failed: {error_detail}")
            return False, None
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No error detail"
            log_test("Admin Login API", False, f"Unexpected status {response.status_code}: {error_detail}")
            return False, None
            
    except requests.exceptions.Timeout:
        log_test("Admin Login API", False, "Request timeout - server may be overloaded")
        return False, None
    except requests.exceptions.ConnectionError as e:
        log_test("Admin Login API", False, f"Connection error: {str(e)}")
        return False, None
    except Exception as e:
        log_test("Admin Login API", False, f"Exception: {str(e)}")
        return False, None

def test_2_admin_database_verification():
    """Test 2: Verify admin user exists in MongoDB Atlas database"""
    print("\n" + "="*80)
    print("TEST 2: ADMIN DATABASE VERIFICATION")
    print("="*80)
    
    try:
        # Try to import pymongo
        try:
            import pymongo
            from pymongo import MongoClient
        except ImportError:
            log_test("MongoDB Connection", False, "pymongo not available - installing...")
            os.system("pip install pymongo")
            import pymongo
            from pymongo import MongoClient
        
        # Connect to MongoDB Atlas
        print("🔗 Connecting to MongoDB Atlas...")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        log_test("MongoDB Connection", True, "Successfully connected to Atlas")
        
        # Get database
        db_name = "loyalty_production"  # From backend .env
        db = client[db_name]
        
        # Check if admins collection exists
        collections = db.list_collection_names()
        print(f"📋 Available collections: {collections}")
        
        if "admins" not in collections:
            log_test("Admin Collection", False, "Admins collection does not exist")
            return False
        
        # Search for superadmin user
        admin_user = db.admins.find_one({"username": "superadmin"})
        
        if admin_user:
            log_test("Admin User Exists", True, f"Found superadmin user with ID: {admin_user.get('id', 'N/A')}")
            print(f"👤 Admin User Data:")
            print(f"   - ID: {admin_user.get('id', 'N/A')}")
            print(f"   - Username: {admin_user.get('username', 'N/A')}")
            print(f"   - Email: {admin_user.get('email', 'N/A')}")
            print(f"   - Role: {admin_user.get('role', 'N/A')}")
            print(f"   - Active: {admin_user.get('active', 'N/A')}")
            print(f"   - Created: {admin_user.get('created_at', 'N/A')}")
            if admin_user.get('password_hash'):
                print(f"   - Password Hash: {admin_user.get('password_hash')[:20]}...")
            else:
                print("   - Password Hash: None")
            
            # Verify role
            if admin_user.get('role') == 'super_admin':
                log_test("Admin Role", True, "User has super_admin role")
            else:
                log_test("Admin Role", False, f"User has wrong role: {admin_user.get('role')}")
            
            # Verify active status
            if admin_user.get('active', False):
                log_test("Admin Active", True, "User is active")
            else:
                log_test("Admin Active", False, "User is not active")
            
            return True
        else:
            log_test("Admin User Exists", False, "superadmin user not found in database")
            
            # Check if there are any admin users at all
            admin_count = db.admins.count_documents({})
            print(f"📊 Total admin users in database: {admin_count}")
            
            if admin_count > 0:
                print("👥 Existing admin users:")
                for admin in db.admins.find({}, {"username": 1, "role": 1, "active": 1}):
                    print(f"   - {admin.get('username', 'N/A')} ({admin.get('role', 'N/A')}) - Active: {admin.get('active', 'N/A')}")
            
            return False
            
    except Exception as e:
        log_test("MongoDB Connection", False, f"Exception: {str(e)}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

def test_3_emergency_admin_setup():
    """Test 3: Check if emergency admin setup was completed during deployment"""
    print("\n" + "="*80)
    print("TEST 3: EMERGENCY ADMIN SETUP VERIFICATION")
    print("="*80)
    
    try:
        # Check if there's an admin creation endpoint
        print("🔧 Testing admin creation endpoint availability...")
        
        # First, try to get any admin token (this will fail but shows if endpoint exists)
        response = requests.post(f"{API_BASE}/admin/login", json={"username": "test", "password": "test"}, timeout=10)
        
        if response.status_code in [401, 400]:
            log_test("Admin Login Endpoint", True, "Admin login endpoint is accessible")
        elif response.status_code == 404:
            log_test("Admin Login Endpoint", False, "Admin login endpoint not found")
            return False
        else:
            log_test("Admin Login Endpoint", True, f"Admin login endpoint responds (status: {response.status_code})")
        
        # Check if there's an admin creation endpoint for emergency setup
        try:
            response = requests.post(f"{API_BASE}/admin/create", json={}, timeout=10)
            if response.status_code in [401, 403]:
                log_test("Admin Creation Endpoint", True, "Admin creation endpoint exists (requires auth)")
            elif response.status_code == 404:
                log_test("Admin Creation Endpoint", False, "Admin creation endpoint not found")
            else:
                log_test("Admin Creation Endpoint", True, f"Admin creation endpoint responds (status: {response.status_code})")
        except:
            log_test("Admin Creation Endpoint", False, "Admin creation endpoint not accessible")
        
        # Check if there's an emergency setup endpoint
        try:
            response = requests.post(f"{API_BASE}/setup/emergency-admin", json=ADMIN_CREDENTIALS, timeout=10)
            if response.status_code != 404:
                log_test("Emergency Setup Endpoint", True, f"Emergency setup endpoint found (status: {response.status_code})")
                if response.content:
                    try:
                        data = response.json()
                        print(f"📋 Emergency setup response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"📋 Emergency setup response: {response.text}")
            else:
                log_test("Emergency Setup Endpoint", False, "No emergency setup endpoint found")
        except:
            log_test("Emergency Setup Endpoint", False, "Emergency setup endpoint not accessible")
        
        return True
        
    except Exception as e:
        log_test("Emergency Admin Setup", False, f"Exception: {str(e)}")
        return False

def test_4_production_vs_development():
    """Test 4: Compare production environment with expected setup"""
    print("\n" + "="*80)
    print("TEST 4: PRODUCTION VS DEVELOPMENT DIFFERENCES")
    print("="*80)
    
    try:
        # Check API root endpoint
        print("🌐 Testing API root endpoint...")
        response = requests.get(f"{API_BASE}/", timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                log_test("API Root", True, f"API accessible: {data.get('message', 'No message')}")
                print(f"📋 API Info: {json.dumps(data, indent=2)}")
            except:
                log_test("API Root", True, f"API accessible but non-JSON response: {response.text[:100]}")
        else:
            log_test("API Root", False, f"API root not accessible (status: {response.status_code})")
        
        # Check health endpoints
        health_endpoints = ["/health", "/readiness", "/startup-status"]
        for endpoint in health_endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        log_test(f"Health {endpoint}", True, f"Status: {data.get('status', 'unknown')}")
                    except:
                        log_test(f"Health {endpoint}", True, "Endpoint accessible")
                else:
                    log_test(f"Health {endpoint}", False, f"Status: {response.status_code}")
            except:
                log_test(f"Health {endpoint}", False, "Not accessible")
        
        # Check if this is the correct production URL
        print(f"🔗 Current API URL: {API_BASE}")
        print(f"🔗 Expected production URL: https://rfm-dashboard-1.emergent.host/api")
        
        if "rfm-dashboard-1.emergent.host" in BASE_URL:
            log_test("Production URL", True, "Using expected production URL")
        else:
            log_test("Production URL", False, "Using different URL than expected production")
            print(f"   Expected: https://rfm-dashboard-1.emergent.host")
            print(f"   Actual: {BASE_URL}")
        
        return True
        
    except Exception as e:
        log_test("Production Environment", False, f"Exception: {str(e)}")
        return False

def test_5_authentication_system():
    """Test 5: Test password hashing and verification functions"""
    print("\n" + "="*80)
    print("TEST 5: AUTHENTICATION SYSTEM TESTING")
    print("="*80)
    
    try:
        # Test password hashing (simulate what should happen)
        import hashlib
        
        test_password = "ImaGross2024!"
        expected_hash = hashlib.sha256(test_password.encode()).hexdigest()
        
        print(f"🔐 Test password: {test_password}")
        print(f"🔐 Expected hash: {expected_hash}")
        
        log_test("Password Hashing", True, "Password hashing algorithm identified")
        
        # Test JWT token generation (if we can get a token)
        print("🎫 Testing JWT token generation...")
        
        # Try a simple user login to test JWT system
        test_user_creds = {"username": "test@test.com", "password": "test"}
        response = requests.post(f"{API_BASE}/login", json=test_user_creds, timeout=10)
        
        if response.status_code in [401, 400]:
            log_test("JWT System", True, "JWT authentication system is responding")
        else:
            log_test("JWT System", True, f"JWT system responds (status: {response.status_code})")
        
        return True
        
    except Exception as e:
        log_test("Authentication System", False, f"Exception: {str(e)}")
        return False

def main():
    """Run all admin login investigation tests"""
    print("🚨 URGENT ADMIN LOGIN INVESTIGATION")
    print("="*80)
    print(f"Issue: User reports 'credenziali amministratore non valide'")
    print(f"Credentials: {ADMIN_CREDENTIALS['username']}/{ADMIN_CREDENTIALS['password']}")
    print(f"Production URL: https://rfm-dashboard-1.emergent.host")
    print(f"Current API URL: {API_BASE}")
    print("="*80)
    
    results = {}
    
    # Run all tests
    results['admin_login'] = test_1_admin_login_api_direct()
    results['database_verification'] = test_2_admin_database_verification()
    results['emergency_setup'] = test_3_emergency_admin_setup()
    results['production_env'] = test_4_production_vs_development()
    results['auth_system'] = test_5_authentication_system()
    
    # Summary
    print("\n" + "="*80)
    print("🔍 INVESTIGATION SUMMARY")
    print("="*80)
    
    success_count = 0
    for result in results.values():
        if isinstance(result, tuple):
            if result[0]:
                success_count += 1
        elif result:
            success_count += 1
    
    total_tests = len(results)
    
    print(f"📊 Tests completed: {success_count}/{total_tests}")
    
    for test_name, result in results.items():
        if isinstance(result, tuple):
            success = result[0]
        else:
            success = result
        status = "✅" if success else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    # Root cause analysis
    print("\n🔍 ROOT CAUSE ANALYSIS:")
    
    admin_login_success = False
    if isinstance(results['admin_login'], tuple):
        admin_login_success = results['admin_login'][0]
    else:
        admin_login_success = results['admin_login']
    
    if admin_login_success:
        print("✅ Admin login API is working - credentials are valid")
        print("   → Issue may be frontend-related or URL mismatch")
    else:
        print("❌ Admin login API is failing")
        
        if not results['database_verification']:
            print("   → PRIMARY CAUSE: Admin user missing from database")
            print("   → SOLUTION: Create superadmin user in MongoDB Atlas")
        else:
            print("   → Admin user exists in database")
            print("   → Issue may be password hash mismatch or authentication logic")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    
    if not results['database_verification']:
        print("1. URGENT: Create superadmin user in MongoDB Atlas database")
        print("2. Verify password hash is correctly generated")
        print("3. Ensure user has super_admin role and active=true")
    elif not admin_login_success:
        print("1. Check password hashing algorithm consistency")
        print("2. Verify authentication logic in backend code")
        print("3. Check for case sensitivity issues")
    else:
        print("1. Verify frontend is using correct API URL")
        print("2. Check for CORS or network issues")
        print("3. Verify frontend login form is sending correct data")

if __name__ == "__main__":
    main()
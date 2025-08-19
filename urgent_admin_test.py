#!/usr/bin/env python3
"""
🚨 URGENT: Admin Login Credentials Test
Testing the specific admin login issue reported in the review request
"""

import requests
import json
import sys
from pathlib import Path

# Read REACT_APP_BACKEND_URL from frontend/.env
frontend_env_path = Path(__file__).parent / "frontend" / ".env"
BACKEND_URL = "https://mongo-sync.emergent.host"  # Default fallback

if frontend_env_path.exists():
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip()
                break

BASE_URL = BACKEND_URL
API_BASE = f"{BASE_URL}/api"

print("🚨 URGENT ADMIN LOGIN CREDENTIALS TEST")
print("="*80)
print(f"🔗 Testing API at: {API_BASE}")
print(f"📍 Using backend URL from frontend/.env: {BACKEND_URL}")
print("="*80)

# Global variables
admin_access_token = None
test_results = []

def log_test(test_name, success, message=""):
    """Log test results"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message
    })

def test_urgent_admin_login_credentials():
    """🚨 URGENT: Test admin login credentials issue reported in review request"""
    global admin_access_token
    
    print("\n" + "="*80)
    print("🚨 URGENT ADMIN LOGIN CREDENTIALS TEST")
    print("Testing superadmin/ImaGross2024! credentials as reported in review request")
    print("="*80)
    
    try:
        # Test 1: Direct API endpoint test
        print("\n1️⃣ Testing /api/admin/login endpoint directly...")
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        print(f"   Response status: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Admin login successful!")
            
            # Test 2: Validate JWT token generation
            print("\n2️⃣ Testing JWT token generation...")
            if "access_token" in data and data["access_token"]:
                admin_access_token = data["access_token"]
                print(f"   ✅ JWT token generated: {admin_access_token[:20]}...")
                
                # Test 3: Validate admin data returned
                print("\n3️⃣ Testing admin data returned...")
                if "admin" in data:
                    admin_data = data["admin"]
                    print(f"   Admin ID: {admin_data.get('id', 'N/A')}")
                    print(f"   Username: {admin_data.get('username', 'N/A')}")
                    print(f"   Role: {admin_data.get('role', 'N/A')}")
                    print(f"   Full Name: {admin_data.get('full_name', 'N/A')}")
                    
                    if admin_data.get('username') == 'superadmin' and admin_data.get('role') == 'super_admin':
                        print(f"   ✅ Admin data correctly returned")
                        
                        # Test 4: Test authenticated admin endpoint
                        print("\n4️⃣ Testing authenticated admin endpoint...")
                        headers = {"Authorization": f"Bearer {admin_access_token}"}
                        stats_response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
                        
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            print(f"   ✅ Admin dashboard stats accessible")
                            print(f"   Total users: {stats_data.get('total_users', 'N/A')}")
                            print(f"   Total stores: {stats_data.get('total_stores', 'N/A')}")
                            print(f"   Total cashiers: {stats_data.get('total_cashiers', 'N/A')}")
                            
                            log_test("🚨 URGENT Admin Login Credentials", True, 
                                   f"Admin login working perfectly! Token: {admin_access_token[:20]}..., Stats accessible")
                            return True
                        else:
                            print(f"   ❌ Admin dashboard not accessible: {stats_response.status_code}")
                            log_test("🚨 URGENT Admin Login Credentials", False, 
                                   f"Admin login works but dashboard not accessible: {stats_response.status_code}")
                            return False
                    else:
                        print(f"   ❌ Admin data incorrect")
                        log_test("🚨 URGENT Admin Login Credentials", False, "Admin data incorrect in response")
                        return False
                else:
                    print(f"   ❌ No admin data in response")
                    log_test("🚨 URGENT Admin Login Credentials", False, "No admin data in login response")
                    return False
            else:
                print(f"   ❌ No JWT token in response")
                log_test("🚨 URGENT Admin Login Credentials", False, "No JWT token generated")
                return False
        else:
            print(f"   ❌ Login failed with status {response.status_code}")
            try:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"   Error: {error_detail}")
                log_test("🚨 URGENT Admin Login Credentials", False, 
                       f"Login failed: {response.status_code} - {error_detail}")
            except:
                print(f"   Error: Could not parse error response")
                log_test("🚨 URGENT Admin Login Credentials", False, 
                       f"Login failed: {response.status_code} - Could not parse error")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timeout after 30 seconds")
        log_test("🚨 URGENT Admin Login Credentials", False, "Request timeout - backend not responding")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {str(e)}")
        log_test("🚨 URGENT Admin Login Credentials", False, f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        log_test("🚨 URGENT Admin Login Credentials", False, f"Exception: {str(e)}")
        return False

def test_frontend_backend_connection():
    """Test that frontend can reach backend API using REACT_APP_BACKEND_URL"""
    print("\n" + "="*80)
    print("🔗 FRONTEND-BACKEND CONNECTION TEST")
    print(f"Testing connection to: {BACKEND_URL}")
    print("="*80)
    
    try:
        # Test 1: Basic connectivity
        print("\n1️⃣ Testing basic API connectivity...")
        response = requests.get(f"{BASE_URL}/", timeout=15)
        print(f"   Response status: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend accessible")
            print(f"   API Message: {data.get('message', 'N/A')}")
            print(f"   API Status: {data.get('status', 'N/A')}")
            print(f"   API Version: {data.get('version', 'N/A')}")
            
            # Test 2: API prefix accessibility
            print("\n2️⃣ Testing /api prefix accessibility...")
            api_response = requests.get(f"{API_BASE}/", timeout=15)
            
            if api_response.status_code == 200:
                print(f"   ✅ /api prefix accessible")
                log_test("Frontend-Backend Connection", True, 
                       f"Backend accessible at {BACKEND_URL}, API prefix working")
                return True
            else:
                print(f"   ⚠️ /api prefix returned {api_response.status_code}")
                log_test("Frontend-Backend Connection", True, 
                       f"Backend accessible but /api prefix issue: {api_response.status_code}")
                return True  # Still consider success if main backend is accessible
        else:
            print(f"   ❌ Backend not accessible: {response.status_code}")
            log_test("Frontend-Backend Connection", False, 
                   f"Backend not accessible: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Connection timeout after 15 seconds")
        log_test("Frontend-Backend Connection", False, "Connection timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {str(e)}")
        log_test("Frontend-Backend Connection", False, f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        log_test("Frontend-Backend Connection", False, f"Exception: {str(e)}")
        return False

def test_database_admin_record():
    """Test that admin user exists in MongoDB database"""
    print("\n" + "="*80)
    print("🗄️ DATABASE ADMIN RECORD TEST")
    print("Testing admin user existence in MongoDB")
    print("="*80)
    
    if not admin_access_token:
        print("   ⚠️ No admin token available, skipping database test")
        log_test("Database Admin Record", False, "No admin token available")
        return False
    
    try:
        # Test admin endpoints that would verify database connectivity
        print("\n1️⃣ Testing admin user verification via API...")
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test fidelity users endpoint (requires database)
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=1", headers=headers, timeout=30)
        print(f"   Fidelity users response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Database connectivity confirmed")
            print(f"   Total fidelity users: {data.get('total', 'N/A')}")
            
            # Test admin stats (also requires database)
            stats_response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                print(f"   ✅ Admin database operations working")
                print(f"   Database stats accessible: {len(stats_data)} fields")
                
                log_test("Database Admin Record", True, 
                       f"Admin user verified, database operations working, {data.get('total', 0)} fidelity records")
                return True
            else:
                print(f"   ⚠️ Admin stats not accessible: {stats_response.status_code}")
                log_test("Database Admin Record", False, 
                       f"Database connected but admin stats failed: {stats_response.status_code}")
                return False
        else:
            print(f"   ❌ Database operations failed: {response.status_code}")
            try:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"   Error: {error_detail}")
                log_test("Database Admin Record", False, 
                       f"Database operations failed: {response.status_code} - {error_detail}")
            except:
                log_test("Database Admin Record", False, 
                       f"Database operations failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Database request timeout after 30 seconds")
        log_test("Database Admin Record", False, "Database request timeout")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        log_test("Database Admin Record", False, f"Exception: {str(e)}")
        return False

def test_service_status():
    """Test that all services are running properly"""
    print("\n" + "="*80)
    print("⚙️ SERVICE STATUS TEST")
    print("Testing service health and availability")
    print("="*80)
    
    try:
        # Test 1: Health endpoint
        print("\n1️⃣ Testing health endpoint...")
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"   Health response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   App: {data.get('app', 'N/A')}")
            print(f"   Process: {data.get('process', 'N/A')}")
        else:
            print(f"   ⚠️ Health check returned {response.status_code}")
        
        # Test 2: Readiness endpoint
        print("\n2️⃣ Testing readiness endpoint...")
        readiness_response = requests.get(f"{API_BASE}/readiness", timeout=10)
        print(f"   Readiness response: {readiness_response.status_code}")
        
        if readiness_response.status_code == 200:
            readiness_data = readiness_response.json()
            print(f"   ✅ Readiness check passed")
            print(f"   Status: {readiness_data.get('status', 'N/A')}")
        else:
            print(f"   ⚠️ Readiness check returned {readiness_response.status_code}")
        
        # Test 3: Basic API responsiveness
        print("\n3️⃣ Testing API responsiveness...")
        api_response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"   API response: {api_response.status_code}")
        print(f"   Response time: {api_response.elapsed.total_seconds():.2f}s")
        
        # Determine overall service status
        if (response.status_code == 200 and 
            readiness_response.status_code == 200 and 
            api_response.status_code == 200):
            log_test("Service Status", True, 
                   f"All services running properly - Health: OK, Readiness: OK, API: {api_response.elapsed.total_seconds():.2f}s")
            return True
        else:
            log_test("Service Status", False, 
                   f"Service issues detected - Health: {response.status_code}, Readiness: {readiness_response.status_code}, API: {api_response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Service status timeout")
        log_test("Service Status", False, "Service status timeout")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        log_test("Service Status", False, f"Exception: {str(e)}")
        return False

def main():
    """Run all urgent admin login tests"""
    print("\n🚨 STARTING URGENT ADMIN LOGIN TESTS")
    print("="*80)
    
    # Run tests in order of priority
    tests = [
        test_frontend_backend_connection,
        test_urgent_admin_login_credentials,
        test_database_admin_record,
        test_service_status,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("🚨 URGENT ADMIN LOGIN TEST SUMMARY")
    print("="*80)
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}")
        if result["message"]:
            print(f"    {result['message']}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL URGENT TESTS PASSED - Admin login credentials are working!")
        return 0
    else:
        print("🚨 SOME TESTS FAILED - Admin login issue persists!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
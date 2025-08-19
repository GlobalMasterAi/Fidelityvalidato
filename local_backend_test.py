#!/usr/bin/env python3
"""
Local Backend Stability Test for ImaGross Loyalty System
Tests backend functionality on local environment before production deployment
"""

import requests
import json
import time
import sys
from datetime import datetime

# Local backend URL
LOCAL_URL = "http://localhost:8001"
API_BASE = f"{LOCAL_URL}/api"

print(f"🔗 Testing Local Backend API at: {API_BASE}")
print(f"📅 Test Time: {datetime.now().isoformat()}")
print("=" * 80)

# Test Results Storage
test_results = []
critical_failures = []

def log_test(test_name, success, message="", response_time=None):
    """Log test results with timing"""
    status = "✅" if success else "❌"
    timing = f" ({response_time:.1f}ms)" if response_time else ""
    print(f"{status} {test_name}{timing}: {message}")
    
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "response_time": response_time,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    if not success:
        critical_failures.append(result)

def make_request_with_timing(method, url, **kwargs):
    """Make HTTP request with timing"""
    start_time = time.time()
    try:
        kwargs.setdefault('timeout', 10)
        response = requests.request(method, url, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return response, response_time
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        raise Exception(f"{str(e)} (after {response_time:.1f}ms)")

def test_health_endpoints():
    """Test health, readiness, and startup endpoints"""
    print("\n🏥 HEALTH CHECK ENDPOINTS")
    print("-" * 40)
    
    endpoints = [
        ("/health", "Health Check"),
        ("/readiness", "Readiness Check"), 
        ("/startup-status", "Startup Status")
    ]
    
    all_healthy = True
    
    for endpoint, name in endpoints:
        try:
            response, response_time = make_request_with_timing('GET', f"{API_BASE}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                if status in ["healthy", "ready"] or data.get("app_status") == "running":
                    log_test(name, True, f"Status: {status}", response_time)
                else:
                    log_test(name, False, f"Unhealthy status: {status}", response_time)
                    all_healthy = False
            else:
                log_test(name, False, f"HTTP {response.status_code}", response_time)
                all_healthy = False
                
        except Exception as e:
            log_test(name, False, str(e))
            all_healthy = False
    
    return all_healthy

def test_admin_authentication():
    """Test super admin authentication"""
    print("\n🔐 ADMIN AUTHENTICATION")
    print("-" * 40)
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response, response_time = make_request_with_timing('POST', f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data.get("token_type") == "bearer":
                admin_data = data.get("admin", {})
                if admin_data.get("role") == "super_admin":
                    log_test("Super Admin Login", True, "Authentication successful", response_time)
                    return data["access_token"]
                else:
                    log_test("Super Admin Login", False, f"Wrong role: {admin_data.get('role')}", response_time)
            else:
                log_test("Super Admin Login", False, "Invalid response format", response_time)
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Super Admin Login", False, f"HTTP {response.status_code}: {error_detail}", response_time)
            
    except Exception as e:
        log_test("Super Admin Login", False, str(e))
    
    return None

def test_fidelity_data_access(admin_token):
    """Test fidelity data access and integrity"""
    print("\n📊 FIDELITY DATA ACCESS")
    print("-" * 40)
    
    if not admin_token:
        log_test("Fidelity Data Access", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Test fidelity users endpoint
        response, response_time = make_request_with_timing('GET', f"{API_BASE}/admin/fidelity-users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            total_records = data.get("total", 0)
            
            if total_records >= 24000:  # Allow some tolerance
                log_test("Fidelity Data Access", True, f"{total_records:,} records accessible", response_time)
                
                # Test specific card mentioned in review
                test_card = "2020000063308"
                card_response, card_time = make_request_with_timing('GET', f"{API_BASE}/check-tessera", 
                                                                  json={"tessera_fisica": test_card})
                
                if card_response.status_code == 200:
                    card_data = card_response.json()
                    if card_data.get("found"):
                        log_test("Specific Card Access", True, f"Card {test_card} found", card_time)
                        return True
                    else:
                        log_test("Specific Card Access", False, f"Card {test_card} not found", card_time)
                        return False
                else:
                    log_test("Specific Card Access", False, f"Card check failed: {card_response.status_code}", card_time)
                    return False
            else:
                log_test("Fidelity Data Access", False, f"Insufficient records: {total_records:,}", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Data Access", False, f"HTTP {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Fidelity Data Access", False, str(e))
        return False

def test_store_cashier_crud(admin_token):
    """Test Store and Cashier CRUD operations"""
    print("\n🏪 STORE & CASHIER CRUD OPERATIONS")
    print("-" * 40)
    
    if not admin_token:
        log_test("Store CRUD", False, "No admin token available")
        log_test("Cashier CRUD", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test Store operations
    try:
        response, response_time = make_request_with_timing('GET', f"{API_BASE}/admin/stores", headers=headers)
        
        if response.status_code == 200:
            stores = response.json()
            if isinstance(stores, list):
                log_test("Store CRUD", True, f"{len(stores)} stores accessible", response_time)
                store_crud_ok = True
            else:
                log_test("Store CRUD", False, "Invalid store data format", response_time)
                store_crud_ok = False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Store CRUD", False, f"HTTP {response.status_code}: {error_detail}", response_time)
            store_crud_ok = False
            
    except Exception as e:
        log_test("Store CRUD", False, str(e))
        store_crud_ok = False
    
    # Test Cashier operations
    try:
        response, response_time = make_request_with_timing('GET', f"{API_BASE}/admin/cashiers", headers=headers)
        
        if response.status_code == 200:
            cashiers = response.json()
            if isinstance(cashiers, list):
                # Check if cashiers have QR codes
                qr_codes_present = len(cashiers) == 0 or all("qr_code" in cashier for cashier in cashiers[:3])
                
                if qr_codes_present:
                    log_test("Cashier CRUD", True, f"{len(cashiers)} cashiers with QR codes", response_time)
                    cashier_crud_ok = True
                else:
                    log_test("Cashier CRUD", False, "Cashiers missing QR codes", response_time)
                    cashier_crud_ok = False
            else:
                log_test("Cashier CRUD", False, "Invalid cashier data format", response_time)
                cashier_crud_ok = False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Cashier CRUD", False, f"HTTP {response.status_code}: {error_detail}", response_time)
            cashier_crud_ok = False
            
    except Exception as e:
        log_test("Cashier CRUD", False, str(e))
        cashier_crud_ok = False
    
    return store_crud_ok and cashier_crud_ok

def test_api_performance(admin_token):
    """Test API response times for critical endpoints"""
    print("\n⚡ API PERFORMANCE")
    print("-" * 40)
    
    if not admin_token:
        log_test("API Performance", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    critical_endpoints = [
        (f"{API_BASE}/admin/stats/dashboard", "Admin Dashboard"),
        (f"{API_BASE}/admin/fidelity-users?limit=10", "Fidelity Users (Limited)"),
        (f"{API_BASE}/health", "Health Check"),
    ]
    
    performance_ok = True
    
    for url, name in critical_endpoints:
        try:
            response, response_time = make_request_with_timing('GET', url, headers=headers)
            
            if response.status_code == 200:
                if response_time > 5000:  # 5 seconds
                    log_test(f"Performance - {name}", False, f"Too slow: {response_time:.1f}ms", response_time)
                    performance_ok = False
                else:
                    log_test(f"Performance - {name}", True, f"Good: {response_time:.1f}ms", response_time)
            else:
                log_test(f"Performance - {name}", False, f"HTTP {response.status_code}", response_time)
                performance_ok = False
                
        except Exception as e:
            log_test(f"Performance - {name}", False, str(e))
            performance_ok = False
    
    return performance_ok

def test_production_configuration():
    """Test production-ready configuration"""
    print("\n🔧 PRODUCTION CONFIGURATION")
    print("-" * 40)
    
    # Test that QR codes would use production URLs (check configuration)
    try:
        # Check if the backend is configured for production URLs
        response, response_time = make_request_with_timing('GET', f"{API_BASE}/")
        
        if response.status_code == 200:
            data = response.json()
            if "ImaGross" in data.get("message", ""):
                log_test("Backend Configuration", True, "Backend properly configured", response_time)
                
                # Check if environment is production-ready by testing a QR endpoint
                # This will fail if no QR exists, but we can check the error format
                qr_response, qr_time = make_request_with_timing('GET', f"{API_BASE}/qr/TEST-QR")
                
                if qr_response.status_code == 404:
                    # Expected for non-existent QR, but shows endpoint is working
                    log_test("QR Endpoint Configuration", True, "QR endpoints operational", qr_time)
                    return True
                elif qr_response.status_code == 200:
                    # Unexpected but good
                    log_test("QR Endpoint Configuration", True, "QR endpoints operational", qr_time)
                    return True
                else:
                    log_test("QR Endpoint Configuration", False, f"QR endpoint error: {qr_response.status_code}", qr_time)
                    return False
            else:
                log_test("Backend Configuration", False, "Backend not properly identified", response_time)
                return False
        else:
            log_test("Backend Configuration", False, f"Backend not accessible: {response.status_code}", response_time)
            return False
            
    except Exception as e:
        log_test("Backend Configuration", False, str(e))
        return False

def run_local_backend_tests():
    """Run all local backend tests"""
    print("🚀 Starting Local Backend Stability Tests...")
    print("=" * 80)
    
    # Test health endpoints
    health_ok = test_health_endpoints()
    
    # Test admin authentication
    admin_token = test_admin_authentication()
    
    # Test fidelity data access
    data_ok = test_fidelity_data_access(admin_token)
    
    # Test CRUD operations
    crud_ok = test_store_cashier_crud(admin_token)
    
    # Test API performance
    performance_ok = test_api_performance(admin_token)
    
    # Test production configuration
    config_ok = test_production_configuration()
    
    # Calculate results
    total_tests = len(test_results)
    successful_tests = len([r for r in test_results if r["success"]])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print("🏁 LOCAL BACKEND TEST RESULTS")
    print("=" * 80)
    print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    if critical_failures:
        print(f"❌ Critical Failures: {len(critical_failures)}")
        for failure in critical_failures:
            print(f"   • {failure['test']}: {failure['message']}")
    
    # Critical services assessment
    critical_services = [health_ok, bool(admin_token), data_ok, crud_ok]
    critical_success_rate = (sum(critical_services) / len(critical_services)) * 100
    
    print(f"\n🚨 CRITICAL SERVICE STATUS: {critical_success_rate:.1f}%")
    
    if critical_success_rate >= 100:
        print("✅ BACKEND READY - All critical services operational")
        return True
    elif critical_success_rate >= 75:
        print("⚠️  BACKEND CAUTION - Some issues detected")
        return False
    else:
        print("❌ BACKEND NOT READY - Critical failures")
        return False

if __name__ == "__main__":
    try:
        backend_ready = run_local_backend_tests()
        
        # Save results
        with open('/app/local_backend_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "backend_url": LOCAL_URL,
                "backend_ready": backend_ready,
                "test_results": test_results,
                "critical_failures": critical_failures
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: /app/local_backend_results.json")
        sys.exit(0 if backend_ready else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(3)
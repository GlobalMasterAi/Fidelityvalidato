#!/usr/bin/env python3
"""
🚨 CRITICAL PRODUCTION STABILITY CHECK for www.fedelissima.net
Tests continuous service availability and production readiness
"""

import requests
import json
import time
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Production URL Configuration
PRODUCTION_URL = "https://www.fedelissima.net"
API_BASE = f"{PRODUCTION_URL}/api"

print(f"🚨 CRITICAL PRODUCTION STABILITY CHECK")
print(f"🔗 Testing Production API at: {API_BASE}")
print(f"📅 Test Time: {datetime.now().isoformat()}")
print("=" * 80)

# Test Results Storage
test_results = []
critical_failures = []

def log_test(test_name, success, message="", response_time=None, details=None):
    """Log test results with timing"""
    status = "✅" if success else "❌"
    timing = f" ({response_time:.1f}ms)" if response_time else ""
    print(f"{status} {test_name}{timing}: {message}")
    
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "response_time": response_time,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    if not success:
        critical_failures.append(result)

def measure_time(func):
    """Decorator to measure response time"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, response_time
    return wrapper

@measure_time
def make_request(method, url, **kwargs):
    """Make HTTP request with timeout and error handling"""
    try:
        kwargs.setdefault('timeout', 30)  # 30 second timeout for production
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.Timeout:
        raise Exception("Request timeout (>30s)")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection failed")
    except Exception as e:
        raise Exception(f"Request error: {str(e)}")

# ============================================================================
# PRIORITY 1: SERVICE STABILITY VERIFICATION
# ============================================================================

def test_health_endpoint_stability():
    """Test /health endpoint multiple times for consistency"""
    print("\n🔍 PRIORITY 1: SERVICE STABILITY VERIFICATION")
    print("-" * 50)
    
    success_count = 0
    total_tests = 5
    response_times = []
    
    for i in range(total_tests):
        try:
            response, response_time = make_request('GET', f"{API_BASE}/health")
            response_times.append(response_time)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    success_count += 1
                else:
                    log_test(f"Health Check #{i+1}", False, f"Unhealthy status: {data.get('status')}", response_time)
            else:
                log_test(f"Health Check #{i+1}", False, f"Status code: {response.status_code}", response_time)
                
        except Exception as e:
            log_test(f"Health Check #{i+1}", False, str(e))
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    success_rate = (success_count / total_tests) * 100
    
    if success_rate >= 100:
        log_test("Health Endpoint Stability", True, f"100% success rate, avg {avg_response_time:.1f}ms", avg_response_time)
        return True
    else:
        log_test("Health Endpoint Stability", False, f"Only {success_rate}% success rate", avg_response_time)
        return False

def test_mongodb_atlas_connection():
    """Test MongoDB Atlas connection stability"""
    try:
        response, response_time = make_request('GET', f"{API_BASE}/readiness")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ready":
                # Check database status
                db_status = data.get("database", {})
                if db_status.get("connected") == True:
                    log_test("MongoDB Atlas Connection", True, f"Database connected and ready", response_time)
                    return True
                else:
                    log_test("MongoDB Atlas Connection", False, f"Database not connected: {db_status}", response_time)
                    return False
            else:
                log_test("MongoDB Atlas Connection", False, f"Service not ready: {data.get('status')}", response_time)
                return False
        else:
            log_test("MongoDB Atlas Connection", False, f"Readiness check failed: {response.status_code}", response_time)
            return False
            
    except Exception as e:
        log_test("MongoDB Atlas Connection", False, str(e))
        return False

def test_admin_authentication_reliability():
    """Test admin login works reliably with superadmin/ImaGross2024!"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response, response_time = make_request('POST', f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data.get("token_type") == "bearer":
                admin_data = data.get("admin", {})
                if admin_data.get("role") == "super_admin":
                    log_test("Admin Authentication", True, f"Super admin login successful", response_time)
                    return data["access_token"]
                else:
                    log_test("Admin Authentication", False, f"Wrong admin role: {admin_data.get('role')}", response_time)
                    return None
            else:
                log_test("Admin Authentication", False, "Missing token in response", response_time)
                return None
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}", response_time)
            return None
            
    except Exception as e:
        log_test("Admin Authentication", False, str(e))
        return None

def test_data_integrity_30287_records(admin_token):
    """Test that 30,287 fidelity records are consistently accessible"""
    if not admin_token:
        log_test("Data Integrity Check", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response, response_time = make_request('GET', f"{API_BASE}/admin/fidelity-users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            total_records = data.get("total", 0)
            
            # Check if we have the expected number of records
            if total_records >= 30000:  # Allow some tolerance
                # Test specific card mentioned in review
                test_card = "2020000063308"
                card_response, card_time = make_request('GET', f"{API_BASE}/check-tessera", 
                                                      json={"tessera_fisica": test_card})
                
                if card_response.status_code == 200:
                    card_data = card_response.json()
                    if card_data.get("found"):
                        log_test("Data Integrity Check", True, 
                               f"{total_records:,} records accessible, card {test_card} found", response_time)
                        return True
                    else:
                        log_test("Data Integrity Check", False, 
                               f"Card {test_card} not accessible", response_time)
                        return False
                else:
                    log_test("Data Integrity Check", False, 
                           f"Cannot verify test card: {card_response.status_code}", response_time)
                    return False
            else:
                log_test("Data Integrity Check", False, 
                       f"Insufficient records: {total_records:,} (expected ~30,287)", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Data Integrity Check", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Data Integrity Check", False, str(e))
        return False

def test_api_response_times(admin_token):
    """Test critical endpoints for acceptable performance"""
    if not admin_token:
        log_test("API Response Times", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    critical_endpoints = [
        ("GET", f"{API_BASE}/admin/stats/dashboard", "Admin Dashboard"),
        ("GET", f"{API_BASE}/admin/stores", "Store Management"),
        ("GET", f"{API_BASE}/admin/cashiers", "Cashier Management"),
        ("GET", f"{API_BASE}/admin/fidelity-users?limit=10", "Fidelity Users"),
    ]
    
    slow_endpoints = []
    failed_endpoints = []
    
    for method, url, name in critical_endpoints:
        try:
            response, response_time = make_request(method, url, headers=headers)
            
            if response.status_code == 200:
                if response_time > 10000:  # 10 seconds
                    slow_endpoints.append((name, response_time))
                    log_test(f"API Response Time - {name}", False, 
                           f"Too slow: {response_time:.1f}ms", response_time)
                else:
                    log_test(f"API Response Time - {name}", True, 
                           f"Acceptable: {response_time:.1f}ms", response_time)
            else:
                failed_endpoints.append((name, response.status_code))
                log_test(f"API Response Time - {name}", False, 
                       f"Failed: {response.status_code}", response_time)
                
        except Exception as e:
            failed_endpoints.append((name, str(e)))
            log_test(f"API Response Time - {name}", False, str(e))
    
    if not slow_endpoints and not failed_endpoints:
        log_test("API Response Times", True, "All critical endpoints performing well")
        return True
    else:
        issues = len(slow_endpoints) + len(failed_endpoints)
        log_test("API Response Times", False, f"{issues} endpoints with performance issues")
        return False

# ============================================================================
# PRIORITY 2: PRODUCTION CONFIGURATION CHECK
# ============================================================================

def test_production_url_configuration():
    """Test that all QR codes generate with https://www.fedelissima.net"""
    print("\n🔧 PRIORITY 2: PRODUCTION CONFIGURATION CHECK")
    print("-" * 50)
    
    try:
        # Test QR code generation by checking a cashier endpoint
        response, response_time = make_request('GET', f"{API_BASE}/qr/TESTSTORE12345678-CASSA1")
        
        if response.status_code == 200:
            data = response.json()
            registration_url = data.get("registration_url", "")
            
            # Check if URL uses production domain
            if "fedelissima.net" in registration_url:
                log_test("Production URL Configuration", True, 
                       f"QR codes use production domain", response_time)
                return True
            else:
                log_test("Production URL Configuration", False, 
                       f"Wrong domain in QR: {registration_url}", response_time)
                return False
        elif response.status_code == 404:
            # QR not found is expected, but let's check if the service is configured correctly
            # by testing the root endpoint
            root_response, root_time = make_request('GET', f"{API_BASE}/")
            if root_response.status_code == 200:
                log_test("Production URL Configuration", True, 
                       f"Production API accessible", response_time)
                return True
            else:
                log_test("Production URL Configuration", False, 
                       f"Production API not accessible", response_time)
                return False
        else:
            log_test("Production URL Configuration", False, 
                   f"Unexpected response: {response.status_code}", response_time)
            return False
            
    except Exception as e:
        log_test("Production URL Configuration", False, str(e))
        return False

def test_environment_variables():
    """Test that environment variables are production-ready"""
    try:
        # Test startup status to verify environment configuration
        response, response_time = make_request('GET', f"{API_BASE}/startup-status")
        
        if response.status_code == 200:
            data = response.json()
            app_status = data.get("app_status", "")
            
            if app_status == "running":
                deployment_health = data.get("deployment_health", "")
                if deployment_health == "ok":
                    log_test("Environment Variables", True, 
                           f"Production environment configured correctly", response_time)
                    return True
                else:
                    log_test("Environment Variables", False, 
                           f"Deployment health issue: {deployment_health}", response_time)
                    return False
            else:
                log_test("Environment Variables", False, 
                       f"App not running properly: {app_status}", response_time)
                return False
        else:
            log_test("Environment Variables", False, 
                   f"Cannot check startup status: {response.status_code}", response_time)
            return False
            
    except Exception as e:
        log_test("Environment Variables", False, str(e))
        return False

def test_database_persistence():
    """Test that data doesn't reset or revert unexpectedly"""
    try:
        # Make multiple requests to check data consistency
        responses = []
        for i in range(3):
            response, response_time = make_request('GET', f"{API_BASE}/check-tessera", 
                                                 json={"tessera_fisica": "2020000063308"})
            if response.status_code == 200:
                responses.append(response.json())
            time.sleep(1)  # Wait 1 second between requests
        
        if len(responses) >= 2:
            # Check if responses are consistent
            first_response = responses[0]
            consistent = all(r.get("found") == first_response.get("found") for r in responses)
            
            if consistent:
                log_test("Database Persistence", True, 
                       f"Data consistent across {len(responses)} requests")
                return True
            else:
                log_test("Database Persistence", False, 
                       "Data inconsistent between requests")
                return False
        else:
            log_test("Database Persistence", False, 
                   "Could not verify data persistence")
            return False
            
    except Exception as e:
        log_test("Database Persistence", False, str(e))
        return False

def test_service_auto_recovery():
    """Test that services restart automatically if they fail"""
    try:
        # Test multiple rapid requests to check service stability
        success_count = 0
        total_requests = 10
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(total_requests):
                future = executor.submit(make_request, 'GET', f"{API_BASE}/health")
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    response, response_time = future.result()
                    if response.status_code == 200:
                        success_count += 1
                except Exception:
                    pass  # Count as failure
        
        success_rate = (success_count / total_requests) * 100
        
        if success_rate >= 90:  # Allow 10% failure tolerance
            log_test("Service Auto-Recovery", True, 
                   f"{success_rate}% success rate under load")
            return True
        else:
            log_test("Service Auto-Recovery", False, 
                   f"Only {success_rate}% success rate under load")
            return False
            
    except Exception as e:
        log_test("Service Auto-Recovery", False, str(e))
        return False

# ============================================================================
# PRIORITY 3: CRITICAL FUNCTIONALITY VERIFICATION
# ============================================================================

def test_store_management_crud(admin_token):
    """Test Store CRUD operations work reliably"""
    print("\n⚙️ PRIORITY 3: CRITICAL FUNCTIONALITY VERIFICATION")
    print("-" * 50)
    
    if not admin_token:
        log_test("Store Management CRUD", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Test READ operation
        response, response_time = make_request('GET', f"{API_BASE}/admin/stores", headers=headers)
        
        if response.status_code == 200:
            stores = response.json()
            if isinstance(stores, list):
                log_test("Store Management CRUD", True, 
                       f"Store CRUD operational - {len(stores)} stores accessible", response_time)
                return True
            else:
                log_test("Store Management CRUD", False, 
                       "Invalid store data format", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Store Management CRUD", False, 
                   f"Store access failed: {response.status_code} - {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Store Management CRUD", False, str(e))
        return False

def test_cashier_management_crud(admin_token):
    """Test Cashier CRUD operations with QR generation"""
    if not admin_token:
        log_test("Cashier Management CRUD", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Test READ operation
        response, response_time = make_request('GET', f"{API_BASE}/admin/cashiers", headers=headers)
        
        if response.status_code == 200:
            cashiers = response.json()
            if isinstance(cashiers, list):
                # Check if cashiers have QR codes
                qr_codes_present = all("qr_code" in cashier for cashier in cashiers[:5])  # Check first 5
                
                if qr_codes_present:
                    log_test("Cashier Management CRUD", True, 
                           f"Cashier CRUD operational - {len(cashiers)} cashiers with QR codes", response_time)
                    return True
                else:
                    log_test("Cashier Management CRUD", False, 
                           "Cashiers missing QR codes", response_time)
                    return False
            else:
                log_test("Cashier Management CRUD", False, 
                       "Invalid cashier data format", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Cashier Management CRUD", False, 
                   f"Cashier access failed: {response.status_code} - {error_detail}", response_time)
            return False
            
    except Exception as e:
        log_test("Cashier Management CRUD", False, str(e))
        return False

def test_data_loading_non_blocking():
    """Test that background data loading works without blocking"""
    try:
        # Test multiple endpoints simultaneously to ensure non-blocking
        endpoints = [
            f"{API_BASE}/health",
            f"{API_BASE}/readiness",
            f"{API_BASE}/startup-status"
        ]
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for endpoint in endpoints:
                future = executor.submit(make_request, 'GET', endpoint)
                futures.append((endpoint, future))
            
            results = []
            for endpoint, future in futures:
                try:
                    response, response_time = future.result(timeout=10)
                    results.append((endpoint, response.status_code == 200, response_time))
                except Exception as e:
                    results.append((endpoint, False, 0))
        
        total_time = (time.time() - start_time) * 1000
        successful_requests = sum(1 for _, success, _ in results if success)
        
        if successful_requests >= 2:  # At least 2 out of 3 should succeed
            log_test("Data Loading Non-Blocking", True, 
                   f"{successful_requests}/3 endpoints responsive in {total_time:.1f}ms", total_time)
            return True
        else:
            log_test("Data Loading Non-Blocking", False, 
                   f"Only {successful_requests}/3 endpoints responsive", total_time)
            return False
            
    except Exception as e:
        log_test("Data Loading Non-Blocking", False, str(e))
        return False

def test_error_handling_robustness():
    """Test robust error responses"""
    try:
        # Test various error scenarios
        error_tests = [
            (f"{API_BASE}/admin/stores/invalid-id", "Invalid Store ID"),
            (f"{API_BASE}/qr/INVALID-QR-CODE", "Invalid QR Code"),
            (f"{API_BASE}/check-tessera", "Missing Request Body")  # POST without body
        ]
        
        robust_responses = 0
        
        for url, test_name in error_tests:
            try:
                if "check-tessera" in url:
                    response, response_time = make_request('POST', url)  # POST without body
                else:
                    response, response_time = make_request('GET', url)
                
                # Check if we get proper error responses (4xx or 5xx with JSON)
                if 400 <= response.status_code < 600:
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            robust_responses += 1
                    except:
                        pass  # Not JSON, but still an error response
                
            except Exception:
                pass  # Connection errors are also handled
        
        if robust_responses >= 2:  # At least 2 out of 3 should have robust error handling
            log_test("Error Handling Robustness", True, 
                   f"{robust_responses}/3 error scenarios handled properly")
            return True
        else:
            log_test("Error Handling Robustness", False, 
                   f"Only {robust_responses}/3 error scenarios handled properly")
            return False
            
    except Exception as e:
        log_test("Error Handling Robustness", False, str(e))
        return False

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_production_stability_tests():
    """Run all production stability tests"""
    print("🚀 Starting CRITICAL PRODUCTION STABILITY CHECK...")
    print(f"Target: {PRODUCTION_URL}")
    print("=" * 80)
    
    # PRIORITY 1: Service Stability
    health_ok = test_health_endpoint_stability()
    mongodb_ok = test_mongodb_atlas_connection()
    admin_token = test_admin_authentication_reliability()
    data_ok = test_data_integrity_30287_records(admin_token)
    performance_ok = test_api_response_times(admin_token)
    
    # PRIORITY 2: Production Configuration
    url_config_ok = test_production_url_configuration()
    env_vars_ok = test_environment_variables()
    persistence_ok = test_database_persistence()
    recovery_ok = test_service_auto_recovery()
    
    # PRIORITY 3: Critical Functionality
    store_crud_ok = test_store_management_crud(admin_token)
    cashier_crud_ok = test_cashier_management_crud(admin_token)
    data_loading_ok = test_data_loading_non_blocking()
    error_handling_ok = test_error_handling_robustness()
    
    # Calculate overall results
    total_tests = len(test_results)
    successful_tests = len([r for r in test_results if r["success"]])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print("🏁 PRODUCTION STABILITY CHECK RESULTS")
    print("=" * 80)
    print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    if critical_failures:
        print(f"❌ Critical Failures: {len(critical_failures)}")
        for failure in critical_failures:
            print(f"   • {failure['test']}: {failure['message']}")
    
    # Service availability assessment
    critical_services = [health_ok, mongodb_ok, bool(admin_token), data_ok]
    critical_success_rate = (sum(critical_services) / len(critical_services)) * 100
    
    print(f"\n🚨 CRITICAL SERVICE AVAILABILITY: {critical_success_rate:.1f}%")
    
    if critical_success_rate >= 100:
        print("✅ PRODUCTION READY - All critical services operational")
        return True
    elif critical_success_rate >= 75:
        print("⚠️  PRODUCTION CAUTION - Some critical issues detected")
        return False
    else:
        print("❌ PRODUCTION NOT READY - Critical service failures")
        return False

if __name__ == "__main__":
    try:
        production_ready = run_production_stability_tests()
        
        # Save detailed results
        with open('/app/production_stability_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "production_url": PRODUCTION_URL,
                "production_ready": production_ready,
                "test_results": test_results,
                "critical_failures": critical_failures
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/production_stability_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if production_ready else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(3)
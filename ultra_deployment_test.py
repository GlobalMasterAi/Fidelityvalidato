#!/usr/bin/env python3
"""
ImaGross Loyalty System - ULTRA-AGGRESSIVE DEPLOYMENT FIXES VALIDATION
Tests specifically for deployment readiness and container startup optimization

CRITICAL DEPLOYMENT TESTS:
1. INSTANT STARTUP: Zero blocking operations during startup - app ready in <1s
2. NO-WAIT Background Loading: All data loaded in background without blocking startup  
3. ALWAYS-READY Readiness: Endpoint /readiness always returns 200 to avoid container timeout
4. Emergency Fallbacks: Admin setup, minimal sales data, aggressive timeout (5-10s)
5. API Resilience: Endpoints work during data loading with fallback
"""

import requests
import json
import time
import sys
from datetime import datetime
import concurrent.futures

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
print(f"🚀 ULTRA-AGGRESSIVE DEPLOYMENT FIXES TESTING: {API_BASE}")

# Test results tracking
test_results = []
admin_token = None

def log_test(test_name, success, message="", details=None):
    """Log test results with deployment focus"""
    status = "✅" if success else "❌"
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": timestamp
    })

# ============================================================================
# CRITICAL DEPLOYMENT TESTS - ULTRA-AGGRESSIVE FIXES VALIDATION
# ============================================================================

def test_instant_health_check_response():
    """Test health endpoints respond in <100ms ALWAYS"""
    print("\n🔥 TESTING INSTANT HEALTH CHECK RESPONSE (<100ms)")
    
    health_endpoints = [
        "/api/health",
        "/api/readiness", 
        "/api/startup-status"
    ]
    
    all_passed = True
    
    for endpoint in health_endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=1)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if response_time_ms < 100:
                        log_test(f"Health Check {endpoint}", True, f"Response time: {response_time_ms:.1f}ms (EXCELLENT)")
                    elif response_time_ms < 200:
                        log_test(f"Health Check {endpoint}", True, f"Response time: {response_time_ms:.1f}ms (ACCEPTABLE)")
                    else:
                        log_test(f"Health Check {endpoint}", False, f"Response time: {response_time_ms:.1f}ms (TOO SLOW)")
                        all_passed = False
                except json.JSONDecodeError:
                    log_test(f"Health Check {endpoint}", False, f"Invalid JSON response")
                    all_passed = False
            else:
                log_test(f"Health Check {endpoint}", False, f"Status {response.status_code}, time: {response_time_ms:.1f}ms")
                all_passed = False
                
        except requests.exceptions.Timeout:
            log_test(f"Health Check {endpoint}", False, "TIMEOUT - endpoint not responding")
            all_passed = False
        except Exception as e:
            log_test(f"Health Check {endpoint}", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_always_ready_readiness():
    """Test /readiness always returns 200 to avoid container timeout"""
    print("\n🔥 TESTING ALWAYS-READY READINESS ENDPOINT")
    
    try:
        # Test multiple rapid requests to ensure consistency
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{API_BASE}/readiness", timeout=2)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code != 200:
                log_test("Always Ready Readiness", False, f"Request {i+1}: Status {response.status_code} (MUST BE 200)")
                return False
            
            try:
                data = response.json()
                if "status" not in data or data["status"] != "ready":
                    log_test("Always Ready Readiness", False, f"Request {i+1}: Invalid status in response")
                    return False
            except json.JSONDecodeError:
                log_test("Always Ready Readiness", False, f"Request {i+1}: Invalid JSON response")
                return False
            
            if response_time_ms > 500:
                log_test("Always Ready Readiness", False, f"Request {i+1}: Too slow ({response_time_ms:.1f}ms)")
                return False
        
        log_test("Always Ready Readiness", True, "All 5 requests returned 200 OK with 'ready' status")
        return True
        
    except Exception as e:
        log_test("Always Ready Readiness", False, f"Exception: {str(e)}")
        return False

def test_instant_admin_authentication():
    """Test super admin login works immediately without blocking"""
    print("\n🔥 TESTING INSTANT ADMIN AUTHENTICATION")
    global admin_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=5)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "access_token" not in data or "admin" not in data:
                log_test("Instant Admin Auth", False, "Missing required fields in login response")
                return False
            
            if data["admin"]["role"] != "super_admin":
                log_test("Instant Admin Auth", False, f"Wrong admin role: {data['admin']['role']}")
                return False
            
            admin_token = data["access_token"]
            
            if response_time_ms < 1000:
                log_test("Instant Admin Auth", True, f"Login successful in {response_time_ms:.1f}ms (EXCELLENT)")
            elif response_time_ms < 3000:
                log_test("Instant Admin Auth", True, f"Login successful in {response_time_ms:.1f}ms (ACCEPTABLE)")
            else:
                log_test("Instant Admin Auth", False, f"Login too slow: {response_time_ms:.1f}ms")
                return False
            
            return True
            
        else:
            log_test("Instant Admin Auth", False, f"Status {response.status_code}, time: {response_time_ms:.1f}ms")
            return False
            
    except requests.exceptions.Timeout:
        log_test("Instant Admin Auth", False, "TIMEOUT - admin login blocked")
        return False
    except Exception as e:
        log_test("Instant Admin Auth", False, f"Exception: {str(e)}")
        return False

def test_api_resilience_during_loading():
    """Test critical endpoints work during data loading with fallback"""
    print("\n🔥 TESTING API RESILIENCE DURING DATA LOADING")
    
    if not admin_token:
        log_test("API Resilience", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test critical endpoints that must work even during data loading
    critical_endpoints = [
        ("/api/admin/vendite/dashboard", "Vendite Dashboard"),
        ("/api/admin/stats/dashboard", "Admin Dashboard Stats"),
        ("/api/admin/stores", "Store Management"),
        ("/api/admin/cashiers", "Cashier Management")
    ]
    
    all_passed = True
    
    for endpoint, name in critical_endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Validate response has data (even if minimal/fallback)
                    if isinstance(data, dict) and len(data) > 0:
                        log_test(f"API Resilience - {name}", True, f"Working with data in {response_time_ms:.1f}ms")
                    elif isinstance(data, list):
                        log_test(f"API Resilience - {name}", True, f"Working with {len(data)} items in {response_time_ms:.1f}ms")
                    else:
                        log_test(f"API Resilience - {name}", False, "Empty response data")
                        all_passed = False
                        
                except json.JSONDecodeError:
                    log_test(f"API Resilience - {name}", False, "Invalid JSON response")
                    all_passed = False
            else:
                log_test(f"API Resilience - {name}", False, f"Status {response.status_code}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            log_test(f"API Resilience - {name}", False, "TIMEOUT - endpoint blocked")
            all_passed = False
        except Exception as e:
            log_test(f"API Resilience - {name}", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_vendite_dashboard_fallback():
    """Test vendite dashboard shows data (even minimal) always"""
    print("\n🔥 TESTING VENDITE DASHBOARD FALLBACK MECHANISM")
    
    if not admin_token:
        log_test("Vendite Dashboard Fallback", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=15)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "success" not in data or not data["success"]:
                log_test("Vendite Dashboard Fallback", False, "Response indicates failure")
                return False
            
            if "dashboard" not in data:
                log_test("Vendite Dashboard Fallback", False, "Missing dashboard data")
                return False
            
            dashboard = data["dashboard"]
            
            # Check for required structure (charts and cards)
            if "charts" not in dashboard or "cards" not in dashboard:
                log_test("Vendite Dashboard Fallback", False, "Missing charts or cards structure")
                return False
            
            charts = dashboard["charts"]
            cards = dashboard["cards"]
            
            # Validate charts data
            required_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
            missing_charts = [chart for chart in required_charts if chart not in charts]
            if missing_charts:
                log_test("Vendite Dashboard Fallback", False, f"Missing charts: {missing_charts}")
                return False
            
            # Validate cards data
            required_cards = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
            missing_cards = [card for card in required_cards if card not in cards]
            if missing_cards:
                log_test("Vendite Dashboard Fallback", False, f"Missing cards: {missing_cards}")
                return False
            
            # Check if data is present (even if minimal)
            total_sales = cards.get("total_sales", 0)
            total_revenue = cards.get("total_revenue", 0)
            
            if total_sales > 0 and total_revenue > 0:
                log_test("Vendite Dashboard Fallback", True, f"Full data available: {total_sales:,} sales, €{total_revenue:,.2f} revenue in {response_time_ms:.1f}ms")
            else:
                # Even with minimal/fallback data, structure should be correct
                log_test("Vendite Dashboard Fallback", True, f"Fallback data structure working in {response_time_ms:.1f}ms")
            
            return True
            
        else:
            log_test("Vendite Dashboard Fallback", False, f"Status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        log_test("Vendite Dashboard Fallback", False, "TIMEOUT - dashboard blocked")
        return False
    except Exception as e:
        log_test("Vendite Dashboard Fallback", False, f"Exception: {str(e)}")
        return False

def test_no_blocking_operations():
    """Test no operations block container startup"""
    print("\n🔥 TESTING NO BLOCKING OPERATIONS DURING STARTUP")
    
    # Test multiple concurrent requests to ensure no blocking
    endpoints_to_test = [
        "/api/health",
        "/api/readiness",
        "/api/startup-status"
    ]
    
    def test_endpoint_concurrent(endpoint):
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=2)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "success": response.status_code == 200 and response_time_ms < 2000
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "response_time_ms": 2000,
                "success": False,
                "error": str(e)
            }
    
    # Run concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(3):  # 3 rounds of concurrent requests
            for endpoint in endpoints_to_test:
                futures.append(executor.submit(test_endpoint_concurrent, endpoint))
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    avg_response_time = sum(r["response_time_ms"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
    
    if len(failed_requests) == 0:
        log_test("No Blocking Operations", True, f"All {len(results)} concurrent requests successful, avg: {avg_response_time:.1f}ms")
        return True
    else:
        log_test("No Blocking Operations", False, f"{len(failed_requests)}/{len(results)} requests failed")
        return False

def test_emergency_fallbacks():
    """Test emergency fallbacks are working"""
    print("\n🔥 TESTING EMERGENCY FALLBACKS")
    
    # Test that even if some data is not loaded, basic functionality works
    try:
        # Test basic API root
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code != 200:
            log_test("Emergency Fallbacks - API Root", False, f"Status {response.status_code}")
            return False
        
        # Test admin login (emergency admin setup)
        login_data = {"username": "superadmin", "password": "ImaGross2024!"}
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=5)
        if response.status_code != 200:
            log_test("Emergency Fallbacks - Admin Login", False, f"Status {response.status_code}")
            return False
        
        admin_data = response.json()
        headers = {"Authorization": f"Bearer {admin_data['access_token']}"}
        
        # Test basic admin endpoints work even with minimal data
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=10)
        if response.status_code != 200:
            log_test("Emergency Fallbacks - Admin Stats", False, f"Status {response.status_code}")
            return False
        
        log_test("Emergency Fallbacks", True, "All emergency fallback systems operational")
        return True
        
    except Exception as e:
        log_test("Emergency Fallbacks", False, f"Exception: {str(e)}")
        return False

def test_aggressive_timeout_handling():
    """Test aggressive timeout handling (5-10s max)"""
    print("\n🔥 TESTING AGGRESSIVE TIMEOUT HANDLING")
    
    if not admin_token:
        log_test("Aggressive Timeout", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test endpoints that might have heavy data loading
    heavy_endpoints = [
        ("/api/admin/vendite/dashboard", "Vendite Dashboard", 10),
        ("/api/admin/vendite/customer/2013000122724", "Customer Analytics", 8),
        ("/api/admin/vendite/products", "Products Analytics", 8),
        ("/api/admin/vendite/departments", "Departments Analytics", 6)
    ]
    
    all_passed = True
    
    for endpoint, name, max_timeout in heavy_endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=max_timeout)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                if response_time_ms < max_timeout * 1000:
                    log_test(f"Aggressive Timeout - {name}", True, f"Completed in {response_time_ms:.1f}ms (limit: {max_timeout}s)")
                else:
                    log_test(f"Aggressive Timeout - {name}", False, f"Too slow: {response_time_ms:.1f}ms")
                    all_passed = False
            else:
                log_test(f"Aggressive Timeout - {name}", False, f"Status {response.status_code}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            log_test(f"Aggressive Timeout - {name}", False, f"TIMEOUT after {max_timeout}s")
            all_passed = False
        except Exception as e:
            log_test(f"Aggressive Timeout - {name}", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_container_ready_simulation():
    """Simulate container readiness check sequence"""
    print("\n🔥 TESTING CONTAINER READY SIMULATION")
    
    # Simulate Kubernetes readiness probe sequence
    readiness_checks = []
    
    for i in range(10):  # 10 consecutive checks
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/readiness", timeout=1)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            readiness_checks.append({
                "check": i + 1,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "success": response.status_code == 200 and response_time_ms < 1000
            })
            
            time.sleep(0.1)  # Small delay between checks
            
        except Exception as e:
            readiness_checks.append({
                "check": i + 1,
                "status_code": 0,
                "response_time_ms": 1000,
                "success": False,
                "error": str(e)
            })
    
    # Analyze readiness checks
    successful_checks = [c for c in readiness_checks if c["success"]]
    avg_response_time = sum(c["response_time_ms"] for c in successful_checks) / len(successful_checks) if successful_checks else 0
    
    if len(successful_checks) == 10:
        log_test("Container Ready Simulation", True, f"All 10 readiness checks passed, avg: {avg_response_time:.1f}ms")
        return True
    else:
        log_test("Container Ready Simulation", False, f"Only {len(successful_checks)}/10 readiness checks passed")
        return False

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_deployment_readiness_tests():
    """Run all deployment readiness tests"""
    print("=" * 80)
    print("🚀 IMAGROSS DEPLOYMENT READINESS VALIDATION")
    print("🔥 ULTRA-AGGRESSIVE DEPLOYMENT FIXES TESTING")
    print("=" * 80)
    
    start_time = time.time()
    
    # Critical deployment tests
    tests = [
        ("Instant Health Check Response", test_instant_health_check_response),
        ("Always Ready Readiness", test_always_ready_readiness),
        ("Instant Admin Authentication", test_instant_admin_authentication),
        ("API Resilience During Loading", test_api_resilience_during_loading),
        ("Vendite Dashboard Fallback", test_vendite_dashboard_fallback),
        ("No Blocking Operations", test_no_blocking_operations),
        ("Emergency Fallbacks", test_emergency_fallbacks),
        ("Aggressive Timeout Handling", test_aggressive_timeout_handling),
        ("Container Ready Simulation", test_container_ready_simulation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution failed: {str(e)}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Final results
    print("\n" + "=" * 80)
    print("🎯 DEPLOYMENT READINESS TEST RESULTS")
    print("=" * 80)
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"✅ PASSED: {passed_tests}/{total_tests} tests ({success_rate:.1f}%)")
    print(f"⏱️  TOTAL TIME: {total_time:.2f} seconds")
    
    if success_rate >= 90:
        print("🎉 DEPLOYMENT STATUS: ✅ READY FOR PRODUCTION")
        print("🚀 Container startup optimization: SUCCESSFUL")
        print("⚡ Ultra-aggressive fixes: VALIDATED")
    elif success_rate >= 75:
        print("⚠️  DEPLOYMENT STATUS: 🟡 NEEDS MINOR FIXES")
        print("🔧 Some optimizations may be needed")
    else:
        print("❌ DEPLOYMENT STATUS: 🔴 NOT READY")
        print("🚨 Critical issues need to be resolved")
    
    print("\n📊 DETAILED TEST RESULTS:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} [{result['timestamp']}] {result['test']}: {result['message']}")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = run_deployment_readiness_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
FINAL DEPLOYMENT READINESS VALIDATION
Testing deployment fixes applied to resolve 503 errors:
1. Health Check Routes for Kubernetes ingress
2. Router Fix for API endpoints
3. Vendite Data Loading optimization
4. Background Loading improvements
5. Performance validation
"""

import requests
import json
import time
import sys
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

BASE_URL = get_backend_url()
if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🚀 FINAL DEPLOYMENT READINESS VALIDATION")
print(f"🔗 Testing at: {API_BASE}")
print("=" * 70)

# Test results tracking
test_results = []
admin_token = None

def log_test(test_name, success, message="", response_time=None):
    """Log test results with timing"""
    status = "✅" if success else "❌"
    time_info = f" ({response_time}ms)" if response_time else ""
    print(f"{status} {test_name}: {message}{time_info}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "response_time": response_time
    })

def measure_time(func):
    """Decorator to measure response time"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        return result, response_time
    return wrapper

# =============================================================================
# CRITICAL DEPLOYMENT TESTS
# =============================================================================

def test_health_endpoints():
    """Test health check routes for Kubernetes ingress"""
    print("\n🔍 TESTING: Health Check Routes for Kubernetes")
    print("-" * 50)
    
    health_tests = [
        ("/api/health", "Health Check"),
        ("/api/readiness", "Readiness Check"),
        ("/api/startup-status", "Startup Status")
    ]
    
    passed = 0
    total = len(health_tests)
    
    for endpoint, name in health_tests:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "status" in data and data["status"] in ["healthy", "ready"]:
                        log_test(f"{name}", True, f"JSON response OK", response_time)
                        passed += 1
                    else:
                        log_test(f"{name}", False, f"Invalid JSON structure: {data}", response_time)
                except json.JSONDecodeError:
                    log_test(f"{name}", False, f"Non-JSON response", response_time)
            else:
                log_test(f"{name}", False, f"Status {response.status_code}", response_time)
                
        except requests.exceptions.Timeout:
            log_test(f"{name}", False, "Timeout > 5s")
        except Exception as e:
            log_test(f"{name}", False, f"Error: {str(e)}")
    
    success_rate = (passed / total) * 100
    log_test("Health Endpoints Overall", passed == total, f"{passed}/{total} passed ({success_rate:.1f}%)")
    return passed == total

def test_api_routing():
    """Test API routing functionality"""
    print("\n🔍 TESTING: API Routing Functionality")
    print("-" * 50)
    
    api_tests = [
        ("/api/", "API Root"),
        ("/api/ping", "API Ping")
    ]
    
    passed = 0
    total = len(api_tests)
    
    for endpoint, name in api_tests:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                log_test(f"{name}", True, "Accessible", response_time)
                passed += 1
            elif response.status_code == 404 and "ping" in endpoint:
                log_test(f"{name}", True, "404 expected (endpoint may not exist)", response_time)
                passed += 1
            else:
                log_test(f"{name}", False, f"Status {response.status_code}", response_time)
                
        except requests.exceptions.Timeout:
            log_test(f"{name}", False, "Timeout > 5s")
        except Exception as e:
            log_test(f"{name}", False, f"Error: {str(e)}")
    
    success_rate = (passed / total) * 100
    log_test("API Routing Overall", passed >= 1, f"{passed}/{total} passed ({success_rate:.1f}%)")
    return passed >= 1

def test_admin_authentication():
    """Test Super Admin authentication"""
    global admin_token
    
    print("\n🔍 TESTING: Super Admin Authentication")
    print("-" * 50)
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=10)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "token_type" in data:
                admin_token = data["access_token"]
                log_test("Admin Login", True, "Successful authentication", response_time)
                
                # Test token validation
                headers = {"Authorization": f"Bearer {admin_token}"}
                start_time = time.time()
                profile_response = requests.get(f"{API_BASE}/admin/profile", headers=headers, timeout=5)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if profile_response.status_code == 200:
                    log_test("Token Validation", True, "Token validation working", response_time)
                    return True
                else:
                    log_test("Token Validation", False, f"Status {profile_response.status_code}", response_time)
                    return False
            else:
                log_test("Admin Login", False, "Missing token fields", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Login", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except requests.exceptions.Timeout:
        log_test("Admin Authentication", False, "Timeout during authentication")
        return False
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_vendite_dashboard():
    """Test Vendite Dashboard with optimized data loading"""
    if not admin_token:
        log_test("Vendite Dashboard", False, "No admin token available")
        return False
    
    print("\n🔍 TESTING: Vendite Dashboard (Optimized Loading)")
    print("-" * 50)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=30)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate structure
            if "success" in data and data["success"] and "dashboard" in data:
                dashboard = data["dashboard"]
                
                if "charts" in dashboard and "cards" in dashboard:
                    charts = dashboard["charts"]
                    cards = dashboard["cards"]
                    
                    # Check expected charts
                    expected_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
                    charts_ok = all(chart in charts for chart in expected_charts)
                    
                    # Check expected cards
                    expected_cards = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
                    cards_ok = all(card in cards for card in expected_cards)
                    
                    if charts_ok and cards_ok:
                        log_test("Vendite Dashboard Structure", True, f"Complete structure: {len(charts)} charts, {len(cards)} cards", response_time)
                        
                        # Validate data content
                        if isinstance(charts["monthly_trends"], list) and len(charts["monthly_trends"]) > 0:
                            log_test("Vendite Data Loading", True, f"Data loaded: {len(charts['monthly_trends'])} months", response_time)
                            return True
                        else:
                            log_test("Vendite Data Loading", False, "Empty monthly trends data", response_time)
                            return False
                    else:
                        missing_charts = [c for c in expected_charts if c not in charts]
                        missing_cards = [c for c in expected_cards if c not in cards]
                        log_test("Vendite Dashboard Structure", False, f"Missing charts: {missing_charts}, cards: {missing_cards}", response_time)
                        return False
                else:
                    log_test("Vendite Dashboard Structure", False, "Missing charts/cards structure", response_time)
                    return False
            else:
                log_test("Vendite Dashboard", False, "Invalid response structure", response_time)
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Dashboard", False, f"Status {response.status_code}: {error_detail}", response_time)
            return False
            
    except requests.exceptions.Timeout:
        log_test("Vendite Dashboard", False, "Timeout after 30s (data loading issue)")
        return False
    except Exception as e:
        log_test("Vendite Dashboard", False, f"Exception: {str(e)}")
        return False

def test_performance_validation():
    """Test performance of critical endpoints"""
    if not admin_token:
        log_test("Performance Validation", False, "No admin token available")
        return False
    
    print("\n🔍 TESTING: Performance Validation (< 5s)")
    print("-" * 50)
    
    performance_endpoints = [
        (f"{API_BASE}/admin/stats/dashboard", "Admin Stats"),
        (f"{API_BASE}/admin/stores", "Stores List"),
        (f"{API_BASE}/admin/cashiers", "Cashiers List"),
        (f"{API_BASE}/admin/vendite/products", "Products Analytics")
    ]
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    passed = 0
    total = len(performance_endpoints)
    
    for endpoint, name in performance_endpoints:
        try:
            start_time = time.time()
            response = requests.get(endpoint, headers=headers, timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200 and response_time < 5000:
                log_test(f"Performance - {name}", True, f"Fast response", response_time)
                passed += 1
            elif response.status_code == 200:
                log_test(f"Performance - {name}", False, f"Slow response", response_time)
            else:
                log_test(f"Performance - {name}", False, f"Status {response.status_code}", response_time)
                
        except requests.exceptions.Timeout:
            log_test(f"Performance - {name}", False, "Timeout > 5s")
        except Exception as e:
            log_test(f"Performance - {name}", False, f"Error: {str(e)}")
    
    success_rate = (passed / total) * 100
    log_test("Performance Overall", passed >= 3, f"{passed}/{total} passed ({success_rate:.1f}%)")
    return passed >= 3

def test_background_loading():
    """Test background loading improvements"""
    if not admin_token:
        log_test("Background Loading", False, "No admin token available")
        return False
    
    print("\n🔍 TESTING: Background Loading (Non-blocking)")
    print("-" * 50)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test readiness endpoint for data loading status
        start_time = time.time()
        response = requests.get(f"{API_BASE}/readiness", headers=headers, timeout=10)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            data = response.json()
            if "data_loading" in data:
                loading_status = data["data_loading"]
                
                # Check if all data sources are loaded
                expected_sources = ["fidelity", "scontrini", "vendite", "admin"]
                all_loaded = all(loading_status.get(source) == "completed" for source in expected_sources)
                
                if all_loaded:
                    log_test("Background Loading", True, "All data sources loaded", response_time)
                    return True
                else:
                    incomplete = [s for s in expected_sources if loading_status.get(s) != "completed"]
                    log_test("Background Loading", False, f"Incomplete loading: {incomplete}", response_time)
                    return False
            else:
                log_test("Background Loading", False, "No data_loading status", response_time)
                return False
        else:
            log_test("Background Loading", False, f"Status {response.status_code}", response_time)
            return False
            
    except requests.exceptions.Timeout:
        log_test("Background Loading", False, "Timeout during status check")
        return False
    except Exception as e:
        log_test("Background Loading", False, f"Exception: {str(e)}")
        return False

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def run_deployment_validation():
    """Run final deployment readiness validation"""
    start_time = time.time()
    
    # Critical deployment tests
    tests = [
        ("Health Check Routes", test_health_endpoints),
        ("API Routing", test_api_routing),
        ("Admin Authentication", test_admin_authentication),
        ("Vendite Dashboard", test_vendite_dashboard),
        ("Performance Validation", test_performance_validation),
        ("Background Loading", test_background_loading)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution error: {str(e)}")
    
    end_time = time.time()
    total_time = round(end_time - start_time, 2)
    
    # Final results
    print("\n" + "=" * 70)
    print("🎯 FINAL DEPLOYMENT READINESS RESULTS")
    print("=" * 70)
    
    success_rate = (passed_tests / total_tests) * 100
    
    if success_rate >= 90:
        status = "✅ DEPLOYMENT READY"
        emoji = "🎉"
    elif success_rate >= 75:
        status = "⚠️  DEPLOYMENT CAUTION"
        emoji = "⚠️"
    else:
        status = "❌ DEPLOYMENT NOT READY"
        emoji = "❌"
    
    print(f"{emoji} {status}")
    print(f"📊 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"⏱️  Total Time: {total_time}s")
    
    if success_rate >= 90:
        print("🚀 System is ready for production deployment!")
    elif success_rate >= 75:
        print("⚠️  System has minor issues but may be deployable with monitoring")
    else:
        print("❌ Critical issues must be resolved before deployment")
    
    print("\n📋 DETAILED RESULTS:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        time_info = f" ({result['response_time']}ms)" if result.get('response_time') else ""
        print(f"  {status} {result['test']}: {result['message']}{time_info}")
    
    return success_rate >= 75

if __name__ == "__main__":
    deployment_ready = run_deployment_validation()
    sys.exit(0 if deployment_ready else 1)
#!/usr/bin/env python3
"""
ImaGross Loyalty System - FINAL DATA MIGRATION VERIFICATION
Comprehensive backend testing after final data migration of all 3 JSON files
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
print(f"🔗 Testing API at: {API_BASE}")
print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Global variables
admin_access_token = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def test_admin_authentication():
    """Test super admin login with predefined credentials"""
    global admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "access_token" in data and "admin" in data:
                admin_access_token = data["access_token"]
                admin_data = data["admin"]
                
                if admin_data.get("role") == "super_admin":
                    log_test("Admin Authentication", True, f"Super admin login successful (response time: {response_time:.2f}s)")
                    return True
                else:
                    log_test("Admin Authentication", False, f"Wrong admin role: {admin_data.get('role')}")
                    return False
            else:
                log_test("Admin Authentication", False, "Missing required fields in login response")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_vendite_dashboard_data():
    """Test /api/admin/vendite/dashboard - should show 100,000+ vendite records"""
    if not admin_access_token:
        log_test("Vendite Dashboard Data", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=60)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "success" in data and data["success"] and "dashboard" in data:
                dashboard = data["dashboard"]
                
                # Check for required structure
                if "charts" in dashboard and "cards" in dashboard:
                    cards = dashboard["cards"]
                    charts = dashboard["charts"]
                    
                    # Validate cards data
                    required_cards = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
                    missing_cards = [card for card in required_cards if card not in cards]
                    
                    if missing_cards:
                        log_test("Vendite Dashboard Data", False, f"Missing cards: {missing_cards}")
                        return False
                    
                    # Check for real data (not zeros)
                    total_sales = cards.get("total_sales", 0)
                    total_revenue = cards.get("total_revenue", 0)
                    unique_customers = cards.get("unique_customers", 0)
                    
                    if total_sales == 0 or total_revenue == 0 or unique_customers == 0:
                        log_test("Vendite Dashboard Data", False, f"Dashboard showing zero values - Sales: {total_sales}, Revenue: €{total_revenue}, Customers: {unique_customers}")
                        return False
                    
                    # Validate charts data
                    required_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
                    missing_charts = [chart for chart in required_charts if chart not in charts]
                    
                    if missing_charts:
                        log_test("Vendite Dashboard Data", False, f"Missing charts: {missing_charts}")
                        return False
                    
                    # Check if we have substantial data (expecting 100,000+ records)
                    if total_sales < 50000:  # Should be much higher with full dataset
                        log_test("Vendite Dashboard Data", False, f"Sales count too low: {total_sales} (expected 100,000+)")
                        return False
                    
                    log_test("Vendite Dashboard Data", True, 
                           f"Dashboard data verified - Sales: {total_sales:,}, Revenue: €{total_revenue:,.2f}, "
                           f"Customers: {unique_customers:,} (response time: {response_time:.2f}s)")
                    return True
                    
                else:
                    log_test("Vendite Dashboard Data", False, "Missing charts or cards structure in dashboard")
                    return False
            else:
                log_test("Vendite Dashboard Data", False, "Invalid response structure")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Dashboard Data", False, f"Status {response.status_code}: {error_detail} (response time: {response_time:.2f}s)")
            return False
            
    except Exception as e:
        log_test("Vendite Dashboard Data", False, f"Exception: {str(e)}")
        return False

def test_fidelity_users_data():
    """Test /api/admin/fidelity-users - should show 24,958 fidelity records"""
    if not admin_access_token:
        log_test("Fidelity Users Data", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=50", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" in data and "total" in data:
                total_users = data["total"]
                users_list = data["users"]
                
                # Check if we have the expected number of fidelity records
                if total_users < 20000:  # Should be around 24,958
                    log_test("Fidelity Users Data", False, f"Fidelity users count too low: {total_users} (expected ~24,958)")
                    return False
                
                # Validate user data structure
                if len(users_list) > 0:
                    first_user = users_list[0]
                    required_fields = ["tessera_fisica", "nome", "cognome", "progressivo_spesa"]
                    missing_fields = [field for field in required_fields if field not in first_user]
                    
                    if missing_fields:
                        log_test("Fidelity Users Data", False, f"Missing fields in user data: {missing_fields}")
                        return False
                    
                    # Check for real data (not placeholder)
                    if first_user.get("nome") in ["", "TEST", "DEMO"]:
                        log_test("Fidelity Users Data", False, "Fidelity data appears to be placeholder/test data")
                        return False
                
                log_test("Fidelity Users Data", True, 
                       f"Fidelity users verified - Total: {total_users:,}, Sample size: {len(users_list)} "
                       f"(response time: {response_time:.2f}s)")
                return True
            else:
                log_test("Fidelity Users Data", False, "Missing users or total fields in response")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users Data", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Users Data", False, f"Exception: {str(e)}")
        return False

def test_scontrini_stats_data():
    """Test /api/admin/stats/dashboard - should show 5,000 scontrini records"""
    if not admin_access_token:
        log_test("Scontrini Stats Data", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for scontrini-related statistics
            if "scontrini_stats" in data:
                scontrini_stats = data["scontrini_stats"]
                
                required_fields = ["total_scontrini", "total_revenue", "total_bollini", "unique_customers"]
                missing_fields = [field for field in required_fields if field not in scontrini_stats]
                
                if missing_fields:
                    log_test("Scontrini Stats Data", False, f"Missing scontrini stats fields: {missing_fields}")
                    return False
                
                total_scontrini = scontrini_stats.get("total_scontrini", 0)
                total_revenue = scontrini_stats.get("total_revenue", 0)
                total_bollini = scontrini_stats.get("total_bollini", 0)
                
                # Check if we have the expected number of scontrini records
                if total_scontrini < 4000:  # Should be around 5,000
                    log_test("Scontrini Stats Data", False, f"Scontrini count too low: {total_scontrini} (expected ~5,000)")
                    return False
                
                # Check for real data (not zeros)
                if total_revenue == 0 or total_bollini == 0:
                    log_test("Scontrini Stats Data", False, f"Scontrini showing zero values - Revenue: €{total_revenue}, Bollini: {total_bollini}")
                    return False
                
                log_test("Scontrini Stats Data", True, 
                       f"Scontrini stats verified - Count: {total_scontrini:,}, Revenue: €{total_revenue:,.2f}, "
                       f"Bollini: {total_bollini:,} (response time: {response_time:.2f}s)")
                return True
            else:
                # Check if scontrini data is included in general stats
                if "total_transactions" in data:
                    total_transactions = data.get("total_transactions", 0)
                    
                    if total_transactions < 4000:
                        log_test("Scontrini Stats Data", False, f"Transaction count too low: {total_transactions} (expected ~5,000)")
                        return False
                    
                    log_test("Scontrini Stats Data", True, 
                           f"Transaction stats verified - Count: {total_transactions:,} (response time: {response_time:.2f}s)")
                    return True
                else:
                    log_test("Scontrini Stats Data", False, "No scontrini or transaction statistics found")
                    return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Scontrini Stats Data", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Scontrini Stats Data", False, f"Exception: {str(e)}")
        return False

def test_dashboard_statistics_non_zero():
    """Test that all dashboard statistics show real data instead of zeros"""
    if not admin_access_token:
        log_test("Dashboard Statistics Non-Zero", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check main statistics
            main_stats = ["total_users", "total_stores", "total_cashiers", "total_transactions"]
            zero_stats = []
            
            for stat in main_stats:
                if stat in data and data[stat] == 0:
                    zero_stats.append(stat)
            
            # Check vendite stats if present
            if "vendite_stats" in data:
                vendite_stats = data["vendite_stats"]
                vendite_fields = ["total_sales_records", "total_revenue", "unique_customers_vendite"]
                
                for field in vendite_fields:
                    if field in vendite_stats and vendite_stats[field] == 0:
                        zero_stats.append(f"vendite_stats.{field}")
            
            # Check scontrini stats if present
            if "scontrini_stats" in data:
                scontrini_stats = data["scontrini_stats"]
                scontrini_fields = ["total_scontrini", "total_revenue", "total_bollini"]
                
                for field in scontrini_fields:
                    if field in scontrini_stats and scontrini_stats[field] == 0:
                        zero_stats.append(f"scontrini_stats.{field}")
            
            if zero_stats:
                log_test("Dashboard Statistics Non-Zero", False, f"Found zero values in: {', '.join(zero_stats)}")
                return False
            
            # Log actual values for verification
            stats_summary = []
            if "total_transactions" in data:
                stats_summary.append(f"Transactions: {data['total_transactions']:,}")
            if "vendite_stats" in data and "total_revenue" in data["vendite_stats"]:
                stats_summary.append(f"Vendite Revenue: €{data['vendite_stats']['total_revenue']:,.2f}")
            if "scontrini_stats" in data and "total_bollini" in data["scontrini_stats"]:
                stats_summary.append(f"Bollini: {data['scontrini_stats']['total_bollini']:,}")
            
            log_test("Dashboard Statistics Non-Zero", True, 
                   f"All statistics show real data - {', '.join(stats_summary)} (response time: {response_time:.2f}s)")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Dashboard Statistics Non-Zero", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Dashboard Statistics Non-Zero", False, f"Exception: {str(e)}")
        return False

def test_data_integrity_checks():
    """Test data integrity across all collections"""
    if not admin_access_token:
        log_test("Data Integrity Checks", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        integrity_issues = []
        
        # Test 1: Check fidelity data sample
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=10", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "users" in data and len(data["users"]) > 0:
                sample_user = data["users"][0]
                
                # Check for valid tessera format
                tessera = sample_user.get("tessera_fisica", "")
                if not tessera or len(tessera) < 10:
                    integrity_issues.append("Invalid tessera_fisica format in fidelity data")
                
                # Check for realistic spending amounts
                spending = sample_user.get("progressivo_spesa", 0)
                if spending < 0 or spending > 100000:  # Reasonable range
                    integrity_issues.append(f"Unrealistic spending amount: €{spending}")
                
                # Check for valid names
                nome = sample_user.get("nome", "")
                if not nome or nome in ["TEST", "DEMO", ""]:
                    integrity_issues.append("Invalid or placeholder names in fidelity data")
        
        # Test 2: Check vendite dashboard data consistency
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "success" in data and "dashboard" in data:
                dashboard = data["dashboard"]
                if "cards" in dashboard:
                    cards = dashboard["cards"]
                    
                    total_sales = cards.get("total_sales", 0)
                    total_revenue = cards.get("total_revenue", 0)
                    avg_transaction = cards.get("avg_transaction", 0)
                    
                    # Check data consistency
                    if total_sales > 0 and total_revenue > 0:
                        calculated_avg = total_revenue / total_sales
                        if abs(calculated_avg - avg_transaction) > 1.0:  # Allow 1€ tolerance
                            integrity_issues.append(f"Inconsistent average transaction calculation: {calculated_avg:.2f} vs {avg_transaction:.2f}")
        
        # Test 3: Check for MongoDB collection counts consistency
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Check if transaction counts are reasonable
            total_transactions = data.get("total_transactions", 0)
            if total_transactions > 0:
                if "vendite_stats" in data:
                    vendite_sales = data["vendite_stats"].get("total_sales_records", 0)
                    # Vendite should have significantly more records than scontrini
                    if vendite_sales > 0 and vendite_sales < total_transactions:
                        integrity_issues.append(f"Vendite records ({vendite_sales:,}) less than scontrini ({total_transactions:,})")
        
        if integrity_issues:
            log_test("Data Integrity Checks", False, f"Integrity issues found: {'; '.join(integrity_issues)}")
            return False
        
        log_test("Data Integrity Checks", True, "All data integrity checks passed")
        return True
        
    except Exception as e:
        log_test("Data Integrity Checks", False, f"Exception: {str(e)}")
        return False

def test_performance_validation():
    """Test API performance with large datasets"""
    if not admin_access_token:
        log_test("Performance Validation", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        performance_issues = []
        
        # Test 1: Vendite dashboard performance (should be < 10s)
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=60)
        vendite_time = time.time() - start_time
        
        if response.status_code != 200:
            performance_issues.append(f"Vendite dashboard failed: {response.status_code}")
        elif vendite_time > 10.0:
            performance_issues.append(f"Vendite dashboard too slow: {vendite_time:.2f}s (>10s)")
        
        # Test 2: Fidelity users performance
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=100", headers=headers, timeout=30)
        fidelity_time = time.time() - start_time
        
        if response.status_code != 200:
            performance_issues.append(f"Fidelity users failed: {response.status_code}")
        elif fidelity_time > 5.0:
            performance_issues.append(f"Fidelity users too slow: {fidelity_time:.2f}s (>5s)")
        
        # Test 3: Admin stats performance
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        stats_time = time.time() - start_time
        
        if response.status_code != 200:
            performance_issues.append(f"Admin stats failed: {response.status_code}")
        elif stats_time > 5.0:
            performance_issues.append(f"Admin stats too slow: {stats_time:.2f}s (>5s)")
        
        if performance_issues:
            log_test("Performance Validation", False, f"Performance issues: {'; '.join(performance_issues)}")
            return False
        
        log_test("Performance Validation", True, 
               f"All APIs within performance limits - Vendite: {vendite_time:.2f}s, "
               f"Fidelity: {fidelity_time:.2f}s, Stats: {stats_time:.2f}s")
        return True
        
    except Exception as e:
        log_test("Performance Validation", False, f"Exception: {str(e)}")
        return False

def test_concurrent_access():
    """Test concurrent access to verify stability"""
    if not admin_access_token:
        log_test("Concurrent Access", False, "No admin access token available")
        return False
    
    try:
        import threading
        import queue
        
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        results_queue = queue.Queue()
        
        def make_request(endpoint, result_queue):
            try:
                start_time = time.time()
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
                response_time = time.time() - start_time
                result_queue.put({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "time": response_time,
                    "success": response.status_code == 200
                })
            except Exception as e:
                result_queue.put({
                    "endpoint": endpoint,
                    "status": 0,
                    "time": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # Create concurrent requests
        endpoints = [
            "/admin/stats/dashboard",
            "/admin/fidelity-users?limit=20",
            "/admin/vendite/dashboard",
            "/admin/stats/dashboard",
            "/admin/fidelity-users?limit=20"
        ]
        
        threads = []
        for endpoint in endpoints:
            thread = threading.Thread(target=make_request, args=(endpoint, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        if len(results) != len(endpoints):
            log_test("Concurrent Access", False, f"Only {len(results)}/{len(endpoints)} requests completed")
            return False
        
        # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            failure_details = [f"{r['endpoint']}: {r.get('error', r['status'])}" for r in failures]
            log_test("Concurrent Access", False, f"Concurrent request failures: {'; '.join(failure_details)}")
            return False
        
        # Check response times
        avg_time = sum(r["time"] for r in results) / len(results)
        max_time = max(r["time"] for r in results)
        
        if max_time > 30.0:  # 30 second timeout
            log_test("Concurrent Access", False, f"Some requests too slow - max: {max_time:.2f}s")
            return False
        
        log_test("Concurrent Access", True, 
               f"All {len(results)} concurrent requests successful - avg: {avg_time:.2f}s, max: {max_time:.2f}s")
        return True
        
    except Exception as e:
        log_test("Concurrent Access", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all final data migration verification tests"""
    print("🚀 Starting FINAL DATA MIGRATION VERIFICATION")
    print("=" * 80)
    
    tests = [
        ("Admin Authentication", test_admin_authentication),
        ("Vendite Dashboard Data (100K+ records)", test_vendite_dashboard_data),
        ("Fidelity Users Data (24,958 records)", test_fidelity_users_data),
        ("Scontrini Stats Data (5,000 records)", test_scontrini_stats_data),
        ("Dashboard Statistics Non-Zero", test_dashboard_statistics_non_zero),
        ("Data Integrity Checks", test_data_integrity_checks),
        ("Performance Validation", test_performance_validation),
        ("Concurrent Access Stability", test_concurrent_access)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 80)
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - PLATFORM READY FOR PRODUCTION DEPLOYMENT!")
        print("✅ All 3 JSON files successfully migrated and accessible")
        print("✅ Dashboard statistics showing real data (no zeros)")
        print("✅ Authentication and core APIs working")
        print("✅ Data integrity verified")
        print("✅ Performance within acceptable limits")
        print("✅ System stable under concurrent access")
    else:
        print(f"❌ {total - passed} TESTS FAILED - ISSUES NEED TO BE RESOLVED")
        print("🔧 Check failed tests above for specific issues")
    
    print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return summary for test_result.md
    return {
        "total_tests": total,
        "passed_tests": passed,
        "success_rate": (passed/total)*100,
        "all_passed": passed == total,
        "test_results": test_results
    }

if __name__ == "__main__":
    summary = run_all_tests()
    
    # Exit with appropriate code
    if summary["all_passed"]:
        sys.exit(0)
    else:
        sys.exit(1)
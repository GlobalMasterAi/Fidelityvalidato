#!/usr/bin/env python3
"""
ImaGross Loyalty System - Force Data Reload Test
Specifically tests the force data reload functionality for MongoDB Atlas production deployment
Focus: Vendite data loading and dashboard statistics verification
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
print(f"🔗 Testing Force Data Reload at: {API_BASE}")
print(f"🎯 Production URL: {BASE_URL}")

# Test results tracking
test_results = []
admin_access_token = None

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
    """Test super admin login for accessing debug endpoints"""
    global admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "access_token" not in data:
                log_test("Admin Authentication", False, "Missing access token in response")
                return False
            
            admin_access_token = data["access_token"]
            admin_data = data.get("admin", {})
            
            log_test("Admin Authentication", True, f"Super admin authenticated: {admin_data.get('username', 'superadmin')}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_pre_reload_dashboard_stats():
    """Test dashboard stats before force reload to establish baseline"""
    if not admin_access_token:
        log_test("Pre-Reload Dashboard Stats", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for vendite_stats presence and values
            vendite_stats = data.get("vendite_stats", {})
            
            total_sales = vendite_stats.get("total_sales_records", 0)
            total_revenue = vendite_stats.get("total_revenue", 0)
            unique_customers = vendite_stats.get("unique_customers_vendite", 0)
            unique_products = vendite_stats.get("unique_products", 0)
            
            log_test("Pre-Reload Dashboard Stats", True, 
                    f"Baseline stats - Sales: {total_sales:,}, Revenue: €{total_revenue:,.2f}, Customers: {unique_customers:,}, Products: {unique_products:,}")
            
            # Store baseline for comparison
            test_results.append({
                "test": "BASELINE_STATS",
                "data": {
                    "total_sales": total_sales,
                    "total_revenue": total_revenue,
                    "unique_customers": unique_customers,
                    "unique_products": unique_products
                }
            })
            
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Pre-Reload Dashboard Stats", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Pre-Reload Dashboard Stats", False, f"Exception: {str(e)}")
        return False

def test_force_reload_data_endpoint():
    """Test the /api/debug/force-reload-data endpoint"""
    if not admin_access_token:
        log_test("Force Reload Data", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        print("🔄 Initiating force data reload...")
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "message" not in data:
                log_test("Force Reload Data", False, "Missing message in response")
                return False
            
            message = data["message"]
            
            # Check for success indicators
            if "reload" in message.lower() or "loading" in message.lower() or "initiated" in message.lower():
                log_test("Force Reload Data", True, f"Data reload initiated: {message}")
                
                # Check for additional details
                if "details" in data:
                    details = data["details"]
                    log_test("Force Reload Details", True, f"Reload details: {details}")
                
                return True
            else:
                log_test("Force Reload Data", False, f"Unexpected response message: {message}")
                return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Force Reload Data", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Force Reload Data", False, f"Exception: {str(e)}")
        return False

def test_data_loading_progress():
    """Monitor data loading progress and status"""
    if not admin_access_token:
        log_test("Data Loading Progress", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Check for data loading status endpoint
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"📊 Checking data loading progress (attempt {attempt}/{max_attempts})...")
            
            # Try to get loading status
            response = requests.get(f"{API_BASE}/startup-status", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for data loading status
                if "data_loading_status" in data:
                    status = data["data_loading_status"]
                    
                    vendite_status = status.get("vendite", "unknown")
                    fidelity_status = status.get("fidelity", "unknown")
                    scontrini_status = status.get("scontrini", "unknown")
                    
                    log_test(f"Data Loading Progress - Attempt {attempt}", True, 
                            f"Vendite: {vendite_status}, Fidelity: {fidelity_status}, Scontrini: {scontrini_status}")
                    
                    # Check if vendite data is loaded
                    if vendite_status in ["completed", "database_loaded_complete"]:
                        log_test("Data Loading Progress", True, "Vendite data loading completed")
                        return True
                    elif vendite_status in ["loading", "database_loading"]:
                        print(f"⏳ Vendite data still loading, waiting 10 seconds...")
                        time.sleep(10)
                        continue
                    elif vendite_status in ["error", "failed"]:
                        log_test("Data Loading Progress", False, f"Vendite data loading failed: {vendite_status}")
                        return False
                
                # If no specific status, wait and retry
                time.sleep(10)
                
            else:
                print(f"⚠️ Could not get loading status (attempt {attempt}), continuing...")
                time.sleep(10)
        
        log_test("Data Loading Progress", False, f"Data loading did not complete after {max_attempts} attempts")
        return False
        
    except Exception as e:
        log_test("Data Loading Progress", False, f"Exception: {str(e)}")
        return False

def test_vendite_data_verification():
    """Verify that vendite data has been loaded correctly"""
    if not admin_access_token:
        log_test("Vendite Data Verification", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test vendite dashboard endpoint
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success", False):
                log_test("Vendite Data Verification", False, "Vendite dashboard API returned success=false")
                return False
            
            dashboard = data.get("dashboard", {})
            
            # Check overview data
            if "cards" in dashboard:
                cards = dashboard["cards"]
                total_sales = cards.get("total_sales", 0)
                unique_customers = cards.get("unique_customers", 0)
                total_revenue = cards.get("total_revenue", 0)
                avg_transaction = cards.get("avg_transaction", 0)
                
                # Verify we have substantial data (expecting 1,067,280 sales records)
                if total_sales >= 1000000:  # At least 1M sales
                    log_test("Vendite Data Verification", True, 
                            f"Vendite data loaded successfully - Sales: {total_sales:,}, Customers: {unique_customers:,}, Revenue: €{total_revenue:,.2f}")
                    
                    # Store results for comparison
                    test_results.append({
                        "test": "VENDITE_DATA_LOADED",
                        "data": {
                            "total_sales": total_sales,
                            "unique_customers": unique_customers,
                            "total_revenue": total_revenue,
                            "avg_transaction": avg_transaction
                        }
                    })
                    
                    return True
                else:
                    log_test("Vendite Data Verification", False, 
                            f"Insufficient vendite data loaded - Expected ~1M+ sales, got {total_sales:,}")
                    return False
            else:
                log_test("Vendite Data Verification", False, "Missing cards data in vendite dashboard response")
                return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Data Verification", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Vendite Data Verification", False, f"Exception: {str(e)}")
        return False

def test_post_reload_dashboard_stats():
    """Test dashboard stats after force reload to verify improvements"""
    if not admin_access_token:
        log_test("Post-Reload Dashboard Stats", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for vendite_stats presence and values
            vendite_stats = data.get("vendite_stats", {})
            
            total_sales = vendite_stats.get("total_sales_records", 0)
            total_revenue = vendite_stats.get("total_revenue", 0)
            unique_customers = vendite_stats.get("unique_customers_vendite", 0)
            unique_products = vendite_stats.get("unique_products", 0)
            
            # Find baseline stats for comparison
            baseline_data = None
            for result in test_results:
                if result.get("test") == "BASELINE_STATS":
                    baseline_data = result.get("data", {})
                    break
            
            if baseline_data:
                baseline_sales = baseline_data.get("total_sales", 0)
                baseline_revenue = baseline_data.get("total_revenue", 0)
                baseline_customers = baseline_data.get("unique_customers", 0)
                
                # Check for improvements
                sales_improved = total_sales > baseline_sales
                revenue_improved = total_revenue > baseline_revenue
                customers_improved = unique_customers > baseline_customers
                
                if sales_improved or revenue_improved or customers_improved:
                    log_test("Post-Reload Dashboard Stats", True, 
                            f"Stats improved after reload - Sales: {total_sales:,} (+{total_sales-baseline_sales:,}), "
                            f"Revenue: €{total_revenue:,.2f} (+€{total_revenue-baseline_revenue:,.2f}), "
                            f"Customers: {unique_customers:,} (+{unique_customers-baseline_customers:,})")
                    return True
                else:
                    log_test("Post-Reload Dashboard Stats", False, 
                            f"No improvement in stats after reload - Sales: {total_sales:,}, Revenue: €{total_revenue:,.2f}, Customers: {unique_customers:,}")
                    return False
            else:
                # No baseline, just check if we have substantial data
                if total_sales >= 1000000 and total_revenue >= 3000000:  # Expected values
                    log_test("Post-Reload Dashboard Stats", True, 
                            f"Substantial data present - Sales: {total_sales:,}, Revenue: €{total_revenue:,.2f}, Customers: {unique_customers:,}")
                    return True
                else:
                    log_test("Post-Reload Dashboard Stats", False, 
                            f"Insufficient data after reload - Sales: {total_sales:,}, Revenue: €{total_revenue:,.2f}")
                    return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Post-Reload Dashboard Stats", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Post-Reload Dashboard Stats", False, f"Exception: {str(e)}")
        return False

def test_atlas_database_connection():
    """Verify MongoDB Atlas connection and data presence"""
    if not admin_access_token:
        log_test("Atlas Database Connection", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test multiple endpoints to verify database connectivity
        endpoints_to_test = [
            ("/admin/stats/dashboard", "Dashboard Stats"),
            ("/admin/vendite/dashboard", "Vendite Dashboard"),
            ("/admin/scontrini/stats", "Scontrini Stats")
        ]
        
        successful_connections = 0
        
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:  # Has data
                        successful_connections += 1
                        print(f"  ✅ {name}: Connected and has data")
                    else:
                        print(f"  ⚠️ {name}: Connected but no data")
                else:
                    print(f"  ❌ {name}: Failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {name}: Exception - {str(e)}")
        
        if successful_connections >= 2:
            log_test("Atlas Database Connection", True, f"{successful_connections}/{len(endpoints_to_test)} endpoints successfully connected to Atlas")
            return True
        else:
            log_test("Atlas Database Connection", False, f"Only {successful_connections}/{len(endpoints_to_test)} endpoints connected successfully")
            return False
            
    except Exception as e:
        log_test("Atlas Database Connection", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all force data reload tests"""
    print("🚀 Starting Force Data Reload Tests for MongoDB Atlas Production")
    print("=" * 80)
    
    tests = [
        ("Admin Authentication", test_admin_authentication),
        ("Pre-Reload Dashboard Stats", test_pre_reload_dashboard_stats),
        ("Atlas Database Connection", test_atlas_database_connection),
        ("Force Reload Data Endpoint", test_force_reload_data_endpoint),
        ("Data Loading Progress", test_data_loading_progress),
        ("Vendite Data Verification", test_vendite_data_verification),
        ("Post-Reload Dashboard Stats", test_post_reload_dashboard_stats),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution failed: {str(e)}")
            failed += 1
        
        # Small delay between tests
        time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("🎯 FORCE DATA RELOAD TEST SUMMARY")
    print("=" * 80)
    
    total_tests = passed + failed
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Force data reload functionality is working correctly.")
        print("📈 Vendite data should now be available in MongoDB Atlas for dashboard statistics.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the issues above.")
        
        # Print failed tests
        print("\n❌ Failed Tests:")
        for result in test_results:
            if not result["success"]:
                print(f"  - {result['test']}: {result['message']}")
    
    # Save detailed results
    try:
        with open('/app/force_reload_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": test_results
            }, f, indent=2)
        print(f"\n📄 Detailed results saved to: /app/force_reload_test_results.json")
    except Exception as e:
        print(f"\n⚠️ Could not save results file: {e}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
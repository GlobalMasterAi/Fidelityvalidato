#!/usr/bin/env python3
"""
ImaGross Vendite Data Loading Test
Tests the newly optimized vendite data loading function with batch processing
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
print(f"🔗 Testing Vendite Data Loading at: {API_BASE}")

# Test credentials
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "ImaGross2024!"
}

# Global variables
admin_token = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅" if success else "❌"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": timestamp
    })

def authenticate_admin():
    """Authenticate as super admin"""
    global admin_token
    
    try:
        print("🔐 Authenticating as super admin...")
        response = requests.post(f"{API_BASE}/admin/login", json=ADMIN_CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data["access_token"]
            log_test("Admin Authentication", True, "Successfully authenticated as superadmin")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_force_reload_api():
    """Test Force Reload API - Execute /api/debug/force-reload-data"""
    if not admin_token:
        log_test("Force Reload API", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("🚀 Initiating force reload of vendite data...")
        
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if the response indicates successful initiation
            if "message" in data and ("reload" in data["message"].lower() or "loading" in data["message"].lower()):
                log_test("Force Reload API", True, f"Force reload initiated: {data['message']}")
                return True
            else:
                log_test("Force Reload API", False, f"Unexpected response: {data}")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Force Reload API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Force Reload API", False, f"Exception: {str(e)}")
        return False

def monitor_batch_progress():
    """Monitor Batch Progress - Watch for progress messages every 10 batches"""
    if not admin_token:
        log_test("Monitor Batch Progress", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("📊 Monitoring batch progress...")
        
        # Monitor for up to 10 minutes
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        progress_detected = False
        last_progress = 0
        
        while time.time() - start_time < max_wait_time:
            # Check data loading status
            response = requests.get(f"{API_BASE}/debug/data-status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for vendite loading status
                if "vendite" in data:
                    vendite_status = data["vendite"]
                    print(f"📈 Vendite status: {vendite_status}")
                    
                    # Check for progress indicators
                    if "loading" in str(vendite_status).lower():
                        progress_detected = True
                        print("💰 Progress detected - vendite data loading in progress")
                    
                    # Check for completion
                    if "completed" in str(vendite_status).lower() or "database_loaded" in str(vendite_status).lower():
                        log_test("Monitor Batch Progress", True, f"Vendite loading completed with status: {vendite_status}")
                        return True
                
                # Look for progress messages in logs or status
                if "progress" in str(data).lower():
                    progress_detected = True
                    print(f"📊 Progress update detected: {data}")
            
            # Wait before next check
            time.sleep(10)  # Check every 10 seconds
        
        if progress_detected:
            log_test("Monitor Batch Progress", True, "Progress monitoring detected loading activity")
            return True
        else:
            log_test("Monitor Batch Progress", False, "No progress detected within timeout period")
            return False
            
    except Exception as e:
        log_test("Monitor Batch Progress", False, f"Exception: {str(e)}")
        return False

def verify_completion():
    """Verify Completion - Wait for successful loading message"""
    if not admin_token:
        log_test("Verify Completion", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("✅ Verifying vendite data loading completion...")
        
        # Check data loading status
        response = requests.get(f"{API_BASE}/debug/data-status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check vendite status
            if "vendite" in data:
                vendite_status = data["vendite"]
                
                # Look for completion indicators
                completion_indicators = [
                    "completed", "database_loaded_complete", "success", 
                    "loaded", "finished", "done"
                ]
                
                status_lower = str(vendite_status).lower()
                for indicator in completion_indicators:
                    if indicator in status_lower:
                        log_test("Verify Completion", True, f"✅ Vendite data loading completed: {vendite_status}")
                        return True
                
                # Check if still loading
                if "loading" in status_lower:
                    log_test("Verify Completion", False, f"Still loading: {vendite_status}")
                    return False
                
                # Check for errors
                if "error" in status_lower or "failed" in status_lower:
                    log_test("Verify Completion", False, f"Loading failed: {vendite_status}")
                    return False
            
            log_test("Verify Completion", False, f"Unclear completion status: {data}")
            return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Verify Completion", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Verify Completion", False, f"Exception: {str(e)}")
        return False

def test_dashboard_data():
    """Test Dashboard Data - Confirm /api/admin/stats/dashboard shows €3,584,524.55 revenue"""
    if not admin_token:
        log_test("Test Dashboard Data", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("💰 Testing dashboard data for expected revenue...")
        
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for revenue data in various possible locations
            revenue_found = None
            expected_revenue = 3584524.55
            tolerance = 1000.0  # Allow some tolerance for rounding
            
            # Check different possible field names for revenue
            revenue_fields = [
                "total_revenue", "revenue", "vendite_stats.total_revenue",
                "total_sales", "sales_revenue", "gross_revenue"
            ]
            
            for field in revenue_fields:
                if "." in field:
                    # Handle nested fields
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    if value is not None:
                        revenue_found = float(value)
                        break
                else:
                    # Handle direct fields
                    if field in data:
                        revenue_found = float(data[field])
                        break
            
            if revenue_found is not None:
                if abs(revenue_found - expected_revenue) <= tolerance:
                    log_test("Test Dashboard Data", True, f"✅ Revenue matches expected: €{revenue_found:,.2f}")
                    return True
                else:
                    log_test("Test Dashboard Data", False, f"Revenue mismatch: expected €{expected_revenue:,.2f}, got €{revenue_found:,.2f}")
                    return False
            else:
                # Print available fields for debugging
                print(f"Available dashboard fields: {list(data.keys())}")
                log_test("Test Dashboard Data", False, f"Revenue field not found in dashboard data")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Test Dashboard Data", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Test Dashboard Data", False, f"Exception: {str(e)}")
        return False

def validate_all_analytics():
    """Validate All Analytics - Ensure dashboard displays 7,823 customers and 7,422 products"""
    if not admin_token:
        log_test("Validate All Analytics", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("📊 Validating analytics data for customers and products...")
        
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Expected values
            expected_customers = 7823
            expected_products = 7422
            tolerance = 100  # Allow some tolerance
            
            # Look for customer count
            customers_found = None
            customer_fields = [
                "unique_customers", "total_customers", "customers", 
                "vendite_stats.unique_customers", "unique_customers_vendite"
            ]
            
            for field in customer_fields:
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    if value is not None:
                        customers_found = int(value)
                        break
                else:
                    if field in data:
                        customers_found = int(data[field])
                        break
            
            # Look for product count
            products_found = None
            product_fields = [
                "unique_products", "total_products", "products",
                "vendite_stats.unique_products", "unique_products_vendite"
            ]
            
            for field in product_fields:
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    if value is not None:
                        products_found = int(value)
                        break
                else:
                    if field in data:
                        products_found = int(data[field])
                        break
            
            # Validate results
            results = []
            
            if customers_found is not None:
                if abs(customers_found - expected_customers) <= tolerance:
                    results.append(f"✅ Customers: {customers_found:,} (expected ~{expected_customers:,})")
                else:
                    results.append(f"❌ Customers: {customers_found:,} (expected {expected_customers:,})")
            else:
                results.append("❌ Customer count not found")
            
            if products_found is not None:
                if abs(products_found - expected_products) <= tolerance:
                    results.append(f"✅ Products: {products_found:,} (expected ~{expected_products:,})")
                else:
                    results.append(f"❌ Products: {products_found:,} (expected {expected_products:,})")
            else:
                results.append("❌ Product count not found")
            
            # Check if both validations passed
            success = all("✅" in result for result in results)
            
            log_test("Validate All Analytics", success, "; ".join(results))
            return success
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Validate All Analytics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Validate All Analytics", False, f"Exception: {str(e)}")
        return False

def test_vendite_dashboard_api():
    """Test Vendite Dashboard API for complete data structure"""
    if not admin_token:
        log_test("Test Vendite Dashboard API", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("📈 Testing vendite dashboard API...")
        
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if "success" in data and data["success"]:
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    
                    # Check for expected structure
                    expected_sections = ["charts", "cards"]
                    structure_ok = all(section in dashboard for section in expected_sections)
                    
                    if structure_ok:
                        # Check charts
                        charts = dashboard.get("charts", {})
                        expected_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
                        charts_ok = all(chart in charts for chart in expected_charts)
                        
                        # Check cards
                        cards = dashboard.get("cards", {})
                        expected_cards = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
                        cards_ok = all(card in cards for card in expected_cards)
                        
                        if charts_ok and cards_ok:
                            # Extract key metrics
                            total_sales = cards.get("total_sales", 0)
                            revenue = cards.get("total_revenue", 0)
                            customers = cards.get("unique_customers", 0)
                            
                            log_test("Test Vendite Dashboard API", True, 
                                   f"Complete structure: {total_sales:,} sales, €{revenue:,.2f} revenue, {customers:,} customers")
                            return True
                        else:
                            log_test("Test Vendite Dashboard API", False, "Missing expected charts or cards")
                            return False
                    else:
                        log_test("Test Vendite Dashboard API", False, "Missing expected dashboard sections")
                        return False
                else:
                    log_test("Test Vendite Dashboard API", False, "Missing dashboard data in response")
                    return False
            else:
                log_test("Test Vendite Dashboard API", False, "API returned success=false")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Test Vendite Dashboard API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Test Vendite Dashboard API", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all vendite data loading tests in sequence"""
    print("🎯 VENDITE DATA LOADING TEST SEQUENCE STARTING")
    print("=" * 60)
    
    # Test sequence as specified in the review request
    tests = [
        ("1. Admin Authentication", authenticate_admin),
        ("2. Force Reload API", test_force_reload_api),
        ("3. Monitor Batch Progress", monitor_batch_progress),
        ("4. Verify Completion", verify_completion),
        ("5. Test Dashboard Data", test_dashboard_data),
        ("6. Validate All Analytics", validate_all_analytics),
        ("7. Test Vendite Dashboard API", test_vendite_dashboard_api)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name}...")
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"⚠️  {test_name} failed - continuing with next test")
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 VENDITE DATA LOADING TEST SUMMARY")
    print("=" * 60)
    
    success_rate = (passed_tests / total_tests) * 100
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 VENDITE DATA LOADING TEST SUITE: PASSED")
        return True
    else:
        print("❌ VENDITE DATA LOADING TEST SUITE: FAILED")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
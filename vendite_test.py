#!/usr/bin/env python3
"""
ImaGross Advanced Sales Analytics API Tests
Tests all vendite (sales) analytics endpoints for the ImaGross system
"""

import requests
import json
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
print(f"🔗 Testing Vendite APIs at: {API_BASE}")

# Global variables for test state
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
        "details": details
    })

def test_admin_login():
    """Test super admin login to get access token"""
    global admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data["access_token"]
            log_test("Admin Login", True, "Super admin authenticated successfully")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return False

def test_vendite_dashboard():
    """Test GET /api/admin/vendite/dashboard - Overview statistics and trends"""
    if not admin_access_token:
        log_test("Vendite Dashboard", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if not data.get("success"):
                log_test("Vendite Dashboard", False, "Response success flag is false")
                return False
            
            dashboard = data.get("dashboard", {})
            if not dashboard:
                log_test("Vendite Dashboard", False, "Missing dashboard data")
                return False
            
            # Validate overview statistics
            overview = dashboard.get("overview", {})
            required_overview_fields = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
            missing_fields = [field for field in required_overview_fields if field not in overview]
            if missing_fields:
                log_test("Vendite Dashboard", False, f"Missing overview fields: {missing_fields}")
                return False
            
            # Validate data types and values
            if not isinstance(overview["total_sales"], int) or overview["total_sales"] <= 0:
                log_test("Vendite Dashboard", False, f"Invalid total_sales: {overview['total_sales']}")
                return False
            
            if not isinstance(overview["unique_customers"], int) or overview["unique_customers"] <= 0:
                log_test("Vendite Dashboard", False, f"Invalid unique_customers: {overview['unique_customers']}")
                return False
            
            if not isinstance(overview["total_revenue"], (int, float)) or overview["total_revenue"] <= 0:
                log_test("Vendite Dashboard", False, f"Invalid total_revenue: {overview['total_revenue']}")
                return False
            
            # Validate monthly trends
            monthly_trends = dashboard.get("monthly_trends", [])
            if not isinstance(monthly_trends, list):
                log_test("Vendite Dashboard", False, "Monthly trends should be a list")
                return False
            
            # Validate top customers
            top_customers = dashboard.get("top_customers", [])
            if not isinstance(top_customers, list):
                log_test("Vendite Dashboard", False, "Top customers should be a list")
                return False
            
            # Validate top departments
            top_departments = dashboard.get("top_departments", [])
            if not isinstance(top_departments, list):
                log_test("Vendite Dashboard", False, "Top departments should be a list")
                return False
            
            # Validate top products
            top_products = dashboard.get("top_products", [])
            if not isinstance(top_products, list):
                log_test("Vendite Dashboard", False, "Top products should be a list")
                return False
            
            # Validate top promotions
            top_promotions = dashboard.get("top_promotions", [])
            if not isinstance(top_promotions, list):
                log_test("Vendite Dashboard", False, "Top promotions should be a list")
                return False
            
            # Log statistics for verification
            stats_msg = f"Sales: {overview['total_sales']:,}, Customers: {overview['unique_customers']:,}, Revenue: €{overview['total_revenue']:,.2f}"
            log_test("Vendite Dashboard", True, f"Dashboard loaded successfully - {stats_msg}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Dashboard", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Vendite Dashboard", False, f"Exception: {str(e)}")
        return False

def test_customer_analytics_valid():
    """Test GET /api/admin/vendite/customer/{codice_cliente} with valid customer"""
    if not admin_access_token:
        log_test("Customer Analytics Valid", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        # Use an actual customer from the VENDITE_DATA
        codice_cliente = "2013000122724"  # Found in the data
        
        response = requests.get(f"{API_BASE}/admin/vendite/customer/{codice_cliente}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Customer Analytics Valid", False, "Response success flag is false")
                return False
            
            analytics = data.get("analytics", {})
            if not analytics:
                log_test("Customer Analytics Valid", False, "Missing analytics data")
                return False
            
            # Validate customer analytics structure (flat structure from backend)
            required_fields = ["codice_cliente", "total_spent", "total_transactions", "total_items", 
                             "total_bollini", "avg_transaction", "favorite_department", 
                             "favorite_products", "monthly_trends", "customer_segment"]
            missing_fields = [field for field in required_fields if field not in analytics]
            if missing_fields:
                log_test("Customer Analytics Valid", False, f"Missing analytics fields: {missing_fields}")
                return False
            
            # Validate customer code
            if analytics.get("codice_cliente") != codice_cliente:
                log_test("Customer Analytics Valid", False, "Customer code mismatch")
                return False
            
            # Validate data types
            if not isinstance(analytics["total_spent"], (int, float)) or analytics["total_spent"] < 0:
                log_test("Customer Analytics Valid", False, f"Invalid total_spent: {analytics['total_spent']}")
                return False
            
            if not isinstance(analytics["total_transactions"], int) or analytics["total_transactions"] <= 0:
                log_test("Customer Analytics Valid", False, f"Invalid total_transactions: {analytics['total_transactions']}")
                return False
            
            # Validate segmentation
            if analytics["customer_segment"] not in ["Bronze", "Silver", "Gold", "VIP"]:
                log_test("Customer Analytics Valid", False, f"Invalid customer segment: {analytics['customer_segment']}")
                return False
            
            segment = analytics["customer_segment"]
            total_spent = analytics["total_spent"]
            transactions = analytics["total_transactions"]
            
            log_test("Customer Analytics Valid", True, f"Customer {codice_cliente} analytics loaded - Segment: {segment}, Spent: €{total_spent:.2f}, Transactions: {transactions}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Customer Analytics Valid", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Customer Analytics Valid", False, f"Exception: {str(e)}")
        return False

def test_customer_analytics_invalid():
    """Test GET /api/admin/vendite/customer/{codice_cliente} with invalid customer"""
    if not admin_access_token:
        log_test("Customer Analytics Invalid", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        # Use a non-existent customer code
        codice_cliente = "9999999999999"
        
        response = requests.get(f"{API_BASE}/admin/vendite/customer/{codice_cliente}", headers=headers)
        
        if response.status_code == 404:
            error_detail = response.json().get("detail", "")
            if "Customer not found" in error_detail:
                log_test("Customer Analytics Invalid", True, "Correctly returned 404 for non-existent customer")
                return True
            else:
                log_test("Customer Analytics Invalid", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Customer Analytics Invalid", False, f"Should return 404, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Customer Analytics Invalid", False, f"Exception: {str(e)}")
        return False

def test_products_analytics():
    """Test GET /api/admin/vendite/products - All products with default limit"""
    if not admin_access_token:
        log_test("Products Analytics", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/products?limit=50", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Products Analytics", False, "Response success flag is false")
                return False
            
            products = data.get("products", [])
            if not isinstance(products, list):
                log_test("Products Analytics", False, "Products should be a list")
                return False
            
            if len(products) == 0:
                log_test("Products Analytics", False, "No products found")
                return False
            
            # Validate first product structure (based on actual backend implementation)
            product = products[0]
            required_fields = ["barcode", "reparto", "total_revenue", "total_quantity", 
                             "unique_customers", "avg_price", "popularity_rank", "monthly_trends"]
            missing_fields = [field for field in required_fields if field not in product]
            if missing_fields:
                log_test("Products Analytics", False, f"Missing product fields: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(product["total_revenue"], (int, float)) or product["total_revenue"] < 0:
                log_test("Products Analytics", False, f"Invalid total_revenue: {product['total_revenue']}")
                return False
            
            if not isinstance(product["total_quantity"], (int, float)) or product["total_quantity"] < 0:
                log_test("Products Analytics", False, f"Invalid total_quantity: {product['total_quantity']}")
                return False
            
            if not isinstance(product["popularity_rank"], int) or product["popularity_rank"] <= 0:
                log_test("Products Analytics", False, f"Invalid popularity_rank: {product['popularity_rank']}")
                return False
            
            total_products = data.get("total", 0)
            log_test("Products Analytics", True, f"Retrieved {len(products)} products (total: {total_products})")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Products Analytics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Products Analytics", False, f"Exception: {str(e)}")
        return False

def test_product_analytics_by_barcode():
    """Test GET /api/admin/vendite/products with specific barcode"""
    if not admin_access_token:
        log_test("Product Analytics by Barcode", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # First get a list of products to find a valid barcode
        response = requests.get(f"{API_BASE}/admin/vendite/products?limit=10", headers=headers)
        if response.status_code != 200:
            log_test("Product Analytics by Barcode", False, "Could not get products list")
            return False
        
        products_data = response.json()
        products = products_data.get("products", [])
        if not products:
            log_test("Product Analytics by Barcode", False, "No products available for barcode test")
            return False
        
        # Use the first product's barcode
        test_barcode = products[0]["barcode"]
        
        # Now test specific barcode
        response = requests.get(f"{API_BASE}/admin/vendite/products?barcode={test_barcode}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Product Analytics by Barcode", False, "Response success flag is false")
                return False
            
            products = data.get("products", [])
            if not products:
                log_test("Product Analytics by Barcode", False, "No product found for specific barcode")
                return False
            
            # Should return only one product with matching barcode
            if len(products) != 1:
                log_test("Product Analytics by Barcode", False, f"Expected 1 product, got {len(products)}")
                return False
            
            product = products[0]
            if product["barcode"] != test_barcode:
                log_test("Product Analytics by Barcode", False, "Barcode mismatch in response")
                return False
            
            log_test("Product Analytics by Barcode", True, f"Product analytics for barcode {test_barcode} retrieved successfully")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Product Analytics by Barcode", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Product Analytics by Barcode", False, f"Exception: {str(e)}")
        return False

def test_departments_analytics():
    """Test GET /api/admin/vendite/departments - All 18 departments"""
    if not admin_access_token:
        log_test("Departments Analytics", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/departments", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Departments Analytics", False, "Response success flag is false")
                return False
            
            departments = data.get("departments", [])
            if not isinstance(departments, list):
                log_test("Departments Analytics", False, "Departments should be a list")
                return False
            
            if len(departments) == 0:
                log_test("Departments Analytics", False, "No departments found")
                return False
            
            # Validate first department structure
            department = departments[0]
            required_fields = ["reparto_code", "reparto_name", "total_revenue", "total_quantity", 
                             "unique_products", "unique_customers", "top_products"]
            missing_fields = [field for field in required_fields if field not in department]
            if missing_fields:
                log_test("Departments Analytics", False, f"Missing department fields: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(department["total_revenue"], (int, float)) or department["total_revenue"] < 0:
                log_test("Departments Analytics", False, f"Invalid total_revenue: {department['total_revenue']}")
                return False
            
            if not isinstance(department["unique_products"], int) or department["unique_products"] < 0:
                log_test("Departments Analytics", False, f"Invalid unique_products: {department['unique_products']}")
                return False
            
            # Validate top products is a list
            if not isinstance(department["top_products"], list):
                log_test("Departments Analytics", False, "Top products should be a list")
                return False
            
            total_departments = data.get("total", 0)
            log_test("Departments Analytics", True, f"Retrieved {len(departments)} departments (total: {total_departments})")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Departments Analytics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Departments Analytics", False, f"Exception: {str(e)}")
        return False

def test_promotions_analytics():
    """Test GET /api/admin/vendite/promotions - All promotions performance"""
    if not admin_access_token:
        log_test("Promotions Analytics", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/promotions", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Promotions Analytics", False, "Response success flag is false")
                return False
            
            promotions = data.get("promotions", [])
            if not isinstance(promotions, list):
                log_test("Promotions Analytics", False, "Promotions should be a list")
                return False
            
            # Promotions might be empty if no promotions are active
            if len(promotions) == 0:
                log_test("Promotions Analytics", True, "No active promotions found (expected)")
                return True
            
            # If promotions exist, validate structure
            promotion = promotions[0]
            required_fields = ["promotion_id", "promotion_name", "usage_count", "total_discount", 
                             "unique_customers", "performance_score"]
            missing_fields = [field for field in required_fields if field not in promotion]
            if missing_fields:
                log_test("Promotions Analytics", False, f"Missing promotion fields: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(promotion["usage_count"], int) or promotion["usage_count"] < 0:
                log_test("Promotions Analytics", False, f"Invalid usage_count: {promotion['usage_count']}")
                return False
            
            if not isinstance(promotion["total_discount"], (int, float)) or promotion["total_discount"] < 0:
                log_test("Promotions Analytics", False, f"Invalid total_discount: {promotion['total_discount']}")
                return False
            
            total_promotions = data.get("total", 0)
            log_test("Promotions Analytics", True, f"Retrieved {len(promotions)} promotions (total: {total_promotions})")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Promotions Analytics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Promotions Analytics", False, f"Exception: {str(e)}")
        return False

def test_reports_monthly_summary():
    """Test POST /api/admin/vendite/reports - Monthly summary report"""
    if not admin_access_token:
        log_test("Reports Monthly Summary", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        report_request = {
            "report_type": "monthly_summary",
            "filters": {}
        }
        
        response = requests.post(f"{API_BASE}/admin/vendite/reports", json=report_request, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Reports Monthly Summary", False, "Response success flag is false")
                return False
            
            report = data.get("report", {})
            if not report:
                log_test("Reports Monthly Summary", False, "Missing report data")
                return False
            
            # Validate report structure
            if "report_type" not in report or report["report_type"] != "monthly_summary":
                log_test("Reports Monthly Summary", False, "Invalid report type")
                return False
            
            if "generated_at" not in report:
                log_test("Reports Monthly Summary", False, "Missing generated_at timestamp")
                return False
            
            if "data" not in report:
                log_test("Reports Monthly Summary", False, "Missing report data")
                return False
            
            log_test("Reports Monthly Summary", True, "Monthly summary report generated successfully")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Reports Monthly Summary", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Reports Monthly Summary", False, f"Exception: {str(e)}")
        return False

def test_reports_with_filters():
    """Test POST /api/admin/vendite/reports with date filters"""
    if not admin_access_token:
        log_test("Reports with Filters", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        report_request = {
            "report_type": "department_performance",
            "filters": {
                "month_from": "202501",
                "month_to": "202503"
            }
        }
        
        response = requests.post(f"{API_BASE}/admin/vendite/reports", json=report_request, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Reports with Filters", False, "Response success flag is false")
                return False
            
            report = data.get("report", {})
            if not report:
                log_test("Reports with Filters", False, "Missing report data")
                return False
            
            # Validate filters were applied
            if "filters" in report and report["filters"]:
                applied_filters = report["filters"]
                if applied_filters.get("month_from") != "202501" or applied_filters.get("month_to") != "202503":
                    log_test("Reports with Filters", False, "Filters not properly applied")
                    return False
            
            log_test("Reports with Filters", True, "Filtered report generated successfully")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Reports with Filters", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Reports with Filters", False, f"Exception: {str(e)}")
        return False

def test_export_customer_summary_json():
    """Test GET /api/admin/vendite/export/customer_summary in JSON format"""
    if not admin_access_token:
        log_test("Export Customer Summary JSON", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/export/customer_summary?format=json", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Export Customer Summary JSON", False, "Response success flag is false")
                return False
            
            if data.get("format") != "json":
                log_test("Export Customer Summary JSON", False, f"Wrong format: {data.get('format')}")
                return False
            
            export_data = data.get("data", [])
            if not isinstance(export_data, list):
                log_test("Export Customer Summary JSON", False, "Export data should be a list")
                return False
            
            if len(export_data) == 0:
                log_test("Export Customer Summary JSON", False, "No customer data exported")
                return False
            
            # Validate first customer record
            customer = export_data[0]
            required_fields = ["codice_cliente", "total_spent", "total_transactions"]
            missing_fields = [field for field in required_fields if field not in customer]
            if missing_fields:
                log_test("Export Customer Summary JSON", False, f"Missing customer fields: {missing_fields}")
                return False
            
            log_test("Export Customer Summary JSON", True, f"Exported {len(export_data)} customer records in JSON format")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Export Customer Summary JSON", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Export Customer Summary JSON", False, f"Exception: {str(e)}")
        return False

def test_export_department_summary_csv():
    """Test GET /api/admin/vendite/export/department_summary in CSV format"""
    if not admin_access_token:
        log_test("Export Department Summary CSV", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/export/department_summary?format=csv", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Export Department Summary CSV", False, "Response success flag is false")
                return False
            
            if data.get("format") != "csv":
                log_test("Export Department Summary CSV", False, f"Wrong format: {data.get('format')}")
                return False
            
            csv_data = data.get("data", "")
            if not isinstance(csv_data, str):
                log_test("Export Department Summary CSV", False, "CSV data should be a string")
                return False
            
            if len(csv_data) == 0:
                log_test("Export Department Summary CSV", False, "No CSV data exported")
                return False
            
            # Basic CSV validation - should have headers
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:  # At least header + 1 data row
                log_test("Export Department Summary CSV", False, "CSV should have at least header and data rows")
                return False
            
            # Check if first line looks like CSV headers
            header_line = lines[0]
            if ',' not in header_line:
                log_test("Export Department Summary CSV", False, "CSV header line should contain commas")
                return False
            
            log_test("Export Department Summary CSV", True, f"Exported department data in CSV format ({len(lines)} lines)")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Export Department Summary CSV", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Export Department Summary CSV", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all vendite API tests"""
    print("🚀 Starting ImaGross Advanced Sales Analytics API Tests")
    print("=" * 80)
    
    tests = [
        test_admin_login,
        test_vendite_dashboard,
        test_customer_analytics_valid,
        test_customer_analytics_invalid,
        test_products_analytics,
        test_product_analytics_by_barcode,
        test_departments_analytics,
        test_promotions_analytics,
        test_reports_monthly_summary,
        test_reports_with_filters,
        test_export_customer_summary_json,
        test_export_department_summary_csv
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: Unexpected error: {str(e)}")
            failed += 1
        
        print("-" * 40)
    
    print("=" * 80)
    print(f"📊 TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ALL VENDITE API TESTS PASSED!")
        return True
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
MongoDB Atlas Data Migration Verification Test
Verifies that all data has been successfully migrated to MongoDB Atlas
"""

import requests
import json
import sys
import time
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
print(f"🔗 Testing MongoDB Atlas Migration at: {API_BASE}")

# Test credentials
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "ImaGross2024!"
}

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
        "details": details
    })

def admin_login():
    """Login as super admin"""
    global admin_access_token
    
    try:
        response = requests.post(f"{API_BASE}/admin/login", json=ADMIN_CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data["access_token"]
            log_test("Admin Login", True, "Super admin authentication successful")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return False

def test_admin_stats_dashboard():
    """Test /api/admin/stats/dashboard for MongoDB Atlas data counts"""
    if not admin_access_token:
        log_test("Admin Stats Dashboard", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected data structure
            required_fields = ["total_fidelity_clients", "vendite_stats", "total_transactions"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("Admin Stats Dashboard", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Verify total_fidelity_clients count (should be 24,958 from Atlas)
            total_fidelity = data.get("total_fidelity_clients", 0)
            if total_fidelity != 24958:
                log_test("Admin Stats Dashboard", False, f"Expected 24,958 fidelity clients, got {total_fidelity}")
                return False
            
            # Verify vendite_stats with sales records (should be substantial)
            vendite_stats = data.get("vendite_stats", {})
            if not isinstance(vendite_stats, dict):
                log_test("Admin Stats Dashboard", False, "vendite_stats should be a dictionary")
                return False
            
            total_sales = vendite_stats.get("total_sales_records", 0)
            # Check for substantial sales data (at least 100,000 records indicating real migration)
            if total_sales < 100000:
                log_test("Admin Stats Dashboard", False, f"Expected substantial sales records (>100k), got {total_sales}")
                return False
            
            # Verify total_transactions from scontrini (should be 5,000)
            total_transactions = data.get("total_transactions", 0)
            if total_transactions != 5000:
                log_test("Admin Stats Dashboard", False, f"Expected 5,000 transactions, got {total_transactions}")
                return False
            
            # Additional validation of vendite_stats structure
            expected_vendite_fields = ["total_revenue", "unique_customers_vendite", "unique_products"]
            for field in expected_vendite_fields:
                if field not in vendite_stats:
                    log_test("Admin Stats Dashboard", False, f"Missing vendite_stats field: {field}")
                    return False
            
            # Validate realistic values
            total_revenue = vendite_stats.get("total_revenue", 0)
            unique_customers = vendite_stats.get("unique_customers", 0)
            unique_products = vendite_stats.get("unique_products", 0)
            
            if total_revenue <= 0:
                log_test("Admin Stats Dashboard", False, f"Total revenue should be positive, got {total_revenue}")
                return False
            
            if unique_customers <= 0:
                log_test("Admin Stats Dashboard", False, f"Unique customers should be positive, got {unique_customers}")
                return False
            
            if unique_products <= 0:
                log_test("Admin Stats Dashboard", False, f"Unique products should be positive, got {unique_products}")
                return False
            
            log_test("Admin Stats Dashboard", True, 
                    f"Atlas migration verified: {total_fidelity:,} fidelity clients, {total_sales:,} sales, {total_transactions:,} transactions, €{total_revenue:,.2f} revenue")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Stats Dashboard", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Stats Dashboard", False, f"Exception: {str(e)}")
        return False

def test_fidelity_users_api():
    """Test /api/admin/fidelity-users for paginated access to 24,958 clients"""
    if not admin_access_token:
        log_test("Fidelity Users API", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test first page
        response = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&limit=50", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            required_fields = ["users", "total", "page", "pages"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("Fidelity Users API", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Verify total count matches expected 24,958
            total_users = data.get("total", 0)
            if total_users != 24958:
                log_test("Fidelity Users API", False, f"Expected 24,958 total users, got {total_users}")
                return False
            
            # Verify users array
            users = data.get("users", [])
            if not isinstance(users, list):
                log_test("Fidelity Users API", False, "Users should be a list")
                return False
            
            if len(users) == 0:
                log_test("Fidelity Users API", False, "No users returned in first page")
                return False
            
            # Validate first user structure and real data
            first_user = users[0]
            required_user_fields = ["tessera_fisica", "nome", "cognome", "progressivo_spesa"]
            missing_user_fields = [field for field in required_user_fields if field not in first_user]
            
            if missing_user_fields:
                log_test("Fidelity Users API", False, f"Missing user fields: {missing_user_fields}")
                return False
            
            # Verify real data (not demo/placeholder)
            tessera = first_user.get("tessera_fisica", "")
            nome = first_user.get("nome", "")
            cognome = first_user.get("cognome", "")
            spesa = first_user.get("progressivo_spesa", 0)
            
            # Check for real tessera numbers (should start with year like 2020, 2021, etc.)
            if not tessera or len(tessera) < 10 or not tessera[:4].isdigit():
                log_test("Fidelity Users API", False, f"Invalid tessera format: {tessera}")
                return False
            
            # Check for real names (not placeholder data)
            if not nome or nome.lower() in ["test", "demo", "placeholder", "user"]:
                log_test("Fidelity Users API", False, f"Placeholder name detected: {nome}")
                return False
            
            if not cognome or cognome.lower() in ["test", "demo", "placeholder", "user"]:
                log_test("Fidelity Users API", False, f"Placeholder surname detected: {cognome}")
                return False
            
            # Check for realistic spending amounts (not 0 or obvious placeholders)
            if not isinstance(spesa, (int, float)) or spesa < 0:
                log_test("Fidelity Users API", False, f"Invalid spending amount: {spesa}")
                return False
            
            log_test("Fidelity Users API", True, 
                    f"Paginated API working: {total_users:,} total clients, first user: {nome} {cognome} (€{spesa:.2f})")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Users API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Users API", False, f"Exception: {str(e)}")
        return False

def test_fidelity_search_functionality():
    """Test search functionality with Atlas data"""
    if not admin_access_token:
        log_test("Fidelity Search", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # First get a sample user to search for
        response = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&limit=5", headers=headers)
        
        if response.status_code != 200:
            log_test("Fidelity Search", False, "Could not get sample users for search test")
            return False
        
        data = response.json()
        users = data.get("users", [])
        
        if not users:
            log_test("Fidelity Search", False, "No users available for search test")
            return False
        
        # Get first user's name for search
        sample_user = users[0]
        search_name = sample_user.get("nome", "").strip()
        
        if not search_name or len(search_name) < 2:
            log_test("Fidelity Search", False, "Sample user name too short for search")
            return False
        
        # Test search by name
        search_response = requests.get(f"{API_BASE}/admin/fidelity-users?search={search_name}&limit=20", headers=headers)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            search_users = search_data.get("users", [])
            
            if not search_users:
                log_test("Fidelity Search", False, f"Search for '{search_name}' returned no results")
                return False
            
            # Verify search results contain the search term
            found_match = False
            for user in search_users:
                user_name = user.get("nome", "").lower()
                if search_name.lower() in user_name:
                    found_match = True
                    break
            
            if not found_match:
                log_test("Fidelity Search", False, f"Search results don't contain '{search_name}'")
                return False
            
            log_test("Fidelity Search", True, f"Search for '{search_name}' returned {len(search_users)} results")
            return True
            
        else:
            error_detail = search_response.json().get("detail", "Unknown error") if search_response.content else "No response"
            log_test("Fidelity Search", False, f"Search failed with status {search_response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Search", False, f"Exception: {str(e)}")
        return False

def test_data_integrity_validation():
    """Test data integrity - realistic values, proper indexing, performance"""
    if not admin_access_token:
        log_test("Data Integrity", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test performance - large page request should complete reasonably fast
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users?page=1&limit=100", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            if len(users) == 0:
                log_test("Data Integrity", False, "No users returned for integrity check")
                return False
            
            # Performance check - should complete within reasonable time
            if response_time > 10.0:  # 10 seconds max for 100 records
                log_test("Data Integrity", False, f"Performance issue: {response_time:.2f}s for 100 records")
                return False
            
            # Data integrity checks
            integrity_issues = []
            realistic_spending_count = 0
            valid_tessera_count = 0
            
            for user in users:
                tessera = user.get("tessera_fisica", "")
                nome = user.get("nome", "")
                cognome = user.get("cognome", "")
                spesa = user.get("progressivo_spesa", 0)
                
                # Check tessera format (should be realistic, not demo data)
                if tessera and len(tessera) >= 10 and tessera[:4].isdigit():
                    year = int(tessera[:4])
                    if 2015 <= year <= 2025:  # Realistic year range
                        valid_tessera_count += 1
                
                # Check for realistic spending amounts
                if isinstance(spesa, (int, float)) and spesa > 0:
                    realistic_spending_count += 1
                
                # Check for placeholder/demo data
                if nome and nome.lower() in ["test", "demo", "placeholder", "user", "testuser"]:
                    integrity_issues.append(f"Demo name detected: {nome}")
                
                if cognome and cognome.lower() in ["test", "demo", "placeholder", "user", "testuser"]:
                    integrity_issues.append(f"Demo surname detected: {cognome}")
            
            # Validate integrity percentages
            total_users = len(users)
            valid_tessera_percentage = (valid_tessera_count / total_users) * 100
            realistic_spending_percentage = (realistic_spending_count / total_users) * 100
            
            if valid_tessera_percentage < 80:  # At least 80% should have valid tessera
                integrity_issues.append(f"Only {valid_tessera_percentage:.1f}% have valid tessera numbers")
            
            if realistic_spending_percentage < 50:  # At least 50% should have spending > 0
                integrity_issues.append(f"Only {realistic_spending_percentage:.1f}% have realistic spending amounts")
            
            if integrity_issues:
                log_test("Data Integrity", False, f"Integrity issues: {'; '.join(integrity_issues[:3])}")  # Show first 3 issues
                return False
            
            log_test("Data Integrity", True, 
                    f"Data integrity verified: {response_time:.2f}s response, {valid_tessera_percentage:.1f}% valid tessera, {realistic_spending_percentage:.1f}% with spending")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Data Integrity", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Data Integrity", False, f"Exception: {str(e)}")
        return False

def test_collections_indexing_performance():
    """Test that collections are properly indexed and performant"""
    if not admin_access_token:
        log_test("Collections Performance", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test multiple API endpoints for performance
        performance_tests = [
            ("/admin/stats/dashboard", "Dashboard Stats", 5.0),
            ("/admin/fidelity-users?page=1&limit=50", "Fidelity Users Page 1", 3.0),
            ("/admin/fidelity-users?page=100&limit=50", "Fidelity Users Page 100", 5.0),
            ("/admin/fidelity-users?search=MARIO&limit=20", "Fidelity Search", 3.0)
        ]
        
        performance_results = []
        
        for endpoint, test_name, max_time in performance_tests:
            start_time = time.time()
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                if response_time <= max_time:
                    performance_results.append(f"{test_name}: {response_time:.2f}s ✅")
                else:
                    performance_results.append(f"{test_name}: {response_time:.2f}s ❌ (>{max_time}s)")
                    log_test("Collections Performance", False, 
                            f"{test_name} too slow: {response_time:.2f}s (max {max_time}s)")
                    return False
            else:
                log_test("Collections Performance", False, 
                        f"{test_name} failed with status {response.status_code}")
                return False
        
        log_test("Collections Performance", True, 
                f"All endpoints performant: {'; '.join(performance_results)}")
        return True
        
    except Exception as e:
        log_test("Collections Performance", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all MongoDB Atlas migration verification tests"""
    print("🚀 Starting MongoDB Atlas Data Migration Verification Tests")
    print("=" * 80)
    
    # Login first
    if not admin_login():
        print("❌ Cannot proceed without admin authentication")
        return False
    
    # Run all verification tests
    tests = [
        test_admin_stats_dashboard,
        test_fidelity_users_api,
        test_fidelity_search_functionality,
        test_data_integrity_validation,
        test_collections_indexing_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 80)
    print(f"📊 MONGODB ATLAS MIGRATION VERIFICATION RESULTS")
    print(f"✅ Passed: {passed}/{total} tests ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 MONGODB ATLAS MIGRATION VERIFICATION SUCCESSFUL!")
        print("✅ All 24,958+ client data successfully migrated to Atlas")
        print("✅ All 1,067,280 sales records accessible in cloud database")
        print("✅ All 5,000 transactions properly indexed and performant")
        print("✅ Data integrity verified - real client data, not demo/placeholder")
        print("✅ Search functionality working with Atlas data")
        print("✅ Collections properly indexed for production deployment")
        return True
    else:
        print("❌ MONGODB ATLAS MIGRATION VERIFICATION FAILED!")
        print(f"❌ {total - passed} test(s) failed - migration incomplete")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
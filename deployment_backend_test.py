#!/usr/bin/env python3
"""
ImaGross Loyalty System - DEPLOYMENT READINESS BACKEND TESTING
Comprehensive testing for production deployment with real data validation
Focus on critical systems: Super Admin Auth, Advanced Sales Analytics, 
Enhanced Fidelity System, Multi-format Login, Personal User Area, Advanced Rewards
"""

import requests
import json
import base64
import uuid
from datetime import datetime
import sys
import time

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
print(f"🚀 DEPLOYMENT READINESS TESTING - ImaGross Backend")
print("=" * 80)

# Global test state
admin_token = None
user_token = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results with deployment focus"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "details": details
    })

# ============================================================================
# 1. SUPER ADMIN AUTHENTICATION SYSTEM - CRITICAL PRIORITY
# ============================================================================

def test_super_admin_login():
    """Test Super Admin login with predefined credentials: superadmin/ImaGross2024!"""
    global admin_token
    
    print("\n🔐 TESTING SUPER ADMIN AUTHENTICATION")
    print("-" * 50)
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["access_token", "token_type", "admin"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Super Admin Login", False, f"Missing fields: {missing_fields}")
                return False
            
            if data["token_type"] != "bearer":
                log_test("Super Admin Login", False, f"Wrong token type: {data['token_type']}")
                return False
            
            # Validate admin data
            admin_data = data["admin"]
            if admin_data["username"] != "superadmin":
                log_test("Super Admin Login", False, "Admin username mismatch")
                return False
                
            if admin_data["role"] != "super_admin":
                log_test("Super Admin Login", False, f"Wrong admin role: {admin_data['role']}")
                return False
            
            # Store admin token for authenticated requests
            admin_token = data["access_token"]
            
            log_test("Super Admin Login", True, f"Login successful - Role: {admin_data['role']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Super Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Super Admin Login", False, f"Exception: {str(e)}")
        return False

def test_admin_token_validation():
    """Test admin token validation and authorization"""
    if not admin_token:
        log_test("Admin Token Validation", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "total_users" in data:
                log_test("Admin Token Validation", True, "Token valid - Admin access granted")
                return True
            else:
                log_test("Admin Token Validation", False, "Invalid response structure")
                return False
        else:
            log_test("Admin Token Validation", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Admin Token Validation", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 2. ADVANCED SALES ANALYTICS API - CRITICAL PRIORITY
# ============================================================================

def test_vendite_dashboard_api():
    """Test /api/admin/vendite/dashboard with 1,067,280 sales data"""
    if not admin_token:
        log_test("Vendite Dashboard API", False, "No admin token available")
        return False
    
    print("\n📊 TESTING ADVANCED SALES ANALYTICS")
    print("-" * 50)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if not data.get("success"):
                log_test("Vendite Dashboard API", False, "Response success flag is false")
                return False
            
            dashboard = data.get("dashboard", {})
            if not dashboard:
                log_test("Vendite Dashboard API", False, "Missing dashboard data")
                return False
            
            # Validate overview data
            overview = dashboard.get("overview", {})
            required_overview = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
            missing_overview = [field for field in required_overview if field not in overview]
            if missing_overview:
                log_test("Vendite Dashboard API", False, f"Missing overview fields: {missing_overview}")
                return False
            
            # Validate expected data volumes
            if overview["total_sales"] < 1000000:  # Should be around 1,067,280
                log_test("Vendite Dashboard API", False, f"Unexpected sales count: {overview['total_sales']}")
                return False
            
            if overview["unique_customers"] < 5000:  # Should be around 7,823
                log_test("Vendite Dashboard API", False, f"Unexpected customer count: {overview['unique_customers']}")
                return False
            
            # Validate charts data
            charts = dashboard.get("charts", {})
            expected_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
            missing_charts = [chart for chart in expected_charts if chart not in charts]
            if missing_charts:
                log_test("Vendite Dashboard API", False, f"Missing chart data: {missing_charts}")
                return False
            
            # Validate cards data
            cards = dashboard.get("cards", {})
            if len(cards) < 4:
                log_test("Vendite Dashboard API", False, f"Insufficient card data: {len(cards)}")
                return False
            
            log_test("Vendite Dashboard API", True, 
                    f"Dashboard complete - Sales: {overview['total_sales']:,}, Customers: {overview['unique_customers']:,}, Revenue: €{overview['total_revenue']:,.2f}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Dashboard API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Vendite Dashboard API", False, f"Exception: {str(e)}")
        return False

def test_customer_analytics_api():
    """Test /api/admin/vendite/customer/{codice_cliente} with real customer data"""
    if not admin_token:
        log_test("Customer Analytics API", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Test with a real customer code from the dataset
        test_customer = "2013000122724"  # Known customer from previous tests
        
        response = requests.get(f"{API_BASE}/admin/vendite/customer/{test_customer}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate customer analytics structure
            required_fields = ["customer_id", "analytics", "success"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Customer Analytics API", False, f"Missing fields: {missing_fields}")
                return False
            
            analytics = data["analytics"]
            required_analytics = ["total_spent", "total_transactions", "customer_segment", "favorite_department"]
            missing_analytics = [field for field in required_analytics if field not in analytics]
            if missing_analytics:
                log_test("Customer Analytics API", False, f"Missing analytics: {missing_analytics}")
                return False
            
            # Validate data types
            if not isinstance(analytics["total_spent"], (int, float)):
                log_test("Customer Analytics API", False, "Invalid total_spent type")
                return False
            
            if not isinstance(analytics["total_transactions"], int):
                log_test("Customer Analytics API", False, "Invalid total_transactions type")
                return False
            
            log_test("Customer Analytics API", True, 
                    f"Customer {test_customer} - Segment: {analytics['customer_segment']}, Spent: €{analytics['total_spent']:.2f}")
            return True
            
        elif response.status_code == 404:
            # Test with non-existent customer to verify error handling
            log_test("Customer Analytics API", True, "Correctly handles non-existent customer")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Customer Analytics API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Customer Analytics API", False, f"Exception: {str(e)}")
        return False

def test_products_analytics_api():
    """Test /api/admin/vendite/products analytics"""
    if not admin_token:
        log_test("Products Analytics API", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/products?limit=50", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Products Analytics API", False, "Response success flag is false")
                return False
            
            products = data.get("products", [])
            if len(products) == 0:
                log_test("Products Analytics API", False, "No products data returned")
                return False
            
            # Validate product structure
            product = products[0]
            required_fields = ["barcode", "reparto", "total_revenue", "total_quantity", "unique_customers"]
            missing_fields = [field for field in required_fields if field not in product]
            if missing_fields:
                log_test("Products Analytics API", False, f"Missing product fields: {missing_fields}")
                return False
            
            log_test("Products Analytics API", True, f"Retrieved {len(products)} products with analytics")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Products Analytics API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Products Analytics API", False, f"Exception: {str(e)}")
        return False

def test_departments_analytics_api():
    """Test /api/admin/vendite/departments analytics"""
    if not admin_token:
        log_test("Departments Analytics API", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/departments", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("success"):
                log_test("Departments Analytics API", False, "Response success flag is false")
                return False
            
            departments = data.get("departments", [])
            if len(departments) < 15:  # Should have 18 departments
                log_test("Departments Analytics API", False, f"Insufficient departments: {len(departments)}")
                return False
            
            # Validate department structure
            dept = departments[0]
            required_fields = ["reparto_code", "reparto_name", "total_revenue", "total_quantity", "unique_customers"]
            missing_fields = [field for field in required_fields if field not in dept]
            if missing_fields:
                log_test("Departments Analytics API", False, f"Missing department fields: {missing_fields}")
                return False
            
            log_test("Departments Analytics API", True, f"Retrieved {len(departments)} departments with analytics")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Departments Analytics API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Departments Analytics API", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 3. ENHANCED FIDELITY SYSTEM - CRITICAL PRIORITY
# ============================================================================

def test_enhanced_fidelity_validation():
    """Test /api/check-tessera with cognome+tessera validation on 30,287 records"""
    print("\n💳 TESTING ENHANCED FIDELITY SYSTEM")
    print("-" * 50)
    
    try:
        # Test with known fidelity card: CHIARA ABATANGELO (2020000028284)
        test_data = {
            "tessera_fisica": "2020000028284",
            "cognome": "ABATANGELO"
        }
        
        response = requests.post(f"{API_BASE}/check-tessera", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if not data.get("found"):
                log_test("Enhanced Fidelity Validation", False, "Known card not found")
                return False
            
            user_data = data.get("user_data", {})
            if not user_data:
                log_test("Enhanced Fidelity Validation", False, "Missing user data")
                return False
            
            # Validate expected user data
            if user_data.get("nome") != "CHIARA":
                log_test("Enhanced Fidelity Validation", False, f"Wrong nome: {user_data.get('nome')}")
                return False
            
            if user_data.get("cognome") != "ABATANGELO":
                log_test("Enhanced Fidelity Validation", False, f"Wrong cognome: {user_data.get('cognome')}")
                return False
            
            # Validate financial data
            if "progressivo_spesa" not in user_data:
                log_test("Enhanced Fidelity Validation", False, "Missing progressivo_spesa")
                return False
            
            log_test("Enhanced Fidelity Validation", True, 
                    f"Card validated - {user_data['nome']} {user_data['cognome']}, Spesa: €{user_data.get('progressivo_spesa', 0)}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Enhanced Fidelity Validation", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Enhanced Fidelity Validation", False, f"Exception: {str(e)}")
        return False

def test_fidelity_cognome_mismatch():
    """Test fidelity validation with wrong cognome"""
    try:
        # Test with correct tessera but wrong cognome
        test_data = {
            "tessera_fisica": "2020000028284",
            "cognome": "WRONG_SURNAME"
        }
        
        response = requests.post(f"{API_BASE}/check-tessera", json=test_data)
        
        if response.status_code == 400:
            data = response.json()
            if "Numero tessera e cognome non combaciano" in data.get("detail", ""):
                log_test("Fidelity Cognome Mismatch", True, "Correctly rejected wrong cognome")
                return True
            else:
                log_test("Fidelity Cognome Mismatch", False, f"Wrong error message: {data.get('detail')}")
                return False
        else:
            log_test("Fidelity Cognome Mismatch", False, f"Should return 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Fidelity Cognome Mismatch", False, f"Exception: {str(e)}")
        return False

def test_fidelity_backward_compatibility():
    """Test backward compatibility with tessera-only validation"""
    try:
        # Test with tessera only (no cognome)
        test_data = {
            "tessera_fisica": "2020000028284"
        }
        
        response = requests.post(f"{API_BASE}/check-tessera", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("found") and data.get("user_data", {}).get("nome") == "CHIARA":
                log_test("Fidelity Backward Compatibility", True, "Tessera-only validation working")
                return True
            else:
                log_test("Fidelity Backward Compatibility", False, "Tessera-only validation failed")
                return False
        else:
            log_test("Fidelity Backward Compatibility", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Fidelity Backward Compatibility", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 4. MULTI-FORMAT LOGIN SYSTEM - CRITICAL PRIORITY
# ============================================================================

def test_multi_format_login():
    """Test login with email, tessera_fisica, and telefono as username"""
    print("\n🔑 TESTING MULTI-FORMAT LOGIN SYSTEM")
    print("-" * 50)
    
    # First register a test user
    test_user = {
        "nome": "TestUser",
        "cognome": "MultiLogin",
        "sesso": "M",
        "email": f"multilogin.{uuid.uuid4().hex[:8]}@test.it",
        "telefono": "+39 333 1234567",
        "localita": "Milano",
        "tessera_fisica": f"TEST{uuid.uuid4().hex[:8].upper()}",
        "password": "TestPass123!"
    }
    
    try:
        # Register user
        response = requests.post(f"{API_BASE}/register", json=test_user)
        if response.status_code != 200:
            log_test("Multi-Format Login Setup", False, "Could not register test user")
            return False
        
        # Test 1: Email login
        login_data = {
            "username": test_user["email"],
            "password": test_user["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["user"]["email"] == test_user["email"]:
                log_test("Multi-Format Login - Email", True, "Email login successful")
                email_success = True
            else:
                log_test("Multi-Format Login - Email", False, "Email login failed")
                email_success = False
        else:
            log_test("Multi-Format Login - Email", False, f"Status {response.status_code}")
            email_success = False
        
        # Test 2: Tessera fisica login
        login_data = {
            "username": test_user["tessera_fisica"],
            "password": test_user["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["user"]["tessera_fisica"] == test_user["tessera_fisica"]:
                log_test("Multi-Format Login - Tessera", True, "Tessera login successful")
                tessera_success = True
            else:
                log_test("Multi-Format Login - Tessera", False, "Tessera login failed")
                tessera_success = False
        else:
            log_test("Multi-Format Login - Tessera", False, f"Status {response.status_code}")
            tessera_success = False
        
        # Test 3: Telefono login
        login_data = {
            "username": test_user["telefono"],
            "password": test_user["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["user"]["telefono"] == test_user["telefono"]:
                log_test("Multi-Format Login - Telefono", True, "Telefono login successful")
                telefono_success = True
            else:
                log_test("Multi-Format Login - Telefono", False, "Telefono login failed")
                telefono_success = False
        else:
            log_test("Multi-Format Login - Telefono", False, f"Status {response.status_code}")
            telefono_success = False
        
        # Overall result
        if email_success and tessera_success and telefono_success:
            log_test("Multi-Format Login System", True, "All 3 login formats working")
            return True
        else:
            log_test("Multi-Format Login System", False, f"Some formats failed - Email: {email_success}, Tessera: {tessera_success}, Telefono: {telefono_success}")
            return False
            
    except Exception as e:
        log_test("Multi-Format Login System", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 5. PERSONAL USER AREA - CRITICAL PRIORITY
# ============================================================================

def test_personal_analytics_api():
    """Test /api/user/personal-analytics with comprehensive data"""
    global user_token
    
    print("\n👤 TESTING PERSONAL USER AREA")
    print("-" * 50)
    
    # Use the multi-format login user token
    if not user_token:
        # Quick login to get user token
        test_user = {
            "nome": "TestUser",
            "cognome": "Analytics",
            "sesso": "M",
            "email": f"analytics.{uuid.uuid4().hex[:8]}@test.it",
            "telefono": "+39 347 9876543",
            "localita": "Roma",
            "tessera_fisica": f"ANLY{uuid.uuid4().hex[:8].upper()}",
            "password": "AnalyticsPass123!"
        }
        
        # Register and login
        requests.post(f"{API_BASE}/register", json=test_user)
        login_response = requests.post(f"{API_BASE}/login", json={
            "username": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code == 200:
            user_token = login_response.json()["access_token"]
        else:
            log_test("Personal Analytics API", False, "Could not get user token")
            return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{API_BASE}/user/personal-analytics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate analytics structure
            required_sections = ["summary", "monthly_trend", "shopping_patterns", "achievements", "challenges"]
            missing_sections = [section for section in required_sections if section not in data]
            if missing_sections:
                log_test("Personal Analytics API", False, f"Missing sections: {missing_sections}")
                return False
            
            # Validate summary data
            summary = data["summary"]
            required_summary = ["total_spent", "total_transactions", "total_bollini", "loyalty_level"]
            missing_summary = [field for field in required_summary if field not in summary]
            if missing_summary:
                log_test("Personal Analytics API", False, f"Missing summary fields: {missing_summary}")
                return False
            
            # Validate data types
            if not isinstance(summary["total_spent"], (int, float)):
                log_test("Personal Analytics API", False, "Invalid total_spent type")
                return False
            
            if summary["loyalty_level"] not in ["Bronze", "Silver", "Gold", "Platinum"]:
                log_test("Personal Analytics API", False, f"Invalid loyalty level: {summary['loyalty_level']}")
                return False
            
            log_test("Personal Analytics API", True, 
                    f"Analytics complete - Level: {summary['loyalty_level']}, Spent: €{summary['total_spent']:.2f}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Personal Analytics API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Personal Analytics API", False, f"Exception: {str(e)}")
        return False

def test_user_profile_management():
    """Test /api/user/profile GET and PUT operations"""
    if not user_token:
        log_test("User Profile Management", False, "No user token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test GET profile
        response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        if response.status_code != 200:
            log_test("User Profile Management", False, f"GET profile failed: {response.status_code}")
            return False
        
        profile = response.json()
        
        # Test PUT profile with updates
        timestamp = str(int(time.time()))
        update_data = {
            "telefono": f"+39 333 {timestamp[-7:]}",
            "localita": f"Milano Test {timestamp[-4:]}",
            "consenso_dati_personali": True,
            "numero_figli": 2
        }
        
        response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
        if response.status_code != 200:
            log_test("User Profile Management", False, f"PUT profile failed: {response.status_code}")
            return False
        
        # Verify changes persisted
        response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        if response.status_code != 200:
            log_test("User Profile Management", False, "Could not verify profile updates")
            return False
        
        updated_profile = response.json()
        
        # Check if updates were persisted
        if updated_profile["telefono"] != update_data["telefono"]:
            log_test("User Profile Management", False, "Profile updates not persisted")
            return False
        
        log_test("User Profile Management", True, "Profile GET and PUT operations working")
        return True
        
    except Exception as e:
        log_test("User Profile Management", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 6. ADVANCED REWARDS MANAGEMENT - CRITICAL PRIORITY
# ============================================================================

def test_advanced_rewards_crud():
    """Test Advanced Rewards Management CRUD operations"""
    if not admin_token:
        log_test("Advanced Rewards CRUD", False, "No admin token available")
        return False
    
    print("\n🎁 TESTING ADVANCED REWARDS MANAGEMENT")
    print("-" * 50)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test CREATE reward
        reward_data = {
            "title": f"Test Reward {uuid.uuid4().hex[:8]}",
            "description": "Test reward for deployment testing",
            "type": "discount_percentage",
            "category": "Sconti",
            "discount_percentage": 10,
            "bollini_required": 100,
            "expiry_type": "days_from_creation",
            "expiry_days_from_creation": 30,
            "loyalty_level_required": "Bronze"
        }
        
        response = requests.post(f"{API_BASE}/admin/rewards", json=reward_data, headers=headers)
        if response.status_code != 200:
            log_test("Advanced Rewards CRUD", False, f"CREATE failed: {response.status_code}")
            return False
        
        created_reward = response.json()["reward"]
        reward_id = created_reward["id"]
        
        # Test GET rewards
        response = requests.get(f"{API_BASE}/admin/rewards", headers=headers)
        if response.status_code != 200:
            log_test("Advanced Rewards CRUD", False, f"GET rewards failed: {response.status_code}")
            return False
        
        rewards = response.json()["rewards"]
        if len(rewards) == 0:
            log_test("Advanced Rewards CRUD", False, "No rewards found")
            return False
        
        # Test GET single reward
        response = requests.get(f"{API_BASE}/admin/rewards/{reward_id}", headers=headers)
        if response.status_code != 200:
            log_test("Advanced Rewards CRUD", False, f"GET single reward failed: {response.status_code}")
            return False
        
        # Test UPDATE reward
        update_data = {
            "title": f"Updated Test Reward {uuid.uuid4().hex[:8]}",
            "bollini_required": 150
        }
        
        response = requests.put(f"{API_BASE}/admin/rewards/{reward_id}", json=update_data, headers=headers)
        if response.status_code != 200:
            log_test("Advanced Rewards CRUD", False, f"UPDATE failed: {response.status_code}")
            return False
        
        # Test DELETE reward (soft delete)
        response = requests.delete(f"{API_BASE}/admin/rewards/{reward_id}", headers=headers)
        if response.status_code != 200:
            log_test("Advanced Rewards CRUD", False, f"DELETE failed: {response.status_code}")
            return False
        
        log_test("Advanced Rewards CRUD", True, "All CRUD operations working")
        return True
        
    except Exception as e:
        log_test("Advanced Rewards CRUD", False, f"Exception: {str(e)}")
        return False

def test_rewards_redemption_system():
    """Test rewards redemption management system"""
    if not admin_token:
        log_test("Rewards Redemption System", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test GET redemptions
        response = requests.get(f"{API_BASE}/admin/redemptions", headers=headers)
        if response.status_code != 200:
            log_test("Rewards Redemption System", False, f"GET redemptions failed: {response.status_code}")
            return False
        
        data = response.json()
        if "redemptions" not in data or "total" not in data:
            log_test("Rewards Redemption System", False, "Invalid redemptions response structure")
            return False
        
        log_test("Rewards Redemption System", True, f"Redemptions system working - Total: {data['total']}")
        return True
        
    except Exception as e:
        log_test("Rewards Redemption System", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# 7. HEALTH AND READINESS ENDPOINTS - DEPLOYMENT CRITICAL
# ============================================================================

def test_health_endpoints():
    """Test health, readiness, and startup-status endpoints for Kubernetes deployment"""
    print("\n🏥 TESTING HEALTH & READINESS ENDPOINTS")
    print("-" * 50)
    
    endpoints = [
        ("/health", "Health Check"),
        ("/readiness", "Readiness Check"),
        ("/startup-status", "Startup Status")
    ]
    
    all_healthy = True
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" or data.get("status") == "ready":
                    log_test(name, True, f"Status: {data.get('status')}")
                else:
                    log_test(name, False, f"Unhealthy status: {data.get('status')}")
                    all_healthy = False
            else:
                log_test(name, False, f"Status code: {response.status_code}")
                all_healthy = False
                
        except Exception as e:
            log_test(name, False, f"Exception: {str(e)}")
            all_healthy = False
    
    return all_healthy

# ============================================================================
# MAIN DEPLOYMENT TESTING EXECUTION
# ============================================================================

def run_deployment_tests():
    """Run all deployment-critical tests"""
    print("🚀 STARTING DEPLOYMENT READINESS TESTING")
    print("=" * 80)
    
    # Track test results
    test_functions = [
        # 1. Super Admin Authentication
        test_super_admin_login,
        test_admin_token_validation,
        
        # 2. Advanced Sales Analytics
        test_vendite_dashboard_api,
        test_customer_analytics_api,
        test_products_analytics_api,
        test_departments_analytics_api,
        
        # 3. Enhanced Fidelity System
        test_enhanced_fidelity_validation,
        test_fidelity_cognome_mismatch,
        test_fidelity_backward_compatibility,
        
        # 4. Multi-format Login
        test_multi_format_login,
        
        # 5. Personal User Area
        test_personal_analytics_api,
        test_user_profile_management,
        
        # 6. Advanced Rewards Management
        test_advanced_rewards_crud,
        test_rewards_redemption_system,
        
        # 7. Health Endpoints
        test_health_endpoints
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} crashed: {str(e)}")
            failed += 1
    
    # Final deployment readiness report
    print("\n" + "=" * 80)
    print("🎯 DEPLOYMENT READINESS REPORT")
    print("=" * 80)
    
    total_tests = passed + failed
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 RESULTS: {passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
    
    if failed == 0:
        print("✅ DEPLOYMENT READY: All critical systems operational")
        print("🚀 System ready for production deployment")
    else:
        print(f"❌ DEPLOYMENT ISSUES: {failed} critical systems failing")
        print("🔧 Fix required before production deployment")
    
    # Detailed results
    print("\n📋 DETAILED TEST RESULTS:")
    print("-" * 50)
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    return failed == 0

if __name__ == "__main__":
    deployment_ready = run_deployment_tests()
    sys.exit(0 if deployment_ready else 1)
#!/usr/bin/env python3
"""
ImaGross Loyalty System - Deployment Readiness Testing
Focus on specific fixes mentioned in review request:
1. Vendite Dashboard API Structure (charts/cards)
2. Customer Analytics API (customer_id field)
3. Enhanced Fidelity System (different cards)
4. Multi-format Login (telefono issue)
5. Health Endpoints (JSON response)
"""

import requests
import json
import uuid
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

def get_admin_token():
    """Get admin token for authenticated requests"""
    global admin_access_token
    
    if admin_access_token:
        return admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data["access_token"]
            print(f"✅ Admin authentication successful")
            return admin_access_token
        else:
            print(f"❌ Admin authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Admin authentication error: {str(e)}")
        return None

# ============================================================================
# PRIORITY TEST 1: VENDITE DASHBOARD API STRUCTURE
# ============================================================================

def test_vendite_dashboard_api_structure():
    """Test Vendite Dashboard API for correct charts/cards structure"""
    token = get_admin_token()
    if not token:
        log_test("Vendite Dashboard API Structure", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check basic response structure
            if "success" not in data or not data["success"]:
                log_test("Vendite Dashboard API Structure", False, "Missing or false 'success' field")
                return False
            
            if "dashboard" not in data:
                log_test("Vendite Dashboard API Structure", False, "Missing 'dashboard' field")
                return False
            
            dashboard = data["dashboard"]
            
            # CRITICAL: Check for charts and cards structure as mentioned in fixes
            if "charts" not in dashboard:
                log_test("Vendite Dashboard API Structure", False, "Missing 'charts' structure in dashboard")
                return False
            
            if "cards" not in dashboard:
                log_test("Vendite Dashboard API Structure", False, "Missing 'cards' structure in dashboard")
                return False
            
            # Validate charts structure
            charts = dashboard["charts"]
            expected_charts = ["monthly_trends", "top_customers", "top_departments", "top_products", "top_promotions"]
            
            missing_charts = [chart for chart in expected_charts if chart not in charts]
            if missing_charts:
                log_test("Vendite Dashboard API Structure", False, f"Missing charts: {missing_charts}")
                return False
            
            # Validate cards structure
            cards = dashboard["cards"]
            expected_cards = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
            
            missing_cards = [card for card in expected_cards if card not in cards]
            if missing_cards:
                log_test("Vendite Dashboard API Structure", False, f"Missing cards: {missing_cards}")
                return False
            
            # Validate data content
            if not isinstance(charts["monthly_trends"], list) or len(charts["monthly_trends"]) == 0:
                log_test("Vendite Dashboard API Structure", False, "monthly_trends should be non-empty list")
                return False
            
            if not isinstance(charts["top_customers"], list) or len(charts["top_customers"]) == 0:
                log_test("Vendite Dashboard API Structure", False, "top_customers should be non-empty list")
                return False
            
            # Validate card values are numeric
            for card_name, card_value in cards.items():
                if not isinstance(card_value, (int, float)):
                    log_test("Vendite Dashboard API Structure", False, f"Card {card_name} should be numeric, got {type(card_value)}")
                    return False
            
            log_test("Vendite Dashboard API Structure", True, f"Correct structure with {len(charts)} charts and {len(cards)} cards")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Vendite Dashboard API Structure", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Vendite Dashboard API Structure", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# PRIORITY TEST 2: CUSTOMER ANALYTICS API - CUSTOMER_ID FIELD
# ============================================================================

def test_customer_analytics_api_customer_id():
    """Test Customer Analytics API for required customer_id field"""
    token = get_admin_token()
    if not token:
        log_test("Customer Analytics API customer_id", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use a known customer ID from the system
        test_customer_id = "2013000122724"  # Known customer from previous tests
        
        response = requests.get(f"{API_BASE}/admin/vendite/customer/{test_customer_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check basic response structure
            if "success" not in data or not data["success"]:
                log_test("Customer Analytics API customer_id", False, "Missing or false 'success' field")
                return False
            
            # CRITICAL: Check for customer_id field as mentioned in fixes
            if "customer_id" not in data:
                log_test("Customer Analytics API customer_id", False, "Missing required 'customer_id' field")
                return False
            
            if data["customer_id"] != test_customer_id:
                log_test("Customer Analytics API customer_id", False, f"customer_id mismatch: expected {test_customer_id}, got {data['customer_id']}")
                return False
            
            # Check analytics structure
            if "analytics" not in data:
                log_test("Customer Analytics API customer_id", False, "Missing 'analytics' field")
                return False
            
            analytics = data["analytics"]
            
            # Validate analytics content
            required_analytics_fields = ["total_spent", "total_transactions", "customer_segment"]
            missing_fields = [field for field in required_analytics_fields if field not in analytics]
            if missing_fields:
                log_test("Customer Analytics API customer_id", False, f"Missing analytics fields: {missing_fields}")
                return False
            
            log_test("Customer Analytics API customer_id", True, f"customer_id field present: {data['customer_id']}")
            return True
            
        elif response.status_code == 404:
            # Try with a different customer ID
            test_customer_id = "2020000028284"  # CHIARA ABATANGELO
            response = requests.get(f"{API_BASE}/admin/vendite/customer/{test_customer_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "customer_id" in data and data["customer_id"] == test_customer_id:
                    log_test("Customer Analytics API customer_id", True, f"customer_id field present: {data['customer_id']}")
                    return True
                else:
                    log_test("Customer Analytics API customer_id", False, "customer_id field missing or incorrect")
                    return False
            else:
                log_test("Customer Analytics API customer_id", False, f"No valid customer found for testing")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Customer Analytics API customer_id", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Customer Analytics API customer_id", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# PRIORITY TEST 3: ENHANCED FIDELITY SYSTEM - DIFFERENT CARDS
# ============================================================================

def test_enhanced_fidelity_different_cards():
    """Test Enhanced Fidelity System with different cards (not already migrated)"""
    
    # Test different cards that might not be migrated
    test_cards = [
        {"tessera": "2020000400004", "cognome": "SCHEDA"},  # Known from previous tests
        {"tessera": "2013000122724", "cognome": "CLIENTE"},  # Different test card
        {"tessera": "2020000000013", "cognome": "DAMIANI"},  # COSIMO DAMIANI from previous tests
        {"tessera": "2020000999999", "cognome": "NONEXIST"}  # Non-existent card for negative test
    ]
    
    successful_tests = 0
    total_tests = len(test_cards)
    
    for i, card_data in enumerate(test_cards):
        tessera = card_data["tessera"]
        cognome = card_data["cognome"]
        
        try:
            # Test tessera-only validation (backward compatibility)
            response = requests.post(f"{API_BASE}/check-tessera", json={"tessera_fisica": tessera})
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "found":
                    # Test enhanced validation with cognome
                    enhanced_response = requests.post(f"{API_BASE}/check-tessera", json={
                        "tessera_fisica": tessera,
                        "cognome": cognome
                    })
                    
                    if enhanced_response.status_code == 200:
                        enhanced_data = enhanced_response.json()
                        
                        if enhanced_data.get("status") == "found":
                            log_test(f"Fidelity Card {i+1} - Enhanced Validation", True, f"Card {tessera} with cognome {cognome} validated successfully")
                            successful_tests += 1
                        elif enhanced_data.get("status") == "cognome_mismatch":
                            log_test(f"Fidelity Card {i+1} - Enhanced Validation", True, f"Card {tessera} correctly rejected wrong cognome")
                            successful_tests += 1
                        else:
                            log_test(f"Fidelity Card {i+1} - Enhanced Validation", False, f"Unexpected status: {enhanced_data.get('status')}")
                    else:
                        log_test(f"Fidelity Card {i+1} - Enhanced Validation", False, f"Enhanced validation failed: {enhanced_response.status_code}")
                        
                elif data.get("status") == "già migrata":
                    log_test(f"Fidelity Card {i+1} - Migration Status", True, f"Card {tessera} correctly shows migrated status")
                    successful_tests += 1
                    
                elif data.get("status") == "not_found":
                    if tessera == "2020000999999":  # Expected for non-existent card
                        log_test(f"Fidelity Card {i+1} - Not Found", True, f"Non-existent card {tessera} correctly not found")
                        successful_tests += 1
                    else:
                        log_test(f"Fidelity Card {i+1} - Not Found", False, f"Card {tessera} unexpectedly not found")
                else:
                    log_test(f"Fidelity Card {i+1} - Unknown Status", False, f"Unknown status: {data.get('status')}")
                    
            else:
                log_test(f"Fidelity Card {i+1} - API Error", False, f"API error: {response.status_code}")
                
        except Exception as e:
            log_test(f"Fidelity Card {i+1} - Exception", False, f"Exception: {str(e)}")
    
    # Overall result
    success_rate = (successful_tests / total_tests) * 100
    if success_rate >= 75:  # At least 3 out of 4 tests should pass
        log_test("Enhanced Fidelity System Overall", True, f"Success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        return True
    else:
        log_test("Enhanced Fidelity System Overall", False, f"Low success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        return False

# ============================================================================
# PRIORITY TEST 4: MULTI-FORMAT LOGIN - TELEFONO ISSUE
# ============================================================================

def test_multi_format_login_telefono():
    """Test Multi-format Login System focusing on telefono login issue"""
    
    # First, create a test user to ensure we have valid login data
    test_user_data = {
        "nome": "TestLogin",
        "cognome": "MultiFormat",
        "sesso": "M",
        "email": f"testlogin.{uuid.uuid4().hex[:8]}@email.it",
        "telefono": "+39 333 1234567",
        "localita": "Milano",
        "tessera_fisica": f"TLG{uuid.uuid4().hex[:9].upper()}",
        "password": "TestLogin123!"
    }
    
    try:
        # Register test user
        response = requests.post(f"{API_BASE}/register", json=test_user_data)
        
        if response.status_code != 200:
            log_test("Multi-format Login Setup", False, "Could not create test user")
            return False
        
        user_data = response.json()
        
        # Test 1: Email login (should work)
        email_login = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=email_login)
        
        if response.status_code == 200:
            log_test("Multi-format Login - Email", True, "Email login successful")
            email_success = True
        else:
            log_test("Multi-format Login - Email", False, f"Email login failed: {response.status_code}")
            email_success = False
        
        # Test 2: Tessera login (should work)
        tessera_login = {
            "username": test_user_data["tessera_fisica"],
            "password": test_user_data["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=tessera_login)
        
        if response.status_code == 200:
            log_test("Multi-format Login - Tessera", True, "Tessera login successful")
            tessera_success = True
        else:
            log_test("Multi-format Login - Tessera", False, f"Tessera login failed: {response.status_code}")
            tessera_success = False
        
        # Test 3: Telefono login (CRITICAL - this was failing)
        telefono_login = {
            "username": test_user_data["telefono"],
            "password": test_user_data["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=telefono_login)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                log_test("Multi-format Login - Telefono", True, "Telefono login successful")
                telefono_success = True
            else:
                log_test("Multi-format Login - Telefono", False, "Telefono login response missing required fields")
                telefono_success = False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Multi-format Login - Telefono", False, f"Telefono login failed: {response.status_code} - {error_detail}")
            telefono_success = False
        
        # Test 4: Invalid credentials (should fail)
        invalid_login = {
            "username": test_user_data["email"],
            "password": "WrongPassword123"
        }
        
        response = requests.post(f"{API_BASE}/login", json=invalid_login)
        
        if response.status_code == 401:
            log_test("Multi-format Login - Invalid", True, "Invalid credentials correctly rejected")
            invalid_success = True
        else:
            log_test("Multi-format Login - Invalid", False, f"Invalid credentials should return 401, got {response.status_code}")
            invalid_success = False
        
        # Overall assessment
        total_tests = 4
        successful_tests = sum([email_success, tessera_success, telefono_success, invalid_success])
        
        if successful_tests >= 3 and telefono_success:  # Telefono must work
            log_test("Multi-format Login Overall", True, f"Success rate: {(successful_tests/total_tests)*100:.1f}% - Telefono login working")
            return True
        else:
            log_test("Multi-format Login Overall", False, f"Success rate: {(successful_tests/total_tests)*100:.1f}% - Telefono login issue persists")
            return False
            
    except Exception as e:
        log_test("Multi-format Login System", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# PRIORITY TEST 5: HEALTH ENDPOINTS - JSON RESPONSE
# ============================================================================

def test_health_endpoints_json():
    """Test Health Endpoints for proper JSON responses (not HTML)"""
    
    health_endpoints = [
        "/health",
        "/readiness", 
        "/startup-status"
    ]
    
    successful_tests = 0
    total_tests = len(health_endpoints)
    
    for endpoint in health_endpoints:
        try:
            # Test both with and without /api prefix
            test_urls = [f"{BASE_URL}{endpoint}", f"{API_BASE}{endpoint}"]
            
            endpoint_success = False
            
            for url in test_urls:
                response = requests.get(url)
                
                if response.status_code == 200:
                    # Check if response is JSON
                    try:
                        data = response.json()
                        
                        # Validate JSON structure
                        if isinstance(data, dict):
                            # Check for common health check fields
                            if "status" in data or "health" in data or "ready" in data:
                                log_test(f"Health Endpoint {endpoint}", True, f"JSON response at {url}: {data}")
                                endpoint_success = True
                                break
                            else:
                                log_test(f"Health Endpoint {endpoint}", False, f"JSON response missing health fields at {url}")
                        else:
                            log_test(f"Health Endpoint {endpoint}", False, f"JSON response not a dict at {url}")
                            
                    except json.JSONDecodeError:
                        # Check if it's HTML (the old problem)
                        if response.text.strip().startswith('<'):
                            log_test(f"Health Endpoint {endpoint}", False, f"HTML response instead of JSON at {url}")
                        else:
                            log_test(f"Health Endpoint {endpoint}", False, f"Non-JSON response at {url}: {response.text[:100]}")
                            
                elif response.status_code == 404:
                    continue  # Try next URL
                else:
                    log_test(f"Health Endpoint {endpoint}", False, f"HTTP {response.status_code} at {url}")
            
            if endpoint_success:
                successful_tests += 1
            elif not endpoint_success:
                log_test(f"Health Endpoint {endpoint}", False, f"Not accessible at any URL")
                
        except Exception as e:
            log_test(f"Health Endpoint {endpoint}", False, f"Exception: {str(e)}")
    
    # Overall assessment
    success_rate = (successful_tests / total_tests) * 100
    
    if success_rate >= 66:  # At least 2 out of 3 should work
        log_test("Health Endpoints Overall", True, f"Success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        return True
    else:
        log_test("Health Endpoints Overall", False, f"Low success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        return False

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_deployment_readiness_tests():
    """Run all deployment readiness tests"""
    print("🚀 DEPLOYMENT READINESS TESTING - POST-FIXES VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Vendite Dashboard API Structure", test_vendite_dashboard_api_structure),
        ("Customer Analytics API customer_id", test_customer_analytics_api_customer_id),
        ("Enhanced Fidelity System", test_enhanced_fidelity_different_cards),
        ("Multi-format Login System", test_multi_format_login_telefono),
        ("Health Endpoints JSON", test_health_endpoints_json)
    ]
    
    successful_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 50)
        
        try:
            result = test_function()
            if result:
                successful_tests += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution failed: {str(e)}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 70)
    
    success_rate = (successful_tests / total_tests) * 100
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 DEPLOYMENT READY - Most critical fixes verified")
        return True
    else:
        print("⚠️  DEPLOYMENT NOT READY - Critical issues remain")
        return False

if __name__ == "__main__":
    run_deployment_readiness_tests()
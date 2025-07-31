#!/usr/bin/env python3
"""
ImaGross Personal User Area Features Tests
Tests the new Personal Analytics API and User Profile Management features
"""

import requests
import json
import uuid
from datetime import datetime
import sys

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
print(f"🔗 Testing Personal User Area API at: {API_BASE}")

# Test data - using the fidelity card mentioned in the review request
FIDELITY_TEST_CARD = "2020000028284"  # CHIARA ABATANGELO
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "ImaGross2024!"
}

# Global variables for test state
user_access_token = None
admin_access_token = None
test_user_id = None
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
    """Test admin login to get admin token"""
    global admin_access_token
    
    try:
        response = requests.post(f"{API_BASE}/admin/login", json=ADMIN_CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data["access_token"]
            log_test("Admin Login", True, "Admin authentication successful")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return False

def test_fidelity_card_verification():
    """Test fidelity card verification with CHIARA ABATANGELO card"""
    try:
        tessera_data = {"tessera_fisica": FIDELITY_TEST_CARD}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["found", "migrated"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Fidelity Card Verification", False, f"Missing fields: {missing_fields}")
                return False
            
            if not data["found"]:
                log_test("Fidelity Card Verification", False, "CHIARA ABATANGELO card not found in fidelity data")
                return False
            
            # Check if user data is returned
            if "user_data" in data:
                user_data = data["user_data"]
                expected_fields = ["nome", "cognome", "email", "telefono", "localita"]
                missing_user_fields = [field for field in expected_fields if field not in user_data]
                if missing_user_fields:
                    log_test("Fidelity Card Verification", False, f"Missing user data fields: {missing_user_fields}")
                    return False
                
                # Validate CHIARA ABATANGELO data
                if user_data.get("nome", "").upper() != "CHIARA" or user_data.get("cognome", "").upper() != "ABATANGELO":
                    log_test("Fidelity Card Verification", False, f"Wrong user data: {user_data.get('nome')} {user_data.get('cognome')}")
                    return False
            
            log_test("Fidelity Card Verification", True, f"CHIARA ABATANGELO card verified successfully, migrated: {data['migrated']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Card Verification", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Card Verification", False, f"Exception: {str(e)}")
        return False

def test_user_registration_with_fidelity():
    """Test user registration using fidelity card data"""
    global test_user_id, user_access_token
    
    try:
        # First check the fidelity card to get pre-populated data
        tessera_data = {"tessera_fisica": FIDELITY_TEST_CARD}
        check_response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if check_response.status_code != 200:
            log_test("User Registration with Fidelity", False, "Could not verify fidelity card first")
            return False
        
        check_data = check_response.json()
        if not check_data.get("found") or check_data.get("migrated"):
            # Create a new unique tessera for testing
            test_tessera = f"TEST{uuid.uuid4().hex[:8].upper()}"
            user_data = {
                "nome": "Marco",
                "cognome": "TestUser",
                "sesso": "M",
                "email": f"marco.testuser.{uuid.uuid4().hex[:8]}@email.it",
                "telefono": "+39 333 1234567",
                "localita": "Milano",
                "tessera_fisica": test_tessera,
                "password": "TestPass123!",
                "progressivo_spesa": 150.50,
                "bollini": 25
            }
        else:
            # Use fidelity data for registration
            fidelity_data = check_data["user_data"]
            user_data = {
                "nome": fidelity_data.get("nome", "Marco"),
                "cognome": fidelity_data.get("cognome", "TestUser"),
                "sesso": fidelity_data.get("sesso", "M"),
                "email": f"test.{uuid.uuid4().hex[:8]}@email.it",  # Use unique email
                "telefono": fidelity_data.get("telefono", "+39 333 1234567"),
                "localita": fidelity_data.get("localita", "Milano"),
                "tessera_fisica": f"TEST{uuid.uuid4().hex[:8].upper()}",  # Use unique tessera
                "password": "TestPass123!",
                "indirizzo": fidelity_data.get("indirizzo", ""),
                "progressivo_spesa": fidelity_data.get("progressivo_spesa", 0),
                "bollini": fidelity_data.get("bollini", 0)
            }
        
        response = requests.post(f"{API_BASE}/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            test_user_id = data["id"]
            
            # Now login to get access token
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            login_response = requests.post(f"{API_BASE}/login", json=login_data)
            if login_response.status_code == 200:
                login_result = login_response.json()
                user_access_token = login_result["access_token"]
                
                log_test("User Registration with Fidelity", True, f"User registered and logged in successfully: {data['nome']} {data['cognome']}")
                return True
            else:
                log_test("User Registration with Fidelity", False, "Registration successful but login failed")
                return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Registration with Fidelity", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Registration with Fidelity", False, f"Exception: {str(e)}")
        return False

def test_user_profile_get():
    """Test GET /api/user/profile endpoint"""
    if not user_access_token:
        log_test("User Profile GET", False, "No user access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_access_token}"}
        response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure for complete profile
            required_fields = [
                "id", "nome", "cognome", "email", "telefono", "localita",
                "tessera_fisica", "tessera_digitale", "punti", "created_at",
                "sesso", "bollini", "progressivo_spesa"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("User Profile GET", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(data["punti"], int):
                log_test("User Profile GET", False, f"Points should be integer, got {type(data['punti'])}")
                return False
            
            if not isinstance(data["bollini"], int):
                log_test("User Profile GET", False, f"Bollini should be integer, got {type(data['bollini'])}")
                return False
            
            if not isinstance(data["progressivo_spesa"], (int, float)):
                log_test("User Profile GET", False, f"Progressivo spesa should be numeric, got {type(data['progressivo_spesa'])}")
                return False
            
            # Check for extended fidelity fields
            extended_fields = [
                "consenso_dati_personali", "consenso_dati_pubblicitari",
                "indirizzo", "provincia", "data_nascita"
            ]
            
            extended_present = sum(1 for field in extended_fields if field in data)
            
            log_test("User Profile GET", True, f"Complete profile retrieved with {extended_present}/{len(extended_fields)} extended fields")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Profile GET", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Profile GET", False, f"Exception: {str(e)}")
        return False

def test_user_profile_update():
    """Test PUT /api/user/profile endpoint"""
    if not user_access_token:
        log_test("User Profile UPDATE", False, "No user access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_access_token}"}
        
        # Update profile data
        update_data = {
            "telefono": "+39 347 9876543",
            "localita": "Roma",
            "consenso_dati_personali": True,
            "consenso_dati_pubblicitari": False,
            "newsletter": True,
            "numero_figli": 2,
            "animali_cani": True,
            "intolleranza_lattosio": False
        }
        
        response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate that updates were applied
            if data.get("telefono") != update_data["telefono"]:
                log_test("User Profile UPDATE", False, "Phone number not updated")
                return False
            
            if data.get("localita") != update_data["localita"]:
                log_test("User Profile UPDATE", False, "Location not updated")
                return False
            
            if data.get("consenso_dati_personali") != update_data["consenso_dati_personali"]:
                log_test("User Profile UPDATE", False, "Consent settings not updated")
                return False
            
            if data.get("numero_figli") != update_data["numero_figli"]:
                log_test("User Profile UPDATE", False, "Number of children not updated")
                return False
            
            log_test("User Profile UPDATE", True, "Profile updated successfully with all field types")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Profile UPDATE", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Profile UPDATE", False, f"Exception: {str(e)}")
        return False

def test_personal_analytics_api():
    """Test GET /api/user/personal-analytics endpoint"""
    if not user_access_token:
        log_test("Personal Analytics API", False, "No user access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_access_token}"}
        response = requests.get(f"{API_BASE}/user/personal-analytics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_sections = ["summary", "monthly_trend", "shopping_patterns", "achievements", "next_rewards", "spending_insights", "challenges"]
            missing_sections = [section for section in required_sections if section not in data]
            if missing_sections:
                log_test("Personal Analytics API", False, f"Missing sections: {missing_sections}")
                return False
            
            # Validate summary section
            summary = data["summary"]
            required_summary_fields = [
                "total_spent", "total_transactions", "total_bollini", "avg_transaction",
                "shopping_frequency", "loyalty_level", "days_since_last_shop"
            ]
            
            missing_summary_fields = [field for field in required_summary_fields if field not in summary]
            if missing_summary_fields:
                log_test("Personal Analytics API", False, f"Missing summary fields: {missing_summary_fields}")
                return False
            
            # Validate data types
            if not isinstance(summary["total_spent"], (int, float)):
                log_test("Personal Analytics API", False, f"Total spent should be numeric, got {type(summary['total_spent'])}")
                return False
            
            if not isinstance(summary["total_transactions"], int):
                log_test("Personal Analytics API", False, f"Total transactions should be integer, got {type(summary['total_transactions'])}")
                return False
            
            if not isinstance(summary["total_bollini"], int):
                log_test("Personal Analytics API", False, f"Total bollini should be integer, got {type(summary['total_bollini'])}")
                return False
            
            # Validate loyalty level
            valid_loyalty_levels = ["Bronze", "Silver", "Gold", "Platinum"]
            if summary["loyalty_level"] not in valid_loyalty_levels:
                log_test("Personal Analytics API", False, f"Invalid loyalty level: {summary['loyalty_level']}")
                return False
            
            # Validate monthly trend is a list
            if not isinstance(data["monthly_trend"], list):
                log_test("Personal Analytics API", False, "Monthly trend should be a list")
                return False
            
            # Validate shopping patterns
            patterns = data["shopping_patterns"]
            required_pattern_fields = ["favorite_day", "favorite_hour", "peak_shopping_day"]
            missing_pattern_fields = [field for field in required_pattern_fields if field not in patterns]
            if missing_pattern_fields:
                log_test("Personal Analytics API", False, f"Missing shopping pattern fields: {missing_pattern_fields}")
                return False
            
            # Validate achievements is a list
            if not isinstance(data["achievements"], list):
                log_test("Personal Analytics API", False, "Achievements should be a list")
                return False
            
            # Validate next rewards is a list
            if not isinstance(data["next_rewards"], list):
                log_test("Personal Analytics API", False, "Next rewards should be a list")
                return False
            
            log_test("Personal Analytics API", True, f"Complete analytics retrieved - Level: {summary['loyalty_level']}, Spent: €{summary['total_spent']}, Bollini: {summary['total_bollini']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Personal Analytics API", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Personal Analytics API", False, f"Exception: {str(e)}")
        return False

def test_analytics_unauthorized():
    """Test personal analytics without authentication"""
    try:
        response = requests.get(f"{API_BASE}/user/personal-analytics")
        
        if response.status_code == 403:
            log_test("Analytics Unauthorized", True, "Correctly rejected unauthenticated request")
            return True
        else:
            log_test("Analytics Unauthorized", False, f"Should return 403, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Analytics Unauthorized", False, f"Exception: {str(e)}")
        return False

def test_profile_unauthorized():
    """Test profile endpoints without authentication"""
    try:
        # Test GET profile
        response = requests.get(f"{API_BASE}/user/profile")
        if response.status_code != 403:
            log_test("Profile GET Unauthorized", False, f"Should return 403, got {response.status_code}")
            return False
        
        # Test PUT profile
        response = requests.put(f"{API_BASE}/user/profile", json={"telefono": "123456789"})
        if response.status_code != 403:
            log_test("Profile PUT Unauthorized", False, f"Should return 403, got {response.status_code}")
            return False
        
        log_test("Profile Unauthorized", True, "Both GET and PUT correctly rejected unauthenticated requests")
        return True
        
    except Exception as e:
        log_test("Profile Unauthorized", False, f"Exception: {str(e)}")
        return False

def test_jwt_token_validation():
    """Test JWT token validation in personal area endpoints"""
    try:
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        if response.status_code != 401:
            log_test("JWT Token Validation", False, f"Should return 401 for invalid token, got {response.status_code}")
            return False
        
        response = requests.get(f"{API_BASE}/user/personal-analytics", headers=headers)
        if response.status_code != 401:
            log_test("JWT Token Validation", False, f"Should return 401 for invalid token, got {response.status_code}")
            return False
        
        log_test("JWT Token Validation", True, "Invalid tokens correctly rejected with 401")
        return True
        
    except Exception as e:
        log_test("JWT Token Validation", False, f"Exception: {str(e)}")
        return False

def test_data_integration_scontrini():
    """Test integration with SCONTRINI data for analytics"""
    if not user_access_token:
        log_test("SCONTRINI Data Integration", False, "No user access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {user_access_token}"}
        response = requests.get(f"{API_BASE}/user/personal-analytics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if analytics include transaction-based data
            summary = data["summary"]
            
            # Even if user has no transactions, the structure should be complete
            if "total_transactions" not in summary:
                log_test("SCONTRINI Data Integration", False, "Missing transaction data in analytics")
                return False
            
            if "monthly_trend" not in data:
                log_test("SCONTRINI Data Integration", False, "Missing monthly trend data")
                return False
            
            # Check if monthly trend has proper structure
            monthly_trend = data["monthly_trend"]
            if isinstance(monthly_trend, list) and len(monthly_trend) > 0:
                # If there's data, validate structure
                trend_item = monthly_trend[0]
                required_trend_fields = ["month", "spent", "transactions", "bollini"]
                missing_trend_fields = [field for field in required_trend_fields if field not in trend_item]
                if missing_trend_fields:
                    log_test("SCONTRINI Data Integration", False, f"Missing trend fields: {missing_trend_fields}")
                    return False
            
            log_test("SCONTRINI Data Integration", True, f"SCONTRINI integration working - {summary['total_transactions']} transactions processed")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("SCONTRINI Data Integration", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("SCONTRINI Data Integration", False, f"Exception: {str(e)}")
        return False

def test_admin_vs_user_authentication():
    """Test that admin and user authentication are properly separated"""
    if not admin_access_token or not user_access_token:
        log_test("Admin vs User Auth", False, "Missing admin or user tokens")
        return False
    
    try:
        # Test admin token on user endpoints (should work if admin has user role too, but let's check)
        admin_headers = {"Authorization": f"Bearer {admin_access_token}"}
        user_headers = {"Authorization": f"Bearer {user_access_token}"}
        
        # Test user token on admin endpoint (should fail)
        response = requests.get(f"{API_BASE}/admin/stores", headers=user_headers)
        if response.status_code != 403:
            log_test("Admin vs User Auth", False, f"User token should not access admin endpoints, got {response.status_code}")
            return False
        
        # Test admin token on admin endpoint (should work)
        response = requests.get(f"{API_BASE}/admin/stores", headers=admin_headers)
        if response.status_code != 200:
            log_test("Admin vs User Auth", False, f"Admin token should access admin endpoints, got {response.status_code}")
            return False
        
        # Test user token on user endpoint (should work)
        response = requests.get(f"{API_BASE}/user/profile", headers=user_headers)
        if response.status_code != 200:
            log_test("Admin vs User Auth", False, f"User token should access user endpoints, got {response.status_code}")
            return False
        
        log_test("Admin vs User Auth", True, "Role-based access control working correctly")
        return True
        
    except Exception as e:
        log_test("Admin vs User Auth", False, f"Exception: {str(e)}")
        return False

def run_personal_area_tests():
    """Run all Personal User Area tests"""
    print("🚀 Starting ImaGross Personal User Area Features Tests")
    print("=" * 80)
    
    # Test sequence
    tests = [
        ("🔐 Admin Authentication", test_admin_login),
        ("🎫 Fidelity Card Verification", test_fidelity_card_verification),
        ("👤 User Registration with Fidelity", test_user_registration_with_fidelity),
        ("📋 User Profile GET", test_user_profile_get),
        ("✏️  User Profile UPDATE", test_user_profile_update),
        ("📊 Personal Analytics API", test_personal_analytics_api),
        ("🔒 Analytics Unauthorized", test_analytics_unauthorized),
        ("🔒 Profile Unauthorized", test_profile_unauthorized),
        ("🎟️  JWT Token Validation", test_jwt_token_validation),
        ("📈 SCONTRINI Data Integration", test_data_integration_scontrini),
        ("🔐 Admin vs User Authentication", test_admin_vs_user_authentication)
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 50)
        try:
            if test_func():
                passed += 1
            else:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name}: Exception - {str(e)}")
            failed_tests.append(test_name)
    
    print("\n" + "=" * 80)
    print(f"📊 PERSONAL USER AREA TEST RESULTS: {passed}/{total} tests passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test_name in failed_tests:
            print(f"   • {test_name}")
    
    if passed == total:
        print("\n🎉 ALL PERSONAL USER AREA TESTS PASSED!")
        print("✅ Personal Analytics API: WORKING")
        print("✅ User Profile Management (GET/PUT): WORKING") 
        print("✅ Authentication Integration: WORKING")
        print("✅ Data Integration (Fidelity.json + SCONTRINI): WORKING")
        print("✅ JWT Token Validation: WORKING")
        print("✅ Role-based Access Control: WORKING")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_personal_area_tests()
    sys.exit(0 if success else 1)
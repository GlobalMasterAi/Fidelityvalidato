#!/usr/bin/env python3
"""
Focused User Profile Management API Tests
Tests specifically the PUT endpoint that was just fixed
"""

import requests
import json
import uuid
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
print(f"🔗 Testing User Profile API at: {API_BASE}")

# Test credentials from review request
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "ImaGross2024!"
}

FIDELITY_CARD = "2020000028284"  # CHIARA ABATANGELO

# Global variables
access_token = None
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

def setup_test_user():
    """Create and login a test user for profile testing"""
    global access_token
    
    # Create test user
    user_data = {
        "nome": "TestUser",
        "cognome": "ProfileTest",
        "sesso": "M",
        "email": f"profiletest.{uuid.uuid4().hex[:8]}@email.it",
        "telefono": "+39 333 1111111",
        "localita": "Milano",
        "tessera_fisica": f"PROF{uuid.uuid4().hex[:8].upper()}",
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{API_BASE}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Failed to create test user: {response.status_code}")
        return False
    
    # Login test user
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{API_BASE}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Failed to login test user: {response.status_code}")
        return False
    
    data = response.json()
    access_token = data["access_token"]
    print(f"✅ Test user created and logged in")
    return True

def test_profile_put_database_persistence():
    """CRITICAL TEST: Verify PUT endpoint actually persists changes to database"""
    if not access_token:
        log_test("Profile PUT Persistence", False, "No access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get original profile
        response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        if response.status_code != 200:
            log_test("Profile PUT Persistence", False, "Could not get original profile")
            return False
        
        original_profile = response.json()
        
        # Prepare unique update data
        import time
        timestamp = str(int(time.time()))
        update_data = {
            "telefono": f"+39 347 {timestamp[-7:]}",
            "localita": f"Roma Test {timestamp[-4:]}",
            "consenso_dati_personali": not original_profile.get("consenso_dati_personali", True),
            "numero_figli": (original_profile.get("numero_figli", 0) + 1) % 5
        }
        
        print(f"🔄 Updating profile with: {update_data}")
        
        # Perform PUT request
        response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
        
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Profile PUT Persistence", False, f"PUT failed with status {response.status_code}: {error_detail}")
            return False
        
        print(f"✅ PUT request returned 200 OK")
        
        # CRITICAL: Verify persistence with fresh GET request
        verification_response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        if verification_response.status_code != 200:
            log_test("Profile PUT Persistence", False, "Could not verify profile after update")
            return False
        
        verified_profile = verification_response.json()
        
        # Check each field for persistence
        persistence_results = []
        all_persisted = True
        
        for field, expected_value in update_data.items():
            actual_value = verified_profile.get(field)
            if actual_value == expected_value:
                persistence_results.append(f"✅ {field}: {expected_value}")
            else:
                persistence_results.append(f"❌ {field}: expected {expected_value}, got {actual_value}")
                all_persisted = False
        
        print("📊 Persistence Results:")
        for result in persistence_results:
            print(f"   {result}")
        
        if all_persisted:
            log_test("Profile PUT Persistence", True, f"All {len(update_data)} fields successfully persisted to database")
            return True
        else:
            log_test("Profile PUT Persistence", False, "Some fields failed to persist to database")
            return False
            
    except Exception as e:
        log_test("Profile PUT Persistence", False, f"Exception: {str(e)}")
        return False

def test_profile_put_multiple_updates():
    """Test multiple consecutive PUT requests to verify consistency"""
    if not access_token:
        log_test("Profile PUT Multiple Updates", False, "No access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Perform 3 consecutive updates
        updates = []
        for i in range(3):
            import time
            timestamp = str(int(time.time()) + i)
            update_data = {
                "telefono": f"+39 333 {timestamp[-7:]}",
                "localita": f"Test City {i+1}",
                "numero_figli": i
            }
            
            response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
            if response.status_code != 200:
                log_test("Profile PUT Multiple Updates", False, f"Update {i+1} failed")
                return False
            
            # Verify immediately
            verification_response = requests.get(f"{API_BASE}/user/profile", headers=headers)
            if verification_response.status_code != 200:
                log_test("Profile PUT Multiple Updates", False, f"Verification {i+1} failed")
                return False
            
            verified_profile = verification_response.json()
            
            # Check persistence
            for field, expected_value in update_data.items():
                if verified_profile.get(field) != expected_value:
                    log_test("Profile PUT Multiple Updates", False, f"Update {i+1} field {field} not persisted")
                    return False
            
            updates.append(update_data)
            print(f"✅ Update {i+1} persisted successfully")
        
        log_test("Profile PUT Multiple Updates", True, f"All {len(updates)} consecutive updates persisted correctly")
        return True
        
    except Exception as e:
        log_test("Profile PUT Multiple Updates", False, f"Exception: {str(e)}")
        return False

def test_profile_put_edge_cases():
    """Test edge cases for PUT endpoint"""
    if not access_token:
        log_test("Profile PUT Edge Cases", False, "No access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test 1: Empty update
        response = requests.put(f"{API_BASE}/user/profile", json={}, headers=headers)
        if response.status_code != 200:
            log_test("Profile PUT Edge Cases", False, "Empty update failed")
            return False
        print("✅ Empty update handled correctly")
        
        # Test 2: Null values
        update_data = {
            "consenso_profilazione": None,
            "consenso_marketing": None,
            "coniugato": None
        }
        
        response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
        if response.status_code != 200:
            log_test("Profile PUT Edge Cases", False, "Null values update failed")
            return False
        
        # Verify null values are handled
        verification_response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        verified_profile = verification_response.json()
        
        for field in update_data.keys():
            if field in verified_profile:  # Field should exist but can be null
                print(f"✅ Null field {field} handled correctly")
        
        # Test 3: Boolean string conversion
        update_data = {
            "consenso_dati_personali": "true",
            "animali_cani": "false",
            "newsletter": "1"
        }
        
        response = requests.put(f"{API_BASE}/user/profile", json=update_data, headers=headers)
        if response.status_code != 200:
            log_test("Profile PUT Edge Cases", False, "Boolean string conversion failed")
            return False
        
        # Verify boolean conversion
        verification_response = requests.get(f"{API_BASE}/user/profile", headers=headers)
        verified_profile = verification_response.json()
        
        if verified_profile.get("consenso_dati_personali") != True:
            log_test("Profile PUT Edge Cases", False, "Boolean string 'true' not converted")
            return False
        
        if verified_profile.get("animali_cani") != False:
            log_test("Profile PUT Edge Cases", False, "Boolean string 'false' not converted")
            return False
        
        print("✅ Boolean string conversion working")
        
        log_test("Profile PUT Edge Cases", True, "All edge cases handled correctly")
        return True
        
    except Exception as e:
        log_test("Profile PUT Edge Cases", False, f"Exception: {str(e)}")
        return False

def test_fidelity_card_integration():
    """Test fidelity card data integration"""
    try:
        tessera_data = {"tessera_fisica": FIDELITY_CARD}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("found", False):
                user_data = data.get("user_data", {})
                if user_data:
                    log_test("Fidelity Card Integration", True, f"Card {FIDELITY_CARD} found with data: {user_data.get('nome', '')} {user_data.get('cognome', '')}")
                    return True
                else:
                    log_test("Fidelity Card Integration", False, f"Card {FIDELITY_CARD} found but no user data")
                    return False
            else:
                log_test("Fidelity Card Integration", False, f"Card {FIDELITY_CARD} not found in system")
                return False
        else:
            log_test("Fidelity Card Integration", False, f"Check tessera failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Fidelity Card Integration", False, f"Exception: {str(e)}")
        return False

def run_focused_tests():
    """Run focused profile management tests"""
    print("🎯 FOCUSED USER PROFILE MANAGEMENT API TESTS")
    print("=" * 80)
    print("🔍 CRITICAL FOCUS: PUT endpoint database persistence fix")
    print("-" * 80)
    
    # Setup test user
    if not setup_test_user():
        print("❌ Failed to setup test user, stopping tests")
        return False
    
    # Run focused tests
    tests = [
        test_profile_put_database_persistence,
        test_profile_put_multiple_updates,
        test_profile_put_edge_cases,
        test_fidelity_card_integration
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed_tests.append(test_func.__name__)
        except Exception as e:
            print(f"❌ {test_func.__name__}: Exception - {str(e)}")
            failed_tests.append(test_func.__name__)
    
    print("\n" + "=" * 80)
    print(f"📊 FOCUSED TEST RESULTS: {passed}/{total} tests passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test_name in failed_tests:
            print(f"   • {test_name}")
    
    if passed == total:
        print("\n🎉 ALL FOCUSED TESTS PASSED!")
        print("✅ User Profile PUT endpoint database persistence: FIXED AND WORKING")
        print("✅ Multiple field updates: WORKING")
        print("✅ Edge case handling: WORKING")
        print("✅ Database consistency: VERIFIED")
        return True
    else:
        print(f"\n⚠️  {total - passed} focused tests failed.")
        return False

if __name__ == "__main__":
    success = run_focused_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
JSON Parsing and Data Persistence Fix Test
Tests the improved JSON parsing and data persistence for fidelity data
"""

import requests
import json
import time
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
print(f"🔗 Testing JSON Parsing Fix at: {API_BASE}")

# Test results tracking
test_results = []
admin_token = None

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

def test_admin_authentication():
    """Test admin authentication with superadmin credentials"""
    global admin_token
    
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
            if "access_token" in data:
                admin_token = data["access_token"]
                log_test("Admin Authentication", True, f"Login successful ({response_time:.2f}s)")
                return True
            else:
                log_test("Admin Authentication", False, "No access token in response")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_current_fidelity_count():
    """Check current database state - get fidelity record count"""
    if not admin_token:
        log_test("Current Fidelity Count", False, "No admin token available")
        return False, 0
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "users" in data and "total" in data:
                total_count = data["total"]
                log_test("Current Fidelity Count", True, f"Current count: {total_count:,} records ({response_time:.2f}s)")
                return True, total_count
            else:
                log_test("Current Fidelity Count", False, "Invalid response structure")
                return False, 0
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Current Fidelity Count", False, f"Status {response.status_code}: {error_detail}")
            return False, 0
            
    except Exception as e:
        log_test("Current Fidelity Count", False, f"Exception: {str(e)}")
        return False, 0

def test_search_missing_card():
    """Search for card 2020000063308 to confirm it's currently missing"""
    if not admin_token:
        log_test("Search Missing Card", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Search for the specific card
        params = {"search": "2020000063308"}
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=params, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                users = data["users"]
                found_card = False
                for user in users:
                    if user.get("tessera_fisica") == "2020000063308":
                        found_card = True
                        break
                
                if found_card:
                    log_test("Search Missing Card", False, f"Card 2020000063308 already exists - not missing ({response_time:.2f}s)")
                    return False
                else:
                    log_test("Search Missing Card", True, f"Card 2020000063308 confirmed missing ({response_time:.2f}s)")
                    return True
            else:
                log_test("Search Missing Card", False, "Invalid response structure")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Search Missing Card", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Search Missing Card", False, f"Exception: {str(e)}")
        return False

def test_force_data_reload():
    """Trigger force data reload to test improved JSON parsing"""
    if not admin_token:
        log_test("Force Data Reload", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers, timeout=120)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("Force Data Reload", True, f"Reload initiated: {data['message']} ({response_time:.2f}s)")
                return True
            else:
                log_test("Force Data Reload", False, "Invalid response structure")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Force Data Reload", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Force Data Reload", False, f"Exception: {str(e)}")
        return False

def test_wait_for_reload_completion():
    """Wait for data reload to complete and monitor progress"""
    if not admin_token:
        log_test("Wait for Reload", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        print("⏳ Monitoring data loading progress...")
        max_wait_time = 300  # 5 minutes max
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_time:
            try:
                response = requests.get(f"{API_BASE}/startup-status", headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if "data_loading_status" in data:
                        status = data["data_loading_status"]
                        fidelity_status = status.get("fidelity", "unknown")
                        
                        print(f"   Fidelity status: {fidelity_status}")
                        
                        if fidelity_status in ["completed", "database_loaded_complete"]:
                            elapsed_time = time.time() - start_time
                            log_test("Wait for Reload", True, f"Data loading completed ({elapsed_time:.1f}s)")
                            return True
                        elif fidelity_status in ["error", "failed"]:
                            log_test("Wait for Reload", False, f"Data loading failed: {fidelity_status}")
                            return False
                
                time.sleep(10)  # Wait 10 seconds before checking again
                
            except Exception as e:
                print(f"   Error checking status: {e}")
                time.sleep(5)
        
        log_test("Wait for Reload", False, f"Timeout waiting for reload completion ({max_wait_time}s)")
        return False
        
    except Exception as e:
        log_test("Wait for Reload", False, f"Exception: {str(e)}")
        return False

def test_verify_increased_count():
    """Verify that fidelity count has increased after reload"""
    if not admin_token:
        log_test("Verify Increased Count", False, "No admin token available")
        return False, 0
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "users" in data and "total" in data:
                new_total = data["total"]
                log_test("Verify Increased Count", True, f"New count: {new_total:,} records ({response_time:.2f}s)")
                return True, new_total
            else:
                log_test("Verify Increased Count", False, "Invalid response structure")
                return False, 0
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Verify Increased Count", False, f"Status {response.status_code}: {error_detail}")
            return False, 0
            
    except Exception as e:
        log_test("Verify Increased Count", False, f"Exception: {str(e)}")
        return False, 0

def test_search_specific_card():
    """Search for card 2020000063308 (VASTO GIUSEPPINA) to verify it's now accessible"""
    if not admin_token:
        log_test("Search Specific Card", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Search for the specific card
        params = {"search": "2020000063308"}
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=params, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "users" in data:
                users = data["users"]
                found_card = None
                for user in users:
                    if user.get("tessera_fisica") == "2020000063308":
                        found_card = user
                        break
                
                if found_card:
                    # Verify card details
                    expected_details = {
                        "nome": "GIUSEPPINA",
                        "cognome": "VASTO",
                        "indirizzo": "VIA G. D'ANNUNZIO N.95/C",
                        "localita": "MOLA"
                    }
                    
                    details_match = True
                    mismatches = []
                    
                    for field, expected_value in expected_details.items():
                        actual_value = found_card.get(field, "")
                        if expected_value.upper() not in actual_value.upper():
                            details_match = False
                            mismatches.append(f"{field}: expected '{expected_value}', got '{actual_value}'")
                    
                    # Check spending and bollini
                    progressivo_spesa = found_card.get("progressivo_spesa", 0)
                    bollini = found_card.get("bollini", 0)
                    
                    if details_match:
                        log_test("Search Specific Card", True, 
                               f"Card 2020000063308 found: {found_card.get('nome')} {found_card.get('cognome')}, "
                               f"€{progressivo_spesa}, {bollini} bollini ({response_time:.2f}s)")
                        return True
                    else:
                        log_test("Search Specific Card", False, 
                               f"Card found but details mismatch: {'; '.join(mismatches)} ({response_time:.2f}s)")
                        return False
                else:
                    log_test("Search Specific Card", False, f"Card 2020000063308 still not found ({response_time:.2f}s)")
                    return False
            else:
                log_test("Search Specific Card", False, "Invalid response structure")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Search Specific Card", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Search Specific Card", False, f"Exception: {str(e)}")
        return False

def test_data_persistence():
    """Verify data persistence by checking count again after some time"""
    if not admin_token:
        log_test("Data Persistence", False, "No admin token available")
        return False
    
    try:
        print("⏳ Waiting 30 seconds to test data persistence...")
        time.sleep(30)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "users" in data and "total" in data:
                persistent_count = data["total"]
                log_test("Data Persistence", True, f"Data persisted: {persistent_count:,} records ({response_time:.2f}s)")
                return True, persistent_count
            else:
                log_test("Data Persistence", False, "Invalid response structure")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Data Persistence", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Data Persistence", False, f"Exception: {str(e)}")
        return False

def run_json_parsing_tests():
    """Run all JSON parsing and data persistence tests"""
    print("🧪 Starting JSON Parsing and Data Persistence Tests")
    print("=" * 60)
    
    # Step 1: Admin Authentication
    if not test_admin_authentication():
        print("❌ Cannot proceed without admin authentication")
        return False
    
    # Step 2: Check current database state
    success, initial_count = test_current_fidelity_count()
    if not success:
        print("❌ Cannot get initial fidelity count")
        return False
    
    # Step 3: Search for missing card
    test_search_missing_card()
    
    # Step 4: Trigger force data reload
    if not test_force_data_reload():
        print("❌ Cannot trigger data reload")
        return False
    
    # Step 5: Wait for reload completion
    if not test_wait_for_reload_completion():
        print("❌ Data reload did not complete successfully")
        return False
    
    # Step 6: Verify increased count
    success, new_count = test_verify_increased_count()
    if success:
        count_increase = new_count - initial_count
        if count_increase > 0:
            print(f"📈 Count increased by {count_increase:,} records ({initial_count:,} → {new_count:,})")
        else:
            print(f"⚠️  No count increase detected ({initial_count:,} → {new_count:,})")
    
    # Step 7: Search for specific card
    test_search_specific_card()
    
    # Step 8: Test data persistence
    test_data_persistence()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 JSON PARSING TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for result in test_results if result["success"])
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    print(f"\n🎯 Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
    
    if success_rate >= 80:
        print("🎉 JSON parsing and data persistence fix appears to be working!")
        return True
    else:
        print("⚠️  JSON parsing fix may need additional work")
        return False

if __name__ == "__main__":
    success = run_json_parsing_tests()
    sys.exit(0 if success else 1)
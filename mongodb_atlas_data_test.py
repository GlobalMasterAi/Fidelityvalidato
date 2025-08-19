#!/usr/bin/env python3
"""
MongoDB Atlas Data Persistence Investigation
Tests for the specific issue with card 2020000063308 (VASTO GIUSEPPINA) missing from database
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
print(f"🔗 Testing MongoDB Atlas Data Persistence at: {API_BASE}")

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

def admin_login():
    """Login as super admin"""
    global admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data["access_token"]
            log_test("Admin Login", True, f"Successfully logged in as superadmin (response time: {response.elapsed.total_seconds():.2f}s)")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return False

def test_current_fidelity_count():
    """Test current number of fidelity records in database"""
    if not admin_access_token:
        log_test("Current Fidelity Count", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" in data and "total" in data:
                total_count = data["total"]
                users_returned = len(data["users"])
                
                log_test("Current Fidelity Count", True, 
                        f"Database contains {total_count:,} fidelity records (returned {users_returned} in this page)")
                
                # Check if we have the expected full dataset
                if total_count < 30000:
                    log_test("Fidelity Count Analysis", False, 
                            f"⚠️ INCOMPLETE DATASET: Expected 30,300+ records, found only {total_count:,}")
                else:
                    log_test("Fidelity Count Analysis", True, 
                            f"✅ COMPLETE DATASET: Found {total_count:,} records (expected 30,300+)")
                
                return total_count
            else:
                log_test("Current Fidelity Count", False, f"Invalid response structure: {list(data.keys())}")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Current Fidelity Count", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Current Fidelity Count", False, f"Exception: {str(e)}")
        return False

def test_search_missing_card():
    """Test search for the specific missing card 2020000063308 (VASTO GIUSEPPINA)"""
    if not admin_access_token:
        log_test("Search Missing Card", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Search for the specific card
        search_params = {"search": "2020000063308"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=search_params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" in data:
                users = data["users"]
                found_card = False
                
                for user in users:
                    if user.get("tessera_fisica") == "2020000063308":
                        found_card = True
                        log_test("Search Missing Card", True, 
                                f"✅ FOUND: Card 2020000063308 - {user.get('nome', '')} {user.get('cognome', '')} from {user.get('localita', '')}")
                        
                        # Verify the expected data
                        if user.get("cognome") == "VASTO GIUSEPPINA":
                            log_test("Card Data Verification", True, "Card data matches expected: VASTO GIUSEPPINA")
                        else:
                            log_test("Card Data Verification", False, 
                                    f"Card data mismatch: expected VASTO GIUSEPPINA, got {user.get('cognome', '')}")
                        
                        return True
                
                if not found_card:
                    log_test("Search Missing Card", False, 
                            f"❌ MISSING: Card 2020000063308 not found in database (searched {len(users)} results)")
                    
                    # Try alternative searches
                    log_test("Alternative Search - VASTO", False, "Searching for 'VASTO' surname...")
                    vasto_params = {"search": "VASTO"}
                    vasto_response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=vasto_params, timeout=30)
                    
                    if vasto_response.status_code == 200:
                        vasto_data = vasto_response.json()
                        vasto_users = vasto_data.get("users", [])
                        log_test("Alternative Search - VASTO", len(vasto_users) > 0, 
                                f"Found {len(vasto_users)} users with surname containing 'VASTO'")
                        
                        for user in vasto_users:
                            print(f"  - {user.get('tessera_fisica', '')} {user.get('nome', '')} {user.get('cognome', '')}")
                    
                    return False
            else:
                log_test("Search Missing Card", False, f"Invalid response structure: {list(data.keys())}")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Search Missing Card", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Search Missing Card", False, f"Exception: {str(e)}")
        return False

def test_data_loading_status():
    """Test current data loading status"""
    try:
        # Try multiple status endpoints
        status_endpoints = [
            "/startup-status",
            "/readiness", 
            "/health"
        ]
        
        for endpoint in status_endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    log_test(f"Status Check {endpoint}", True, 
                            f"Status: {data.get('status', 'unknown')} - {json.dumps(data, indent=2)}")
                else:
                    log_test(f"Status Check {endpoint}", False, f"Status {response.status_code}")
                    
            except Exception as e:
                log_test(f"Status Check {endpoint}", False, f"Exception: {str(e)}")
        
        return True
        
    except Exception as e:
        log_test("Data Loading Status", False, f"Exception: {str(e)}")
        return False

def test_force_reload_data():
    """Test the /api/debug/force-reload-data endpoint to trigger fresh data load"""
    if not admin_access_token:
        log_test("Force Reload Data", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        print("🔄 Initiating force reload of data from fidelity_complete.json...")
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            log_test("Force Reload Data", True, 
                    f"Force reload initiated: {data.get('message', 'No message')}")
            
            # Wait a moment for the reload to start
            time.sleep(5)
            
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Force Reload Data", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Force Reload Data", False, f"Exception: {str(e)}")
        return False

def monitor_data_loading_progress():
    """Monitor data loading progress after force reload"""
    print("📊 Monitoring data loading progress...")
    
    max_attempts = 12  # 2 minutes with 10-second intervals
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            # Check readiness endpoint for loading status
            response = requests.get(f"{API_BASE}/readiness", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for loading status information
                if "data_loading_status" in data:
                    status = data["data_loading_status"]
                    print(f"  Attempt {attempt}: Data loading status - {json.dumps(status, indent=2)}")
                    
                    # Check if fidelity data loading is complete
                    fidelity_status = status.get("fidelity", "unknown")
                    if fidelity_status == "completed":
                        log_test("Data Loading Progress", True, 
                                f"Fidelity data loading completed after {attempt} attempts")
                        return True
                    elif "error" in fidelity_status.lower() or "failed" in fidelity_status.lower():
                        log_test("Data Loading Progress", False, 
                                f"Fidelity data loading failed: {fidelity_status}")
                        return False
                else:
                    print(f"  Attempt {attempt}: No data_loading_status in response")
            else:
                print(f"  Attempt {attempt}: Status endpoint returned {response.status_code}")
            
            if attempt < max_attempts:
                time.sleep(10)  # Wait 10 seconds before next check
                
        except Exception as e:
            print(f"  Attempt {attempt}: Exception - {str(e)}")
            if attempt < max_attempts:
                time.sleep(10)
    
    log_test("Data Loading Progress", False, 
            f"Data loading did not complete within {max_attempts * 10} seconds")
    return False

def test_post_reload_fidelity_count():
    """Test fidelity count after force reload"""
    if not admin_access_token:
        log_test("Post-Reload Fidelity Count", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "total" in data:
                total_count = data["total"]
                log_test("Post-Reload Fidelity Count", True, 
                        f"After reload: Database contains {total_count:,} fidelity records")
                
                # Check if we now have the full dataset
                if total_count >= 30000:
                    log_test("Full Dataset Check", True, 
                            f"✅ SUCCESS: Full dataset loaded ({total_count:,} records)")
                    return total_count
                else:
                    log_test("Full Dataset Check", False, 
                            f"❌ STILL INCOMPLETE: Only {total_count:,} records (expected 30,300+)")
                    return total_count
            else:
                log_test("Post-Reload Fidelity Count", False, f"Invalid response structure")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Post-Reload Fidelity Count", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Post-Reload Fidelity Count", False, f"Exception: {str(e)}")
        return False

def test_post_reload_missing_card():
    """Test search for missing card after force reload"""
    if not admin_access_token:
        log_test("Post-Reload Missing Card", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Search for the specific card again
        search_params = {"search": "2020000063308"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=search_params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "users" in data:
                users = data["users"]
                
                for user in users:
                    if user.get("tessera_fisica") == "2020000063308":
                        log_test("Post-Reload Missing Card", True, 
                                f"✅ FOUND AFTER RELOAD: Card 2020000063308 - {user.get('nome', '')} {user.get('cognome', '')} from {user.get('localita', '')}")
                        
                        # Verify expected data
                        expected_data = {
                            "nome": "GIUSEPPINA",
                            "cognome": "VASTO", 
                            "indirizzo": "VIA G. D'ANNUNZIO N.95/C",
                            "localita": "MOLA"
                        }
                        
                        data_matches = True
                        for field, expected_value in expected_data.items():
                            actual_value = user.get(field, "")
                            if expected_value.lower() not in actual_value.lower():
                                log_test(f"Data Verification - {field}", False, 
                                        f"Expected '{expected_value}', got '{actual_value}'")
                                data_matches = False
                            else:
                                log_test(f"Data Verification - {field}", True, 
                                        f"✅ {field}: {actual_value}")
                        
                        if data_matches:
                            log_test("Complete Data Verification", True, 
                                    "✅ All expected data fields match for card 2020000063308")
                        
                        return True
                
                log_test("Post-Reload Missing Card", False, 
                        f"❌ STILL MISSING: Card 2020000063308 not found even after reload")
                return False
            else:
                log_test("Post-Reload Missing Card", False, f"Invalid response structure")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Post-Reload Missing Card", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Post-Reload Missing Card", False, f"Exception: {str(e)}")
        return False

def test_data_persistence_stability():
    """Test if data remains persistent after some time"""
    print("⏳ Testing data persistence stability (waiting 30 seconds)...")
    time.sleep(30)
    
    # Re-check the fidelity count
    final_count = test_current_fidelity_count()
    
    if final_count and final_count >= 30000:
        log_test("Data Persistence Stability", True, 
                f"✅ Data remains stable: {final_count:,} records after 30 seconds")
        return True
    else:
        log_test("Data Persistence Stability", False, 
                f"❌ Data persistence issue: count dropped to {final_count}")
        return False

def analyze_root_cause():
    """Analyze potential root causes of the data persistence issue"""
    print("\n🔍 ROOT CAUSE ANALYSIS")
    print("=" * 50)
    
    # Check if there are any timeout or memory issues
    potential_causes = []
    
    # Analyze test results
    failed_tests = [test for test in test_results if not test["success"]]
    
    if any("timeout" in test["message"].lower() for test in failed_tests):
        potential_causes.append("MongoDB Atlas connection timeouts during large data operations")
    
    if any("memory" in test["message"].lower() for test in failed_tests):
        potential_causes.append("Memory limitations during data loading")
    
    # Check for incomplete loading patterns
    incomplete_loads = [test for test in test_results if "incomplete" in test["message"].lower()]
    if incomplete_loads:
        potential_causes.append("Incomplete data loading process - data loading stops before completion")
    
    # Check for persistence issues
    persistence_issues = [test for test in test_results if "persistence" in test["message"].lower()]
    if persistence_issues:
        potential_causes.append("Data persistence issues - data not properly saved to MongoDB Atlas")
    
    if not potential_causes:
        potential_causes.append("Unknown cause - further investigation needed")
    
    print("Potential Root Causes:")
    for i, cause in enumerate(potential_causes, 1):
        print(f"  {i}. {cause}")
    
    return potential_causes

def main():
    """Main test execution"""
    print("🚀 Starting MongoDB Atlas Data Persistence Investigation")
    print("=" * 60)
    
    # Step 1: Admin login
    if not admin_login():
        print("❌ Cannot proceed without admin access")
        return
    
    # Step 2: Check current database state
    print("\n📊 STEP 1: DATABASE STATE CHECK")
    print("-" * 40)
    
    initial_count = test_current_fidelity_count()
    test_search_missing_card()
    test_data_loading_status()
    
    # Step 3: Force reload data
    print("\n🔄 STEP 2: DATA PERSISTENCE ISSUE INVESTIGATION")
    print("-" * 50)
    
    if test_force_reload_data():
        # Monitor progress
        if monitor_data_loading_progress():
            # Check results after reload
            print("\n📈 STEP 3: POST-RELOAD VERIFICATION")
            print("-" * 40)
            
            post_reload_count = test_post_reload_fidelity_count()
            test_post_reload_missing_card()
            
            # Test persistence stability
            test_data_persistence_stability()
        else:
            print("⚠️ Data loading did not complete successfully")
    else:
        print("❌ Could not initiate force reload")
    
    # Step 4: Root cause analysis
    print("\n🔍 STEP 4: ROOT CAUSE ANALYSIS")
    print("-" * 40)
    
    root_causes = analyze_root_cause()
    
    # Final summary
    print("\n📋 FINAL SUMMARY")
    print("=" * 40)
    
    total_tests = len(test_results)
    passed_tests = len([test for test in test_results if test["success"]])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Key findings
    print("\n🔑 KEY FINDINGS:")
    
    if initial_count and initial_count < 30000:
        print(f"  • Database contains only {initial_count:,} records instead of expected 30,300+")
    
    missing_card_found = any("FOUND" in test["message"] for test in test_results if "Missing Card" in test["test"])
    if not missing_card_found:
        print("  • Card 2020000063308 (VASTO GIUSEPPINA) is missing from database")
    else:
        print("  • Card 2020000063308 (VASTO GIUSEPPINA) was found in database")
    
    reload_successful = any("SUCCESS" in test["message"] for test in test_results if "Full Dataset" in test["test"])
    if reload_successful:
        print("  • Force reload successfully loaded full dataset")
    else:
        print("  • Force reload did not resolve the incomplete dataset issue")
    
    print(f"\n💡 RECOMMENDED ACTIONS:")
    print("  1. Check MongoDB Atlas timeout settings for large operations")
    print("  2. Verify fidelity_complete.json file contains all 30,300+ records")
    print("  3. Monitor memory usage during data loading operations")
    print("  4. Consider implementing chunked data loading for large datasets")
    
    return test_results

if __name__ == "__main__":
    results = main()
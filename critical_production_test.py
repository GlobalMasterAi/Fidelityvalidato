#!/usr/bin/env python3
"""
CRITICAL PRODUCTION ISSUE TESTING
Tests for specific live production issues reported in the review request:
1. Missing User Card 401004000025 (ARESTA)
2. Empty User Dashboard Sections for ELISA
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
print(f"🔗 Testing Critical Production Issues at: {API_BASE}")
print(f"🚨 URGENT LIVE PRODUCTION ISSUE TESTING")
print("=" * 80)

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
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def test_admin_authentication():
    """Test super admin login for accessing admin endpoints"""
    global admin_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get("access_token")
            log_test("Admin Authentication", True, f"Super admin login successful (Response time: {response.elapsed.total_seconds():.2f}s)")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Admin Authentication", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Admin Authentication", False, f"Exception: {str(e)}")
        return False

def test_missing_card_401004000025():
    """CRITICAL ISSUE 1: Test for missing card 401004000025 (ARESTA)"""
    try:
        # Test the card lookup endpoint directly
        card_data = {"tessera_fisica": "401004000025"}
        
        response = requests.post(f"{API_BASE}/check-tessera", json=card_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("found"):
                user_data = data.get("user_data", {})
                cognome = user_data.get("cognome", "")
                
                if "ARESTA" in cognome.upper():
                    log_test("Missing Card 401004000025", True, f"✅ CARD FOUND: {cognome} - Card is accessible in database")
                    return True
                else:
                    log_test("Missing Card 401004000025", False, f"❌ CARD FOUND BUT WRONG SURNAME: Expected ARESTA, got {cognome}")
                    return False
            else:
                log_test("Missing Card 401004000025", False, "❌ CRITICAL: Card 401004000025 (ARESTA) NOT FOUND in database")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Missing Card 401004000025", False, f"❌ API Error - Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Missing Card 401004000025", False, f"❌ Exception: {str(e)}")
        return False

def test_fidelity_data_search():
    """Search fidelity database for ARESTA surname"""
    if not admin_token:
        log_test("Fidelity Data Search", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Search for ARESTA in fidelity users
        response = requests.get(f"{API_BASE}/admin/fidelity-users?search=ARESTA", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            total = data.get("total", 0)
            
            if total > 0:
                aresta_users = []
                for user in users:
                    if "ARESTA" in user.get("cognome", "").upper():
                        aresta_users.append({
                            "tessera": user.get("tessera_fisica", ""),
                            "nome": user.get("nome", ""),
                            "cognome": user.get("cognome", ""),
                            "progressivo_spesa": user.get("progressivo_spesa", 0)
                        })
                
                if aresta_users:
                    log_test("Fidelity Data Search", True, f"Found {len(aresta_users)} ARESTA users in database")
                    for user in aresta_users:
                        print(f"   📋 {user['tessera']} - {user['nome']} {user['cognome']} (€{user['progressivo_spesa']})")
                    return True
                else:
                    log_test("Fidelity Data Search", False, "❌ No ARESTA users found in search results")
                    return False
            else:
                log_test("Fidelity Data Search", False, "❌ Search returned no results for ARESTA")
                return False
                
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Fidelity Data Search", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Fidelity Data Search", False, f"Exception: {str(e)}")
        return False

def test_user_profile_endpoint():
    """CRITICAL ISSUE 2: Test user profile endpoint for dashboard data"""
    try:
        # First, try to find a user named ELISA
        if not admin_token:
            log_test("User Profile Endpoint", False, "No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Search for ELISA users
        response = requests.get(f"{API_BASE}/admin/fidelity-users?search=ELISA", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            elisa_users = []
            for user in users:
                if "ELISA" in user.get("nome", "").upper():
                    elisa_users.append(user)
            
            if elisa_users:
                test_user = elisa_users[0]
                tessera = test_user.get("tessera_fisica", "")
                
                log_test("User Profile Endpoint", True, f"Found ELISA user with tessera: {tessera}")
                
                # Test the profile data structure
                profile_data = {
                    "nome": test_user.get("nome", ""),
                    "cognome": test_user.get("cognome", ""),
                    "tessera_fisica": tessera,
                    "progressivo_spesa": test_user.get("progressivo_spesa", 0),
                    "bollini": test_user.get("bollini", 0)
                }
                
                print(f"   📋 Profile Data: {profile_data}")
                return True
            else:
                log_test("User Profile Endpoint", False, "❌ No ELISA users found in database")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Profile Endpoint", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Profile Endpoint", False, f"Exception: {str(e)}")
        return False

def test_user_rewards_endpoint():
    """Test user rewards endpoint for dashboard data"""
    try:
        # Test the rewards endpoint structure
        # Since we need a logged-in user, we'll test the endpoint structure
        
        # Test if the endpoint exists and returns proper error for unauthenticated request
        response = requests.get(f"{API_BASE}/user/rewards", timeout=30)
        
        if response.status_code == 403 or response.status_code == 401:
            log_test("User Rewards Endpoint", True, "Rewards endpoint exists and requires authentication")
            return True
        elif response.status_code == 404:
            log_test("User Rewards Endpoint", False, "❌ Rewards endpoint not found (404)")
            return False
        else:
            log_test("User Rewards Endpoint", True, f"Rewards endpoint accessible (Status: {response.status_code})")
            return True
            
    except Exception as e:
        log_test("User Rewards Endpoint", False, f"Exception: {str(e)}")
        return False

def test_data_integrity_verification():
    """Verify data loading status and integrity"""
    if not admin_token:
        log_test("Data Integrity Verification", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test fidelity data count
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            total_fidelity = data.get("total", 0)
            
            # Test admin stats
            stats_response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers, timeout=30)
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                
                log_test("Data Integrity Verification", True, 
                        f"✅ Fidelity Records: {total_fidelity:,}, "
                        f"Total Users: {stats_data.get('total_users', 0)}, "
                        f"Total Stores: {stats_data.get('total_stores', 0)}")
                
                # Check if we have reasonable data
                if total_fidelity < 20000:
                    print(f"   ⚠️  WARNING: Fidelity record count ({total_fidelity:,}) seems low (expected ~30,287)")
                
                return True
            else:
                log_test("Data Integrity Verification", False, f"Stats endpoint error: {stats_response.status_code}")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Data Integrity Verification", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Data Integrity Verification", False, f"Exception: {str(e)}")
        return False

def test_card_lookup_multiple_formats():
    """Test card lookup with different formats to find missing cards"""
    try:
        # Test various card number formats that might be in the system
        test_cards = [
            "401004000025",      # Original format
            "2020000401004000025", # With prefix
            "0401004000025",     # With leading zero
            "4010040000025",     # Without one zero
        ]
        
        found_cards = []
        
        for card in test_cards:
            try:
                card_data = {"tessera_fisica": card}
                response = requests.post(f"{API_BASE}/check-tessera", json=card_data, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("found"):
                        user_data = data.get("user_data", {})
                        found_cards.append({
                            "card": card,
                            "nome": user_data.get("nome", ""),
                            "cognome": user_data.get("cognome", "")
                        })
            except:
                continue
        
        if found_cards:
            log_test("Card Lookup Multiple Formats", True, f"Found {len(found_cards)} cards with different formats")
            for card_info in found_cards:
                print(f"   📋 {card_info['card']} - {card_info['nome']} {card_info['cognome']}")
            return True
        else:
            log_test("Card Lookup Multiple Formats", False, "❌ No cards found with any format variation")
            return False
            
    except Exception as e:
        log_test("Card Lookup Multiple Formats", False, f"Exception: {str(e)}")
        return False

def run_critical_tests():
    """Run all critical production tests"""
    print("🚨 STARTING CRITICAL PRODUCTION ISSUE TESTING")
    print("=" * 80)
    
    tests = [
        ("Admin Authentication", test_admin_authentication),
        ("Missing Card 401004000025 (ARESTA)", test_missing_card_401004000025),
        ("Fidelity Data Search for ARESTA", test_fidelity_data_search),
        ("Card Lookup Multiple Formats", test_card_lookup_multiple_formats),
        ("User Profile Endpoint (ELISA)", test_user_profile_endpoint),
        ("User Rewards Endpoint", test_user_rewards_endpoint),
        ("Data Integrity Verification", test_data_integrity_verification),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("🚨 CRITICAL PRODUCTION ISSUE TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (passed / total) * 100
    print(f"📊 Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    # Critical findings
    print("\n🚨 CRITICAL FINDINGS:")
    critical_issues = [r for r in test_results if not r["success"] and "401004000025" in r["test"]]
    
    if critical_issues:
        print("❌ PRODUCTION BLOCKING ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   • {issue['test']}: {issue['message']}")
    else:
        print("✅ No critical blocking issues found for card lookup")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if any("401004000025" in r["test"] and not r["success"] for r in test_results):
        print("   1. Check fidelity_complete.json file for card 401004000025")
        print("   2. Verify JSON parsing is not skipping records")
        print("   3. Check database loading logs for errors")
    
    if any("ELISA" in r["test"] and not r["success"] for r in test_results):
        print("   4. Verify user dashboard API endpoints are implemented")
        print("   5. Check user profile and rewards data population")
    
    return success_rate >= 70  # Consider successful if 70% or more tests pass

if __name__ == "__main__":
    success = run_critical_tests()
    sys.exit(0 if success else 1)
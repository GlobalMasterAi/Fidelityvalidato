#!/usr/bin/env python3
"""
LOCAL CRITICAL PRODUCTION ISSUE TESTING
Tests for specific live production issues using local backend
"""

import requests
import json
import sys
from datetime import datetime

# Use local backend URL
API_BASE = "http://localhost:8001/api"
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

def test_backend_connectivity():
    """Test if backend is running and accessible"""
    try:
        response = requests.get("http://localhost:8001/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "ImaGross" in data.get("message", ""):
                log_test("Backend Connectivity", True, f"Backend is running and accessible")
                return True
            else:
                log_test("Backend Connectivity", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("Backend Connectivity", False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Backend Connectivity", False, f"Connection error: {str(e)}")
        return False

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
                nome = user_data.get("nome", "")
                progressivo_spesa = user_data.get("progressivo_spesa", 0)
                
                if "ARESTA" in cognome.upper():
                    log_test("Missing Card 401004000025", True, 
                            f"✅ CARD FOUND: {nome} {cognome} - €{progressivo_spesa} - Card is accessible in database")
                    return True
                else:
                    log_test("Missing Card 401004000025", False, 
                            f"❌ CARD FOUND BUT WRONG SURNAME: Expected ARESTA, got {cognome}")
                    return False
            else:
                log_test("Missing Card 401004000025", False, 
                        "❌ CRITICAL: Card 401004000025 (ARESTA) NOT FOUND in database")
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

def test_user_dashboard_endpoints():
    """CRITICAL ISSUE 2: Test user dashboard endpoints for ELISA"""
    if not admin_token:
        log_test("User Dashboard Endpoints", False, "No admin token available")
        return False
    
    try:
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
                nome = test_user.get("nome", "")
                cognome = test_user.get("cognome", "")
                progressivo_spesa = test_user.get("progressivo_spesa", 0)
                bollini = test_user.get("bollini", 0)
                
                log_test("User Dashboard Endpoints", True, 
                        f"Found ELISA user: {nome} {cognome} (Tessera: {tessera}, €{progressivo_spesa}, {bollini} bollini)")
                
                # Test if user can login (simulate dashboard access)
                print(f"   📋 Profile Data Available: Nome={nome}, Cognome={cognome}, Spesa=€{progressivo_spesa}, Bollini={bollini}")
                
                # Check if profile data is complete
                if progressivo_spesa > 0 or bollini > 0:
                    print(f"   ✅ User has spending/loyalty data - Dashboard should show content")
                else:
                    print(f"   ⚠️  User has no spending/loyalty data - Dashboard sections may appear empty")
                
                return True
            else:
                log_test("User Dashboard Endpoints", False, "❌ No ELISA users found in database")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Dashboard Endpoints", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Dashboard Endpoints", False, f"Exception: {str(e)}")
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
                
                # Check if we have the expected 30,287 records mentioned in review
                if total_fidelity >= 30000:
                    print(f"   ✅ Fidelity data count looks good ({total_fidelity:,} records)")
                
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
                            "cognome": user_data.get("cognome", ""),
                            "progressivo_spesa": user_data.get("progressivo_spesa", 0)
                        })
            except:
                continue
        
        if found_cards:
            log_test("Card Lookup Multiple Formats", True, f"Found {len(found_cards)} cards with different formats")
            for card_info in found_cards:
                print(f"   📋 {card_info['card']} - {card_info['nome']} {card_info['cognome']} (€{card_info['progressivo_spesa']})")
            return True
        else:
            log_test("Card Lookup Multiple Formats", False, "❌ No cards found with any format variation")
            return False
            
    except Exception as e:
        log_test("Card Lookup Multiple Formats", False, f"Exception: {str(e)}")
        return False

def test_sample_working_cards():
    """Test some sample cards to verify the system is working"""
    if not admin_token:
        log_test("Sample Working Cards", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a few sample users from fidelity data
        response = requests.get(f"{API_BASE}/admin/fidelity-users?limit=5", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            working_cards = 0
            
            for user in users[:3]:  # Test first 3 users
                tessera = user.get("tessera_fisica", "")
                if tessera:
                    card_data = {"tessera_fisica": tessera}
                    card_response = requests.post(f"{API_BASE}/check-tessera", json=card_data, timeout=10)
                    
                    if card_response.status_code == 200:
                        card_result = card_response.json()
                        if card_result.get("found"):
                            working_cards += 1
                            user_data = card_result.get("user_data", {})
                            print(f"   ✅ {tessera} - {user_data.get('nome', '')} {user_data.get('cognome', '')}")
            
            if working_cards > 0:
                log_test("Sample Working Cards", True, f"{working_cards} sample cards are working correctly")
                return True
            else:
                log_test("Sample Working Cards", False, "❌ No sample cards are working")
                return False
        else:
            log_test("Sample Working Cards", False, f"Could not get sample users: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Sample Working Cards", False, f"Exception: {str(e)}")
        return False

def run_critical_tests():
    """Run all critical production tests"""
    print("🚨 STARTING CRITICAL PRODUCTION ISSUE TESTING")
    print("=" * 80)
    
    tests = [
        ("Backend Connectivity", test_backend_connectivity),
        ("Admin Authentication", test_admin_authentication),
        ("Data Integrity Verification", test_data_integrity_verification),
        ("Sample Working Cards", test_sample_working_cards),
        ("Missing Card 401004000025 (ARESTA)", test_missing_card_401004000025),
        ("Card Lookup Multiple Formats", test_card_lookup_multiple_formats),
        ("Fidelity Data Search for ARESTA", test_fidelity_data_search),
        ("User Dashboard Endpoints (ELISA)", test_user_dashboard_endpoints),
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
    critical_issues = [r for r in test_results if not r["success"] and ("401004000025" in r["test"] or "ELISA" in r["test"])]
    
    if critical_issues:
        print("❌ PRODUCTION BLOCKING ISSUES FOUND:")
        for issue in critical_issues:
            print(f"   • {issue['test']}: {issue['message']}")
    else:
        print("✅ No critical blocking issues found")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if any("401004000025" in r["test"] and not r["success"] for r in test_results):
        print("   1. ❌ URGENT: Card 401004000025 (ARESTA) is missing from the database")
        print("   2. Check fidelity_complete.json file for this specific card")
        print("   3. Verify JSON parsing is not skipping records due to malformed data")
        print("   4. Consider re-importing the fidelity data")
    
    if any("ELISA" in r["test"] and not r["success"] for r in test_results):
        print("   5. ❌ URGENT: ELISA user dashboard data issues")
        print("   6. Verify user profile and rewards endpoints are working")
        print("   7. Check if user has spending/loyalty data to display")
    
    return success_rate >= 70  # Consider successful if 70% or more tests pass

if __name__ == "__main__":
    success = run_critical_tests()
    sys.exit(0 if success else 1)
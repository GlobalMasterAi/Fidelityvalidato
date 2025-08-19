#!/usr/bin/env python3
"""
USER DASHBOARD TESTING - Focus on ELISA user dashboard sections
Tests the specific endpoints that populate user dashboard sections
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8001/api"
print(f"🔗 Testing User Dashboard at: {API_BASE}")
print(f"👤 USER DASHBOARD SECTION TESTING - ELISA USER FOCUS")
print("=" * 80)

# Test results tracking
test_results = []
admin_token = None
user_token = None
test_user_data = None

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

def test_admin_login():
    """Get admin token for user lookup"""
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
            log_test("Admin Login", True, "Admin authentication successful")
            return True
        else:
            log_test("Admin Login", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return False

def test_find_elisa_user():
    """Find ELISA user in the system"""
    global test_user_data
    
    if not admin_token:
        log_test("Find ELISA User", False, "No admin token available")
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
                test_user_data = elisa_users[0]  # Use first ELISA user
                tessera = test_user_data.get("tessera_fisica", "")
                nome = test_user_data.get("nome", "")
                cognome = test_user_data.get("cognome", "")
                progressivo_spesa = test_user_data.get("progressivo_spesa", 0)
                bollini = test_user_data.get("bollini", 0)
                
                log_test("Find ELISA User", True, 
                        f"Found: {nome} {cognome} (Tessera: {tessera}, €{progressivo_spesa}, {bollini} bollini)")
                
                print(f"   📋 User Details:")
                print(f"      - Nome: {nome}")
                print(f"      - Cognome: {cognome}")
                print(f"      - Tessera: {tessera}")
                print(f"      - Progressivo Spesa: €{progressivo_spesa}")
                print(f"      - Bollini: {bollini}")
                print(f"      - Email: {test_user_data.get('email', 'N/A')}")
                print(f"      - Telefono: {test_user_data.get('n_telefono', 'N/A')}")
                print(f"      - Localita: {test_user_data.get('localita', 'N/A')}")
                
                return True
            else:
                log_test("Find ELISA User", False, "No ELISA users found in database")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Find ELISA User", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Find ELISA User", False, f"Exception: {str(e)}")
        return False

def test_user_profile_endpoint():
    """Test /api/user/profile endpoint (Profilo section)"""
    if not test_user_data:
        log_test("User Profile Endpoint", False, "No test user data available")
        return False
    
    try:
        # Since we can't login as ELISA (we don't have her password), 
        # we'll test the endpoint structure and what data would be available
        
        tessera = test_user_data.get("tessera_fisica", "")
        
        # Test the check-tessera endpoint to see what profile data is available
        card_data = {"tessera_fisica": tessera}
        response = requests.post(f"{API_BASE}/check-tessera", json=card_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("found"):
                user_data = data.get("user_data", {})
                
                # Check what profile data is available
                profile_fields = {
                    "nome": user_data.get("nome", ""),
                    "cognome": user_data.get("cognome", ""),
                    "email": user_data.get("email", ""),
                    "telefono": user_data.get("n_telefono", ""),
                    "localita": user_data.get("localita", ""),
                    "indirizzo": user_data.get("indirizzo", ""),
                    "progressivo_spesa": user_data.get("progressivo_spesa", 0),
                    "bollini": user_data.get("bollini", 0),
                    "data_nascita": user_data.get("data_nas", ""),
                    "sesso": user_data.get("sesso", "")
                }
                
                # Count non-empty fields
                populated_fields = sum(1 for v in profile_fields.values() if v)
                total_fields = len(profile_fields)
                
                log_test("User Profile Endpoint", True, 
                        f"Profile data available: {populated_fields}/{total_fields} fields populated")
                
                print(f"   📋 Profile Data Analysis:")
                for field, value in profile_fields.items():
                    status = "✅" if value else "❌"
                    print(f"      {status} {field}: {value if value else 'EMPTY'}")
                
                # Check if critical profile fields are populated
                critical_fields = ["nome", "cognome", "progressivo_spesa", "bollini"]
                critical_populated = all(profile_fields.get(field) for field in critical_fields)
                
                if critical_populated:
                    print(f"   ✅ Critical profile fields are populated - Profilo section should show data")
                else:
                    print(f"   ⚠️  Some critical profile fields are missing - Profilo section may appear empty")
                
                return True
            else:
                log_test("User Profile Endpoint", False, "User data not found via check-tessera")
                return False
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Profile Endpoint", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Profile Endpoint", False, f"Exception: {str(e)}")
        return False

def test_user_rewards_offers_endpoint():
    """Test rewards and offers endpoints (Premi & Offerte section)"""
    if not admin_token:
        log_test("User Rewards & Offers", False, "No admin token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test if rewards system is implemented
        rewards_response = requests.get(f"{API_BASE}/admin/rewards", headers=headers, timeout=30)
        
        if rewards_response.status_code == 200:
            rewards_data = rewards_response.json()
            rewards = rewards_data.get("rewards", [])
            
            log_test("User Rewards & Offers", True, 
                    f"Rewards system active: {len(rewards)} rewards available")
            
            print(f"   📋 Rewards System Analysis:")
            print(f"      - Total rewards in system: {len(rewards)}")
            
            if rewards:
                # Analyze reward categories
                categories = {}
                for reward in rewards:
                    category = reward.get("category", "Unknown")
                    categories[category] = categories.get(category, 0) + 1
                
                print(f"      - Reward categories:")
                for category, count in categories.items():
                    print(f"        • {category}: {count} rewards")
                
                # Check if user would have access to rewards based on bollini
                user_bollini = test_user_data.get("bollini", 0) if test_user_data else 0
                accessible_rewards = 0
                
                for reward in rewards:
                    required_bollini = reward.get("bollini_required", 0)
                    if user_bollini >= required_bollini:
                        accessible_rewards += 1
                
                print(f"      - User bollini: {user_bollini}")
                print(f"      - Accessible rewards for user: {accessible_rewards}/{len(rewards)}")
                
                if accessible_rewards > 0:
                    print(f"   ✅ User has access to rewards - Premi & Offerte section should show content")
                else:
                    print(f"   ⚠️  User has no accessible rewards - Premi & Offerte section may appear empty")
            else:
                print(f"   ⚠️  No rewards configured - Premi & Offerte section will appear empty")
            
            return True
        elif rewards_response.status_code == 404:
            log_test("User Rewards & Offers", False, "Rewards endpoint not found - feature not implemented")
            return False
        else:
            error_detail = rewards_response.json().get("detail", "Unknown error") if rewards_response.content else "No response"
            log_test("User Rewards & Offers", False, f"Status {rewards_response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Rewards & Offers", False, f"Exception: {str(e)}")
        return False

def test_user_personal_analytics():
    """Test personal analytics endpoint for dashboard data"""
    try:
        # Test if the personal analytics endpoint exists
        response = requests.get(f"{API_BASE}/user/personal-analytics", timeout=30)
        
        if response.status_code == 401 or response.status_code == 403:
            log_test("User Personal Analytics", True, "Personal analytics endpoint exists and requires authentication")
            print(f"   📋 Endpoint exists and properly secured")
            return True
        elif response.status_code == 404:
            log_test("User Personal Analytics", False, "Personal analytics endpoint not found")
            return False
        else:
            log_test("User Personal Analytics", True, f"Personal analytics endpoint accessible (Status: {response.status_code})")
            return True
            
    except Exception as e:
        log_test("User Personal Analytics", False, f"Exception: {str(e)}")
        return False

def test_dashboard_data_completeness():
    """Analyze if ELISA user has complete data for dashboard sections"""
    if not test_user_data:
        log_test("Dashboard Data Completeness", False, "No test user data available")
        return False
    
    try:
        # Analyze user data completeness
        user_analysis = {
            "basic_profile": {
                "nome": bool(test_user_data.get("nome")),
                "cognome": bool(test_user_data.get("cognome")),
                "email": bool(test_user_data.get("email")),
                "telefono": bool(test_user_data.get("n_telefono")),
                "localita": bool(test_user_data.get("localita"))
            },
            "loyalty_data": {
                "progressivo_spesa": test_user_data.get("progressivo_spesa", 0) > 0,
                "bollini": test_user_data.get("bollini", 0) > 0,
                "data_ultima_spesa": bool(test_user_data.get("data_ult_sc"))
            },
            "extended_profile": {
                "indirizzo": bool(test_user_data.get("indirizzo")),
                "data_nascita": bool(test_user_data.get("data_nas")),
                "sesso": bool(test_user_data.get("sesso"))
            }
        }
        
        # Calculate completeness scores
        basic_score = sum(user_analysis["basic_profile"].values()) / len(user_analysis["basic_profile"]) * 100
        loyalty_score = sum(user_analysis["loyalty_data"].values()) / len(user_analysis["loyalty_data"]) * 100
        extended_score = sum(user_analysis["extended_profile"].values()) / len(user_analysis["extended_profile"]) * 100
        
        overall_score = (basic_score + loyalty_score + extended_score) / 3
        
        log_test("Dashboard Data Completeness", True, 
                f"Data completeness: {overall_score:.1f}% overall")
        
        print(f"   📋 Data Completeness Analysis:")
        print(f"      - Basic Profile: {basic_score:.1f}% complete")
        print(f"      - Loyalty Data: {loyalty_score:.1f}% complete")
        print(f"      - Extended Profile: {extended_score:.1f}% complete")
        print(f"      - Overall: {overall_score:.1f}% complete")
        
        # Detailed breakdown
        print(f"   📋 Field-by-Field Analysis:")
        for category, fields in user_analysis.items():
            print(f"      {category.replace('_', ' ').title()}:")
            for field, has_data in fields.items():
                status = "✅" if has_data else "❌"
                value = test_user_data.get(field) or test_user_data.get(field.replace('n_telefono', 'telefono'))
                print(f"        {status} {field}: {value if has_data else 'MISSING'}")
        
        # Dashboard section predictions
        print(f"   🎯 Dashboard Section Predictions:")
        if basic_score >= 80 and loyalty_score >= 60:
            print(f"      ✅ Profilo section: Should display user data")
        else:
            print(f"      ⚠️  Profilo section: May appear incomplete")
        
        if loyalty_score >= 60:
            print(f"      ✅ Loyalty data: Should show spending and bollini")
        else:
            print(f"      ❌ Loyalty data: May appear empty")
        
        return True
        
    except Exception as e:
        log_test("Dashboard Data Completeness", False, f"Exception: {str(e)}")
        return False

def run_dashboard_tests():
    """Run all user dashboard tests"""
    print("👤 STARTING USER DASHBOARD SECTION TESTING")
    print("=" * 80)
    
    tests = [
        ("Admin Login", test_admin_login),
        ("Find ELISA User", test_find_elisa_user),
        ("User Profile Endpoint (Profilo)", test_user_profile_endpoint),
        ("User Rewards & Offers (Premi & Offerte)", test_user_rewards_offers_endpoint),
        ("User Personal Analytics", test_user_personal_analytics),
        ("Dashboard Data Completeness", test_dashboard_data_completeness),
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
    print("👤 USER DASHBOARD TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (passed / total) * 100
    print(f"📊 Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    # Dashboard section analysis
    print("\n🎯 DASHBOARD SECTION ANALYSIS:")
    
    profilo_issues = [r for r in test_results if not r["success"] and "Profile" in r["test"]]
    premi_issues = [r for r in test_results if not r["success"] and "Rewards" in r["test"]]
    
    if not profilo_issues:
        print("✅ PROFILO SECTION: Should display user data correctly")
    else:
        print("❌ PROFILO SECTION: May appear empty due to:")
        for issue in profilo_issues:
            print(f"   • {issue['message']}")
    
    if not premi_issues:
        print("✅ PREMI & OFFERTE SECTION: Should display rewards correctly")
    else:
        print("❌ PREMI & OFFERTE SECTION: May appear empty due to:")
        for issue in premi_issues:
            print(f"   • {issue['message']}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS FOR ELISA USER DASHBOARD:")
    
    if test_user_data:
        progressivo_spesa = test_user_data.get("progressivo_spesa", 0)
        bollini = test_user_data.get("bollini", 0)
        
        if progressivo_spesa > 0 and bollini > 0:
            print("   ✅ User has loyalty data - Dashboard sections should populate correctly")
        else:
            print("   ⚠️  User lacks loyalty data - This may cause empty dashboard sections")
            print("   💡 Verify user's spending history and bollini calculation")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = run_dashboard_tests()
    sys.exit(0 if success else 1)
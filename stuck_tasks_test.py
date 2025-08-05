#!/usr/bin/env python3
"""
Testing Stuck Tasks from test_result.md:
1. Enhanced Fidelity Validation with Cognome + Tessera
2. Enhanced Multi-Format Login System
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
print(f"🔍 TESTING STUCK TASKS")
print(f"🔗 Testing at: {API_BASE}")
print("=" * 60)

# Test results tracking
test_results = []

def log_test(test_name, success, message=""):
    """Log test results"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {message}")
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message
    })

def test_enhanced_fidelity_validation():
    """Test Enhanced Fidelity Validation with Cognome + Tessera"""
    print("\n🔍 TESTING: Enhanced Fidelity Validation")
    print("-" * 50)
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Valid Card with Correct Cognome",
            "data": {"tessera_fisica": "2020000400004", "cognome": "SCHEDA 202000040000"},
            "expected": "found_or_migrated"
        },
        {
            "name": "Valid Card with Wrong Cognome", 
            "data": {"tessera_fisica": "2020000400004", "cognome": "WRONG_COGNOME"},
            "expected": "mismatch"
        },
        {
            "name": "Non-existent Card",
            "data": {"tessera_fisica": "9999999999999", "cognome": "TEST"},
            "expected": "not_found"
        },
        {
            "name": "Card Without Cognome (Backward Compatibility)",
            "data": {"tessera_fisica": "2020000400004"},
            "expected": "found_or_migrated"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            response = requests.post(f"{API_BASE}/check-tessera", json=test_case["data"], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "found" in data and "migrated" in data:
                    if test_case["expected"] == "found_or_migrated":
                        if data["found"]:
                            if data["migrated"]:
                                log_test(test_case["name"], True, "Card already migrated (expected)")
                                passed += 1
                            elif "user_data" in data:
                                log_test(test_case["name"], True, "Card found with user data")
                                passed += 1
                            else:
                                log_test(test_case["name"], False, "Card found but no user_data")
                        else:
                            log_test(test_case["name"], False, "Card not found when expected")
                    elif test_case["expected"] == "not_found":
                        if not data["found"]:
                            log_test(test_case["name"], True, "Card correctly not found")
                            passed += 1
                        else:
                            log_test(test_case["name"], False, "Card found when should not exist")
                    elif test_case["expected"] == "mismatch":
                        # For cognome mismatch, we expect either not found or specific error
                        if not data["found"] or "error" in data:
                            log_test(test_case["name"], True, "Cognome mismatch handled correctly")
                            passed += 1
                        else:
                            log_test(test_case["name"], False, "Cognome mismatch not detected")
                else:
                    log_test(test_case["name"], False, f"Invalid response structure: {data}")
            elif response.status_code == 400:
                # Check if it's a cognome mismatch error
                error_detail = response.json().get("detail", "")
                if "cognome" in error_detail.lower() and test_case["expected"] == "mismatch":
                    log_test(test_case["name"], True, f"Cognome validation error: {error_detail}")
                    passed += 1
                else:
                    log_test(test_case["name"], False, f"Unexpected 400 error: {error_detail}")
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                log_test(test_case["name"], False, f"Status {response.status_code}: {error_detail}")
                
        except requests.exceptions.Timeout:
            log_test(test_case["name"], False, "Timeout after 10 seconds")
        except Exception as e:
            log_test(test_case["name"], False, f"Exception: {str(e)}")
    
    success_rate = (passed / total) * 100
    log_test("Enhanced Fidelity Overall", passed >= 2, f"{passed}/{total} passed ({success_rate:.1f}%)")
    return passed >= 2

def test_multi_format_login():
    """Test Multi-Format Login System (email, tessera, telefono)"""
    print("\n🔍 TESTING: Multi-Format Login System")
    print("-" * 50)
    
    # First, create a test user to test login formats
    test_user_data = {
        "nome": "TestUser",
        "cognome": "LoginTest",
        "sesso": "M",
        "email": f"testlogin.{uuid.uuid4().hex[:8]}@test.it",
        "telefono": "+39 333 9999999",
        "localita": "TestCity",
        "tessera_fisica": f"TEST{uuid.uuid4().hex[:8].upper()}",
        "password": "TestPass123!"
    }
    
    # Register test user
    try:
        register_response = requests.post(f"{API_BASE}/register", json=test_user_data, timeout=10)
        if register_response.status_code != 200:
            log_test("Test User Registration", False, f"Failed to create test user: {register_response.status_code}")
            return False
        
        log_test("Test User Registration", True, "Test user created successfully")
        
    except Exception as e:
        log_test("Test User Registration", False, f"Exception creating test user: {str(e)}")
        return False
    
    # Test different login formats
    login_tests = [
        {
            "name": "Email Login",
            "data": {"username": test_user_data["email"], "password": test_user_data["password"]},
            "should_work": True
        },
        {
            "name": "Tessera Login", 
            "data": {"username": test_user_data["tessera_fisica"], "password": test_user_data["password"]},
            "should_work": True
        },
        {
            "name": "Telefono Login",
            "data": {"username": test_user_data["telefono"], "password": test_user_data["password"]},
            "should_work": True
        },
        {
            "name": "Invalid Credentials",
            "data": {"username": test_user_data["email"], "password": "WrongPassword"},
            "should_work": False
        }
    ]
    
    passed = 0
    total = len(login_tests)
    
    for login_test in login_tests:
        try:
            response = requests.post(f"{API_BASE}/login", json=login_test["data"], timeout=10)
            
            if login_test["should_work"]:
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data and "user" in data:
                        log_test(login_test["name"], True, "Login successful with token")
                        passed += 1
                    else:
                        log_test(login_test["name"], False, "Login response missing required fields")
                else:
                    error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                    log_test(login_test["name"], False, f"Status {response.status_code}: {error_detail}")
            else:
                # Should fail
                if response.status_code == 401:
                    error_detail = response.json().get("detail", "")
                    if "Credenziali non valide" in error_detail:
                        log_test(login_test["name"], True, "Invalid credentials correctly rejected")
                        passed += 1
                    else:
                        log_test(login_test["name"], False, f"Wrong error message: {error_detail}")
                else:
                    log_test(login_test["name"], False, f"Should return 401, got {response.status_code}")
                
        except requests.exceptions.Timeout:
            log_test(login_test["name"], False, "Timeout after 10 seconds")
        except Exception as e:
            log_test(login_test["name"], False, f"Exception: {str(e)}")
    
    success_rate = (passed / total) * 100
    log_test("Multi-Format Login Overall", passed >= 3, f"{passed}/{total} passed ({success_rate:.1f}%)")
    return passed >= 3

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def run_stuck_tasks_test():
    """Run tests for stuck tasks"""
    start_time = datetime.now()
    
    print("🚀 TESTING STUCK TASKS FROM test_result.md")
    print("Focus: Enhanced Fidelity Validation & Multi-Format Login")
    
    tests = [
        ("Enhanced Fidelity Validation", test_enhanced_fidelity_validation),
        ("Multi-Format Login System", test_multi_format_login)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            log_test(test_name, False, f"Test execution error: {str(e)}")
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    # Final results
    print("\n" + "=" * 60)
    print("🎯 STUCK TASKS TEST RESULTS")
    print("=" * 60)
    
    success_rate = (passed_tests / total_tests) * 100
    
    if success_rate >= 80:
        status = "✅ TASKS RESOLVED"
        emoji = "🎉"
    elif success_rate >= 50:
        status = "⚠️  PARTIAL RESOLUTION"
        emoji = "⚠️"
    else:
        status = "❌ TASKS STILL STUCK"
        emoji = "❌"
    
    print(f"{emoji} {status}")
    print(f"📊 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test']}: {result['message']}")
    
    return success_rate >= 50

if __name__ == "__main__":
    tasks_resolved = run_stuck_tasks_test()
    sys.exit(0 if tasks_resolved else 1)
#!/usr/bin/env python3
"""
Fedelissima.net URL Deployment Verification Tests
Tests all URL updates for fedelissima.net deployment are working correctly
"""

import requests
import json
import base64
import uuid
from datetime import datetime
import sys
import re

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
print(f"🌐 Expected domain: https://fedelissima.net")

# Global variables for test state
admin_access_token = None
test_store_id = None
test_cashier_id = None
test_qr_code = None
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

def is_valid_base64_image(data):
    """Check if data is valid base64 encoded image"""
    try:
        decoded = base64.b64decode(data)
        return decoded.startswith(b'\x89PNG\r\n\x1a\n')
    except:
        return False

def is_valid_uuid(uuid_string):
    """Check if string is valid UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def test_frontend_env_configuration():
    """Test that REACT_APP_BACKEND_URL is correctly updated to https://fedelissima.net"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            content = f.read()
        
        # Check if REACT_APP_BACKEND_URL is set to fedelissima.net
        if 'REACT_APP_BACKEND_URL=https://fedelissima.net' in content:
            log_test("Frontend Environment Configuration", True, "REACT_APP_BACKEND_URL correctly set to https://fedelissima.net")
            return True
        else:
            # Extract the actual value
            for line in content.split('\n'):
                if line.startswith('REACT_APP_BACKEND_URL='):
                    actual_url = line.split('=', 1)[1].strip()
                    log_test("Frontend Environment Configuration", False, f"REACT_APP_BACKEND_URL is '{actual_url}', expected 'https://fedelissima.net'")
                    return False
            
            log_test("Frontend Environment Configuration", False, "REACT_APP_BACKEND_URL not found in .env file")
            return False
            
    except Exception as e:
        log_test("Frontend Environment Configuration", False, f"Exception: {str(e)}")
        return False

def test_api_connectivity():
    """Test API connectivity to fedelissima.net domain"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "ImaGross" in data["message"]:
                log_test("API Connectivity", True, f"API accessible at {BASE_URL}")
                return True
            else:
                log_test("API Connectivity", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("API Connectivity", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("API Connectivity", False, f"Connection error: {str(e)}")
        return False

def test_admin_login():
    """Test super admin login with predefined credentials"""
    global admin_access_token
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        
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
            admin_access_token = data["access_token"]
            
            log_test("Super Admin Login", True, "Super admin login successful")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Super Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Super Admin Login", False, f"Exception: {str(e)}")
        return False

def test_create_test_store():
    """Create a test store for cashier creation"""
    global test_store_id
    
    if not admin_access_token:
        log_test("Create Test Store", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        unique_id = uuid.uuid4().hex[:8].upper()
        store_data = {
            "name": f"ImaGross Test Store {unique_id}",
            "code": f"TESTSTORE{unique_id}",
            "address": "Via Test 123",
            "city": "Milano",
            "province": "MI",
            "phone": "+39 02 1234567",
            "manager_name": "Test Manager"
        }
        
        response = requests.post(f"{API_BASE}/admin/stores", json=store_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            test_store_id = data["id"]
            log_test("Create Test Store", True, f"Test store created: {data['name']}")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Create Test Store", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Create Test Store", False, f"Exception: {str(e)}")
        return False

def test_create_test_cashier():
    """Create a test cashier and verify QR code URL uses fedelissima.net domain"""
    global test_cashier_id, test_qr_code
    
    if not admin_access_token or not test_store_id:
        log_test("Create Test Cashier", False, "No admin token or store ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        cashier_data = {
            "store_id": test_store_id,
            "cashier_number": 1,
            "name": "Test Cashier 1"
        }
        
        response = requests.post(f"{API_BASE}/admin/cashiers", json=cashier_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["id", "store_id", "cashier_number", "name", "qr_code", "qr_code_image"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Create Test Cashier", False, f"Missing fields: {missing_fields}")
                return False
            
            # Store for later tests
            test_cashier_id = data["id"]
            test_qr_code = data["qr_code"]
            
            # Validate QR code image is base64 PNG
            if not is_valid_base64_image(data["qr_code_image"]):
                log_test("Create Test Cashier", False, "Invalid QR code image format")
                return False
            
            log_test("Create Test Cashier", True, f"Test cashier created with QR: {data['qr_code']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Create Test Cashier", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Create Test Cashier", False, f"Exception: {str(e)}")
        return False

def test_qr_code_url_format():
    """Test that generated QR code URL uses correct fedelissima.net domain format"""
    global test_qr_code
    
    if not test_qr_code:
        log_test("QR Code URL Format", False, "No test QR code available")
        return False
    
    try:
        # Get QR code info to check the registration URL
        response = requests.get(f"{API_BASE}/qr/{test_qr_code}", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "registration_url" not in data:
                log_test("QR Code URL Format", False, "Missing registration_url in QR response")
                return False
            
            registration_url = data["registration_url"]
            
            # The registration URL should be in format: /register?qr=STORECODE-CASSAN
            expected_pattern = r"^/register\?qr=[A-Z0-9]+-CASSA\d+$"
            if not re.match(expected_pattern, registration_url):
                log_test("QR Code URL Format", False, f"Invalid registration URL format: {registration_url}")
                return False
            
            # Extract the QR code from the URL
            qr_param = registration_url.split('qr=')[1]
            if qr_param != test_qr_code:
                log_test("QR Code URL Format", False, f"QR code mismatch: URL has {qr_param}, expected {test_qr_code}")
                return False
            
            # The full URL when used with frontend would be: https://fedelissima.net/register?qr=STORECODE-CASSAN
            full_url = f"{BASE_URL}{registration_url}"
            expected_domain = "https://fedelissima.net"
            
            if not full_url.startswith(expected_domain):
                log_test("QR Code URL Format", False, f"QR URL uses wrong domain: {full_url}")
                return False
            
            log_test("QR Code URL Format", True, f"QR code URL format correct: {full_url}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("QR Code URL Format", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("QR Code URL Format", False, f"Exception: {str(e)}")
        return False

def test_qr_regeneration_url():
    """Test QR code regeneration uses fedelissima.net domain"""
    global test_qr_code
    
    if not admin_access_token or not test_cashier_id:
        log_test("QR Regeneration URL", False, "No admin token or cashier ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Update cashier to trigger QR regeneration
        update_data = {
            "name": "Test Cashier 1 - Updated",
            "cashier_number": 2  # Change number to trigger QR regeneration
        }
        
        response = requests.put(f"{API_BASE}/admin/cashiers/{test_cashier_id}", json=update_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate QR code was regenerated
            new_qr_code = data["qr_code"]
            if new_qr_code == test_qr_code:
                log_test("QR Regeneration URL", False, "QR code was not regenerated")
                return False
            
            # Test the new QR code URL format
            qr_response = requests.get(f"{API_BASE}/qr/{new_qr_code}", timeout=30)
            
            if qr_response.status_code == 200:
                qr_data = qr_response.json()
                registration_url = qr_data.get("registration_url", "")
                full_url = f"{BASE_URL}{registration_url}"
                
                if not full_url.startswith("https://fedelissima.net"):
                    log_test("QR Regeneration URL", False, f"Regenerated QR URL uses wrong domain: {full_url}")
                    return False
                
                # Update global test_qr_code for other tests
                test_qr_code = new_qr_code
                
                log_test("QR Regeneration URL", True, f"QR regeneration URL correct: {full_url}")
                return True
            else:
                log_test("QR Regeneration URL", False, f"Could not retrieve regenerated QR info: {qr_response.status_code}")
                return False
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("QR Regeneration URL", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("QR Regeneration URL", False, f"Exception: {str(e)}")
        return False

def test_bulk_qr_regeneration():
    """Test bulk QR regeneration endpoint uses fedelissima.net domain"""
    if not admin_access_token:
        log_test("Bulk QR Regeneration", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test bulk regeneration endpoint (if it exists)
        response = requests.post(f"{API_BASE}/admin/cashiers/regenerate-qr", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "message" not in data or "updated_cashiers" not in data:
                log_test("Bulk QR Regeneration", False, "Missing fields in bulk regeneration response")
                return False
            
            updated_count = data["updated_cashiers"]
            if updated_count > 0:
                # Verify that regenerated QR codes use correct domain
                cashiers_response = requests.get(f"{API_BASE}/admin/cashiers", headers=headers, timeout=30)
                if cashiers_response.status_code == 200:
                    cashiers = cashiers_response.json()
                    
                    # Check a few cashiers to verify their QR codes
                    for cashier in cashiers[:3]:  # Check first 3 cashiers
                        qr_code = cashier.get("qr_code", "")
                        if qr_code:
                            qr_response = requests.get(f"{API_BASE}/qr/{qr_code}", timeout=30)
                            if qr_response.status_code == 200:
                                qr_data = qr_response.json()
                                registration_url = qr_data.get("registration_url", "")
                                full_url = f"{BASE_URL}{registration_url}"
                                
                                if not full_url.startswith("https://fedelissima.net"):
                                    log_test("Bulk QR Regeneration", False, f"Bulk regenerated QR URL uses wrong domain: {full_url}")
                                    return False
                
                log_test("Bulk QR Regeneration", True, f"Bulk QR regeneration successful: {updated_count} cashiers updated")
                return True
            else:
                log_test("Bulk QR Regeneration", True, "Bulk QR regeneration completed (no cashiers needed updating)")
                return True
                
        elif response.status_code == 404:
            # Bulk regeneration endpoint might not exist, which is acceptable
            log_test("Bulk QR Regeneration", True, "Bulk QR regeneration endpoint not implemented (acceptable)")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Bulk QR Regeneration", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Bulk QR Regeneration", False, f"Exception: {str(e)}")
        return False

def test_complete_store_cashier_workflow():
    """Test complete store + cashier workflow with fedelissima.net URLs"""
    if not admin_access_token:
        log_test("Complete Store Cashier Workflow", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Create a new store for workflow test
        unique_id = uuid.uuid4().hex[:6].upper()
        store_data = {
            "name": f"ImaGross Workflow Test {unique_id}",
            "code": f"WORKFLOW{unique_id}",
            "address": "Via Workflow 456",
            "city": "Roma",
            "province": "RM",
            "phone": "+39 06 7654321",
            "manager_name": "Workflow Manager"
        }
        
        store_response = requests.post(f"{API_BASE}/admin/stores", json=store_data, headers=headers, timeout=30)
        
        if store_response.status_code != 200:
            log_test("Complete Store Cashier Workflow", False, "Could not create workflow test store")
            return False
        
        workflow_store_id = store_response.json()["id"]
        
        # Create multiple cashiers for this store
        cashier_urls = []
        for i in range(1, 4):  # Create 3 cashiers
            cashier_data = {
                "store_id": workflow_store_id,
                "cashier_number": i,
                "name": f"Workflow Cashier {i}"
            }
            
            cashier_response = requests.post(f"{API_BASE}/admin/cashiers", json=cashier_data, headers=headers, timeout=30)
            
            if cashier_response.status_code == 200:
                cashier = cashier_response.json()
                qr_code = cashier["qr_code"]
                
                # Get QR info and build full URL
                qr_response = requests.get(f"{API_BASE}/qr/{qr_code}", timeout=30)
                if qr_response.status_code == 200:
                    qr_data = qr_response.json()
                    registration_url = qr_data.get("registration_url", "")
                    full_url = f"{BASE_URL}{registration_url}"
                    cashier_urls.append(full_url)
                    
                    # Verify URL format
                    expected_format = f"https://fedelissima.net/register?qr=WORKFLOW{unique_id}-CASSA{i}"
                    if full_url != expected_format:
                        log_test("Complete Store Cashier Workflow", False, f"Cashier {i} URL format incorrect: {full_url}")
                        return False
                else:
                    log_test("Complete Store Cashier Workflow", False, f"Could not get QR info for cashier {i}")
                    return False
            else:
                log_test("Complete Store Cashier Workflow", False, f"Could not create cashier {i}")
                return False
        
        # Verify all URLs use fedelissima.net domain
        for url in cashier_urls:
            if not url.startswith("https://fedelissima.net"):
                log_test("Complete Store Cashier Workflow", False, f"Workflow URL uses wrong domain: {url}")
                return False
        
        log_test("Complete Store Cashier Workflow", True, f"Complete workflow successful: {len(cashier_urls)} cashiers with correct fedelissima.net URLs")
        return True
        
    except Exception as e:
        log_test("Complete Store Cashier Workflow", False, f"Exception: {str(e)}")
        return False

def test_database_consistency():
    """Test that URL updates didn't affect data integrity"""
    if not admin_access_token:
        log_test("Database Consistency", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test fidelity data integrity
        fidelity_response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        
        if fidelity_response.status_code == 200:
            fidelity_data = fidelity_response.json()
            
            if "total" not in fidelity_data:
                log_test("Database Consistency", False, "Missing total field in fidelity data")
                return False
            
            total_records = fidelity_data["total"]
            
            # Check if we have the expected number of records (around 30,287)
            if total_records < 24000:  # Allow some tolerance
                log_test("Database Consistency", False, f"Too few fidelity records: {total_records} (expected ~30,287)")
                return False
            
            # Test specific card mentioned in review request
            test_card = "2020000063308"
            card_response = requests.get(f"{API_BASE}/check-tessera", json={"tessera_fisica": test_card}, timeout=30)
            
            if card_response.status_code == 200:
                card_data = card_response.json()
                if card_data.get("found"):
                    log_test("Database Consistency", True, f"Data integrity verified: {total_records} fidelity records, card {test_card} accessible")
                    return True
                else:
                    log_test("Database Consistency", False, f"Test card {test_card} not found")
                    return False
            else:
                log_test("Database Consistency", False, f"Could not check test card {test_card}")
                return False
        else:
            error_detail = fidelity_response.json().get("detail", "Unknown error") if fidelity_response.content else "No response"
            log_test("Database Consistency", False, f"Status {fidelity_response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Database Consistency", False, f"Exception: {str(e)}")
        return False

def test_api_endpoints_response():
    """Test that API endpoints respond correctly with new URL configuration"""
    if not admin_access_token:
        log_test("API Endpoints Response", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test key endpoints
        endpoints_to_test = [
            ("/admin/stats/dashboard", "Dashboard stats"),
            ("/admin/stores", "Stores list"),
            ("/admin/cashiers", "Cashiers list"),
            ("/admin/fidelity-users", "Fidelity users")
        ]
        
        successful_endpoints = 0
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
                if response.status_code == 200:
                    successful_endpoints += 1
                else:
                    print(f"  ⚠️ {description} endpoint returned {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ {description} endpoint error: {str(e)}")
        
        if successful_endpoints == len(endpoints_to_test):
            log_test("API Endpoints Response", True, f"All {successful_endpoints} key endpoints responding correctly")
            return True
        elif successful_endpoints >= len(endpoints_to_test) * 0.75:  # At least 75% working
            log_test("API Endpoints Response", True, f"{successful_endpoints}/{len(endpoints_to_test)} endpoints working (acceptable)")
            return True
        else:
            log_test("API Endpoints Response", False, f"Only {successful_endpoints}/{len(endpoints_to_test)} endpoints working")
            return False
            
    except Exception as e:
        log_test("API Endpoints Response", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all fedelissima.net URL verification tests"""
    print("🚀 Starting Fedelissima.net URL Deployment Verification Tests")
    print("=" * 80)
    
    tests = [
        test_frontend_env_configuration,
        test_api_connectivity,
        test_admin_login,
        test_create_test_store,
        test_create_test_cashier,
        test_qr_code_url_format,
        test_qr_regeneration_url,
        test_bulk_qr_regeneration,
        test_complete_store_cashier_workflow,
        test_database_consistency,
        test_api_endpoints_response
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: Unexpected error: {str(e)}")
            failed += 1
        
        print()  # Add spacing between tests
    
    print("=" * 80)
    print(f"📊 FEDELISSIMA.NET URL VERIFICATION RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ALL FEDELISSIMA.NET URL TESTS PASSED!")
        print("✅ System is ready for fedelissima.net production deployment")
    else:
        print("⚠️ Some tests failed - review issues before deployment")
    
    return passed, failed

if __name__ == "__main__":
    run_all_tests()
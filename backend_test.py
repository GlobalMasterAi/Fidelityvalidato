#!/usr/bin/env python3
"""
ImaGross Loyalty System Backend API Tests
Tests all backend endpoints for the loyalty system
"""

import requests
import json
import base64
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
print(f"🔗 Testing API at: {API_BASE}")

# Test data - realistic Italian data for ImaGross
TEST_USER_DATA = {
    "nome": "Marco",
    "cognome": "Rossi", 
    "sesso": "M",
    "email": "marco.rossi@email.it",
    "telefono": "+39 333 1234567",
    "localita": "Milano",
    "tessera_fisica": "IMG001234567",
    "password": "SecurePass123!"
}

TEST_USER_DATA_2 = {
    "nome": "Giulia",
    "cognome": "Bianchi",
    "sesso": "F", 
    "email": "giulia.bianchi@email.it",
    "telefono": "+39 347 9876543",
    "localita": "Roma",
    "tessera_fisica": "IMG007654321",
    "password": "MyPassword456!"
}

# Global variables for test state
access_token = None
user_id = None
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
        # Check if it starts with PNG header
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

def test_api_root():
    """Test API root endpoint"""
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "ImaGross" in data["message"]:
                log_test("API Root", True, "API is accessible")
                return True
            else:
                log_test("API Root", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("API Root", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("API Root", False, f"Connection error: {str(e)}")
        return False

def test_user_registration():
    """Test user registration with all required fields"""
    global user_id
    
    try:
        response = requests.post(f"{API_BASE}/register", json=TEST_USER_DATA)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["id", "nome", "cognome", "sesso", "email", "telefono", 
                             "localita", "tessera_fisica", "tessera_digitale", "punti", 
                             "created_at", "qr_code"]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("User Registration", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data types and values
            if not is_valid_uuid(data["id"]):
                log_test("User Registration", False, "Invalid user ID format")
                return False
                
            if not is_valid_uuid(data["tessera_digitale"]):
                log_test("User Registration", False, "Invalid tessera_digitale format")
                return False
                
            if data["punti"] != 0:
                log_test("User Registration", False, f"Initial points should be 0, got {data['punti']}")
                return False
                
            if not is_valid_base64_image(data["qr_code"]):
                log_test("User Registration", False, "Invalid QR code format")
                return False
            
            # Store user ID for later tests
            user_id = data["id"]
            
            log_test("User Registration", True, f"User registered successfully with ID: {user_id}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Registration", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Registration", False, f"Exception: {str(e)}")
        return False

def test_duplicate_email_validation():
    """Test duplicate email validation"""
    try:
        # Try to register with same email
        duplicate_data = TEST_USER_DATA.copy()
        duplicate_data["tessera_fisica"] = "IMG999999999"  # Different tessera
        
        response = requests.post(f"{API_BASE}/register", json=duplicate_data)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "Email già registrata" in error_detail:
                log_test("Duplicate Email Validation", True, "Correctly rejected duplicate email")
                return True
            else:
                log_test("Duplicate Email Validation", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Duplicate Email Validation", False, f"Should return 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate Email Validation", False, f"Exception: {str(e)}")
        return False

def test_duplicate_tessera_validation():
    """Test duplicate tessera fisica validation"""
    try:
        # Try to register with same tessera fisica
        duplicate_data = TEST_USER_DATA.copy()
        duplicate_data["email"] = "different@email.it"  # Different email
        
        response = requests.post(f"{API_BASE}/register", json=duplicate_data)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "Tessera fisica già registrata" in error_detail:
                log_test("Duplicate Tessera Validation", True, "Correctly rejected duplicate tessera")
                return True
            else:
                log_test("Duplicate Tessera Validation", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Duplicate Tessera Validation", False, f"Should return 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate Tessera Validation", False, f"Exception: {str(e)}")
        return False

def test_user_login():
    """Test user login with valid credentials"""
    global access_token
    
    try:
        login_data = {
            "email": TEST_USER_DATA["email"],
            "password": TEST_USER_DATA["password"]
        }
        
        response = requests.post(f"{API_BASE}/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "access_token" not in data or "token_type" not in data or "user" not in data:
                log_test("User Login", False, "Missing required fields in login response")
                return False
            
            if data["token_type"] != "bearer":
                log_test("User Login", False, f"Wrong token type: {data['token_type']}")
                return False
            
            # Validate user data in response
            user_data = data["user"]
            if user_data["email"] != TEST_USER_DATA["email"]:
                log_test("User Login", False, "User data mismatch in login response")
                return False
                
            if not is_valid_base64_image(user_data["qr_code"]):
                log_test("User Login", False, "Invalid QR code in login response")
                return False
            
            # Store access token for authenticated requests
            access_token = data["access_token"]
            
            log_test("User Login", True, "Login successful with JWT token")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Login", False, f"Exception: {str(e)}")
        return False

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    try:
        login_data = {
            "email": TEST_USER_DATA["email"],
            "password": "WrongPassword123"
        }
        
        response = requests.post(f"{API_BASE}/login", json=login_data)
        
        if response.status_code == 401:
            error_detail = response.json().get("detail", "")
            if "Credenziali non valide" in error_detail:
                log_test("Invalid Login Credentials", True, "Correctly rejected invalid credentials")
                return True
            else:
                log_test("Invalid Login Credentials", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Invalid Login Credentials", False, f"Should return 401, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Invalid Login Credentials", False, f"Exception: {str(e)}")
        return False

def test_user_profile():
    """Test authenticated user profile access"""
    if not access_token:
        log_test("User Profile", False, "No access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_BASE}/profile", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["id", "nome", "cognome", "sesso", "email", "telefono", 
                             "localita", "tessera_fisica", "tessera_digitale", "punti", 
                             "created_at", "qr_code"]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("User Profile", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate user data matches registration
            if data["email"] != TEST_USER_DATA["email"]:
                log_test("User Profile", False, "Profile data doesn't match registered user")
                return False
                
            if not is_valid_base64_image(data["qr_code"]):
                log_test("User Profile", False, "Invalid QR code in profile")
                return False
            
            log_test("User Profile", True, "Profile retrieved successfully with QR code")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Profile", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Profile", False, f"Exception: {str(e)}")
        return False

def test_profile_unauthorized():
    """Test profile access without authentication"""
    try:
        response = requests.get(f"{API_BASE}/profile")
        
        if response.status_code == 403:
            log_test("Profile Unauthorized", True, "Correctly rejected unauthenticated request")
            return True
        else:
            log_test("Profile Unauthorized", False, f"Should return 403, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Profile Unauthorized", False, f"Exception: {str(e)}")
        return False

def test_add_points():
    """Test adding points to user account"""
    if not access_token:
        log_test("Add Points", False, "No access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        points_to_add = 50
        
        response = requests.post(f"{API_BASE}/add-points/{points_to_add}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if "message" not in data or "punti_totali" not in data:
                log_test("Add Points", False, "Missing fields in add points response")
                return False
            
            if data["punti_totali"] != points_to_add:  # Should be 50 since user started with 0
                log_test("Add Points", False, f"Points calculation error: expected {points_to_add}, got {data['punti_totali']}")
                return False
            
            log_test("Add Points", True, f"Successfully added {points_to_add} points")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Add Points", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Add Points", False, f"Exception: {str(e)}")
        return False

def test_digital_card_generation():
    """Test unique tessera_digitale generation"""
    try:
        # Register second user to test uniqueness
        response = requests.post(f"{API_BASE}/register", json=TEST_USER_DATA_2)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check tessera_digitale is different from first user
            if user_id and data["tessera_digitale"] == user_id:
                log_test("Digital Card Generation", False, "tessera_digitale not unique")
                return False
            
            if not is_valid_uuid(data["tessera_digitale"]):
                log_test("Digital Card Generation", False, "Invalid tessera_digitale format")
                return False
                
            if not is_valid_base64_image(data["qr_code"]):
                log_test("Digital Card Generation", False, "Invalid QR code generation")
                return False
            
            log_test("Digital Card Generation", True, "Unique tessera_digitale and QR code generated")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Digital Card Generation", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Digital Card Generation", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all backend API tests"""
    print("🚀 Starting ImaGross Loyalty System Backend API Tests")
    print("=" * 60)
    
    # Test API connectivity first
    if not test_api_root():
        print("❌ API not accessible, stopping tests")
        return False
    
    # Core functionality tests
    tests = [
        test_user_registration,
        test_duplicate_email_validation, 
        test_duplicate_tessera_validation,
        test_user_login,
        test_login_invalid_credentials,
        test_user_profile,
        test_profile_unauthorized,
        test_add_points,
        test_digital_card_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend API is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
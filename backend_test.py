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

# ============================================================================
# SUPER ADMIN AUTHENTICATION SYSTEM TESTS
# ============================================================================

# Global variables for admin tests
admin_access_token = None
admin_user_id = None
test_store_id = None
test_cashier_id = None
test_qr_code = None

def test_admin_login():
    """Test super admin login with predefined credentials"""
    global admin_access_token, admin_user_id
    
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
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
            admin_user_id = admin_data["id"]
            
            log_test("Super Admin Login", True, "Super admin login successful")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Super Admin Login", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Super Admin Login", False, f"Exception: {str(e)}")
        return False

def test_admin_login_invalid():
    """Test admin login with invalid credentials"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "WrongPassword123"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 401:
            error_detail = response.json().get("detail", "")
            if "Credenziali non valide" in error_detail:
                log_test("Admin Invalid Login", True, "Correctly rejected invalid admin credentials")
                return True
            else:
                log_test("Admin Invalid Login", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Admin Invalid Login", False, f"Should return 401, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Admin Invalid Login", False, f"Exception: {str(e)}")
        return False

def test_create_admin_user():
    """Test creating new admin user by super admin"""
    if not admin_access_token:
        log_test("Create Admin User", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        admin_data = {
            "username": "testadmin",
            "email": "testadmin@imagross.it",
            "password": "TestAdmin123!",
            "full_name": "Test Administrator",
            "role": "admin"
        }
        
        response = requests.post(f"{API_BASE}/admin/create", json=admin_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if "message" not in data or "admin_id" not in data:
                log_test("Create Admin User", False, "Missing fields in create admin response")
                return False
            
            if not is_valid_uuid(data["admin_id"]):
                log_test("Create Admin User", False, "Invalid admin ID format")
                return False
            
            log_test("Create Admin User", True, f"Admin user created successfully: {data['admin_id']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Create Admin User", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Create Admin User", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# STORE MANAGEMENT API TESTS
# ============================================================================

def test_create_store():
    """Test store creation with all required fields"""
    global test_store_id
    
    if not admin_access_token:
        log_test("Create Store", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        store_data = {
            "name": "ImaGross Milano Centro",
            "code": "IMAGROSS001",
            "address": "Via Roma 123",
            "city": "Milano",
            "province": "MI",
            "phone": "+39 02 1234567",
            "manager_name": "Giuseppe Verdi"
        }
        
        response = requests.post(f"{API_BASE}/admin/stores", json=store_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["id", "name", "code", "address", "city", "province", "phone", "status", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Create Store", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data matches input
            if data["name"] != store_data["name"] or data["code"] != store_data["code"]:
                log_test("Create Store", False, "Store data mismatch")
                return False
            
            if not is_valid_uuid(data["id"]):
                log_test("Create Store", False, "Invalid store ID format")
                return False
            
            if data["status"] != "active":
                log_test("Create Store", False, f"Wrong default status: {data['status']}")
                return False
            
            # Store ID for later tests
            test_store_id = data["id"]
            
            log_test("Create Store", True, f"Store created successfully: {data['name']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Create Store", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Create Store", False, f"Exception: {str(e)}")
        return False

def test_duplicate_store_code():
    """Test unique store code validation"""
    if not admin_access_token:
        log_test("Duplicate Store Code", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        store_data = {
            "name": "ImaGross Milano Sud",
            "code": "IMAGROSS001",  # Same code as previous store
            "address": "Via Torino 456",
            "city": "Milano",
            "province": "MI",
            "phone": "+39 02 7654321"
        }
        
        response = requests.post(f"{API_BASE}/admin/stores", json=store_data, headers=headers)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "Codice supermercato già esistente" in error_detail:
                log_test("Duplicate Store Code", True, "Correctly rejected duplicate store code")
                return True
            else:
                log_test("Duplicate Store Code", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Duplicate Store Code", False, f"Should return 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate Store Code", False, f"Exception: {str(e)}")
        return False

def test_get_stores():
    """Test store retrieval"""
    if not admin_access_token:
        log_test("Get Stores", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stores", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                log_test("Get Stores", False, "Response should be a list")
                return False
            
            if len(data) == 0:
                log_test("Get Stores", False, "No stores found")
                return False
            
            # Validate first store structure
            store = data[0]
            required_fields = ["id", "name", "code", "address", "city", "province", "phone", "status"]
            missing_fields = [field for field in required_fields if field not in store]
            if missing_fields:
                log_test("Get Stores", False, f"Missing fields in store: {missing_fields}")
                return False
            
            log_test("Get Stores", True, f"Retrieved {len(data)} stores successfully")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Get Stores", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Get Stores", False, f"Exception: {str(e)}")
        return False

def test_update_store():
    """Test store update functionality"""
    if not admin_access_token or not test_store_id:
        log_test("Update Store", False, "No admin token or store ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        update_data = {
            "name": "ImaGross Milano Centro - Updated",
            "code": "IMAGROSS001",
            "address": "Via Roma 123 - Updated",
            "city": "Milano",
            "province": "MI",
            "phone": "+39 02 1234567",
            "manager_name": "Giuseppe Verdi - Updated"
        }
        
        response = requests.put(f"{API_BASE}/admin/stores/{test_store_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["name"] != update_data["name"]:
                log_test("Update Store", False, "Store name not updated")
                return False
            
            if data["address"] != update_data["address"]:
                log_test("Update Store", False, "Store address not updated")
                return False
            
            if "updated_at" not in data:
                log_test("Update Store", False, "Missing updated_at field")
                return False
            
            log_test("Update Store", True, "Store updated successfully")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Update Store", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Update Store", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# CASHIER MANAGEMENT API TESTS
# ============================================================================

def test_create_cashier():
    """Test cashier creation linked to specific store"""
    global test_cashier_id, test_qr_code
    
    if not admin_access_token or not test_store_id:
        log_test("Create Cashier", False, "No admin token or store ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        cashier_data = {
            "store_id": test_store_id,
            "cashier_number": 1,
            "name": "Cassa 1 - Principale"
        }
        
        response = requests.post(f"{API_BASE}/admin/cashiers", json=cashier_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["id", "store_id", "cashier_number", "name", "qr_code", "qr_code_image", "is_active", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Create Cashier", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data matches input
            if data["store_id"] != test_store_id or data["cashier_number"] != 1:
                log_test("Create Cashier", False, "Cashier data mismatch")
                return False
            
            if not is_valid_uuid(data["id"]):
                log_test("Create Cashier", False, "Invalid cashier ID format")
                return False
            
            # Validate QR code format (STORE_CODE-CASSANUMBER)
            if not data["qr_code"].startswith("IMAGROSS001-CASSA1"):
                log_test("Create Cashier", False, f"Wrong QR code format: {data['qr_code']}")
                return False
            
            # Validate QR code image is base64 PNG
            if not is_valid_base64_image(data["qr_code_image"]):
                log_test("Create Cashier", False, "Invalid QR code image format")
                return False
            
            if not data["is_active"]:
                log_test("Create Cashier", False, "Cashier should be active by default")
                return False
            
            # Store for later tests
            test_cashier_id = data["id"]
            test_qr_code = data["qr_code"]
            
            log_test("Create Cashier", True, f"Cashier created with QR: {data['qr_code']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Create Cashier", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Create Cashier", False, f"Exception: {str(e)}")
        return False

def test_duplicate_cashier_number():
    """Test unique cashier number per store validation"""
    if not admin_access_token or not test_store_id:
        log_test("Duplicate Cashier Number", False, "No admin token or store ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        cashier_data = {
            "store_id": test_store_id,
            "cashier_number": 1,  # Same number as previous cashier
            "name": "Cassa 1 - Duplicata"
        }
        
        response = requests.post(f"{API_BASE}/admin/cashiers", json=cashier_data, headers=headers)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "Numero cassa già esistente" in error_detail:
                log_test("Duplicate Cashier Number", True, "Correctly rejected duplicate cashier number")
                return True
            else:
                log_test("Duplicate Cashier Number", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("Duplicate Cashier Number", False, f"Should return 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Duplicate Cashier Number", False, f"Exception: {str(e)}")
        return False

def test_get_store_cashiers():
    """Test cashier retrieval by store"""
    if not admin_access_token or not test_store_id:
        log_test("Get Store Cashiers", False, "No admin token or store ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stores/{test_store_id}/cashiers", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                log_test("Get Store Cashiers", False, "Response should be a list")
                return False
            
            if len(data) == 0:
                log_test("Get Store Cashiers", False, "No cashiers found for store")
                return False
            
            # Validate first cashier structure
            cashier = data[0]
            required_fields = ["id", "store_id", "cashier_number", "name", "qr_code", "qr_code_image"]
            missing_fields = [field for field in required_fields if field not in cashier]
            if missing_fields:
                log_test("Get Store Cashiers", False, f"Missing fields in cashier: {missing_fields}")
                return False
            
            log_test("Get Store Cashiers", True, f"Retrieved {len(data)} cashiers for store")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Get Store Cashiers", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Get Store Cashiers", False, f"Exception: {str(e)}")
        return False

def test_get_all_cashiers():
    """Test cashier retrieval globally"""
    if not admin_access_token:
        log_test("Get All Cashiers", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/cashiers", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                log_test("Get All Cashiers", False, "Response should be a list")
                return False
            
            if len(data) == 0:
                log_test("Get All Cashiers", False, "No cashiers found")
                return False
            
            # Validate first cashier structure with store name
            cashier = data[0]
            required_fields = ["id", "store_id", "cashier_number", "name", "qr_code", "store_name"]
            missing_fields = [field for field in required_fields if field not in cashier]
            if missing_fields:
                log_test("Get All Cashiers", False, f"Missing fields in cashier: {missing_fields}")
                return False
            
            if not cashier["store_name"]:
                log_test("Get All Cashiers", False, "Store name not populated")
                return False
            
            log_test("Get All Cashiers", True, f"Retrieved {len(data)} cashiers globally with store names")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Get All Cashiers", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Get All Cashiers", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# QR CODE GENERATION AND REGISTRATION FLOW TESTS
# ============================================================================

def test_qr_info_retrieval():
    """Test /api/qr/{qr_code} endpoint for cashier info retrieval"""
    if not test_qr_code:
        log_test("QR Info Retrieval", False, "No test QR code available")
        return False
    
    try:
        response = requests.get(f"{API_BASE}/qr/{test_qr_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["store", "cashier", "registration_url"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("QR Info Retrieval", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate store data
            store = data["store"]
            if not store or "name" not in store or "code" not in store:
                log_test("QR Info Retrieval", False, "Invalid store data in QR response")
                return False
            
            # Validate cashier data
            cashier = data["cashier"]
            if not cashier or "name" not in cashier or "cashier_number" not in cashier:
                log_test("QR Info Retrieval", False, "Invalid cashier data in QR response")
                return False
            
            # Validate registration URL
            if not data["registration_url"].startswith("/register?qr="):
                log_test("QR Info Retrieval", False, f"Invalid registration URL: {data['registration_url']}")
                return False
            
            log_test("QR Info Retrieval", True, f"QR info retrieved: {store['name']} - {cashier['name']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("QR Info Retrieval", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("QR Info Retrieval", False, f"Exception: {str(e)}")
        return False

def test_qr_invalid_code():
    """Test QR info retrieval with invalid code"""
    try:
        response = requests.get(f"{API_BASE}/qr/INVALID-QR-CODE")
        
        if response.status_code == 404:
            error_detail = response.json().get("detail", "")
            if "QR code not found" in error_detail:
                log_test("QR Invalid Code", True, "Correctly rejected invalid QR code")
                return True
            else:
                log_test("QR Invalid Code", False, f"Wrong error message: {error_detail}")
                return False
        else:
            log_test("QR Invalid Code", False, f"Should return 404, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("QR Invalid Code", False, f"Exception: {str(e)}")
        return False

def test_user_registration_with_qr():
    """Test user registration via QR code with store/cashier context"""
    if not test_store_id or not test_cashier_id:
        log_test("User Registration with QR", False, "No store/cashier ID available")
        return False
    
    try:
        user_data = {
            "nome": "Anna",
            "cognome": "Verdi",
            "sesso": "F",
            "email": "anna.verdi@email.it",
            "telefono": "+39 345 6789012",
            "localita": "Milano",
            "tessera_fisica": "IMG002345678",
            "password": "AnnaPass123!",
            "store_id": test_store_id,
            "cashier_id": test_cashier_id
        }
        
        response = requests.post(f"{API_BASE}/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response includes store/cashier context
            if "store_name" not in data or "cashier_name" not in data:
                log_test("User Registration with QR", False, "Missing store/cashier context in response")
                return False
            
            if not data["store_name"] or not data["cashier_name"]:
                log_test("User Registration with QR", False, "Store/cashier names not populated")
                return False
            
            # Validate standard user fields
            required_fields = ["id", "nome", "cognome", "email", "tessera_digitale", "qr_code"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("User Registration with QR", False, f"Missing fields: {missing_fields}")
                return False
            
            log_test("User Registration with QR", True, f"User registered via QR: {data['store_name']} - {data['cashier_name']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("User Registration with QR", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("User Registration with QR", False, f"Exception: {str(e)}")
        return False

def test_cashier_registration_count():
    """Test registration count increment for cashiers"""
    if not admin_access_token or not test_cashier_id:
        log_test("Cashier Registration Count", False, "No admin token or cashier ID available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/cashiers", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find our test cashier
            test_cashier = None
            for cashier in data:
                if cashier["id"] == test_cashier_id:
                    test_cashier = cashier
                    break
            
            if not test_cashier:
                log_test("Cashier Registration Count", False, "Test cashier not found")
                return False
            
            # Check if registration count was incremented
            if "total_registrations" not in test_cashier:
                log_test("Cashier Registration Count", False, "Missing total_registrations field")
                return False
            
            if test_cashier["total_registrations"] < 1:
                log_test("Cashier Registration Count", False, f"Registration count not incremented: {test_cashier['total_registrations']}")
                return False
            
            log_test("Cashier Registration Count", True, f"Registration count: {test_cashier['total_registrations']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Cashier Registration Count", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Cashier Registration Count", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# ADMIN DASHBOARD STATISTICS API TESTS
# ============================================================================

def test_dashboard_statistics():
    """Test /admin/stats/dashboard endpoint"""
    if not admin_access_token:
        log_test("Dashboard Statistics", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["total_users", "total_stores", "total_cashiers", "total_transactions", 
                             "recent_registrations", "total_points_distributed"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Dashboard Statistics", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data types
            for field in required_fields:
                if not isinstance(data[field], int):
                    log_test("Dashboard Statistics", False, f"Field {field} should be integer, got {type(data[field])}")
                    return False
            
            # Validate logical values
            if data["total_users"] < 0 or data["total_stores"] < 0 or data["total_cashiers"] < 0:
                log_test("Dashboard Statistics", False, "Negative values in statistics")
                return False
            
            # We should have at least the data we created in tests
            if data["total_stores"] < 1:
                log_test("Dashboard Statistics", False, "Should have at least 1 store")
                return False
            
            if data["total_cashiers"] < 1:
                log_test("Dashboard Statistics", False, "Should have at least 1 cashier")
                return False
            
            log_test("Dashboard Statistics", True, f"Stats: {data['total_users']} users, {data['total_stores']} stores, {data['total_cashiers']} cashiers")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Dashboard Statistics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Dashboard Statistics", False, f"Exception: {str(e)}")
        return False

def test_stores_statistics():
    """Test /admin/stats/stores endpoint"""
    if not admin_access_token:
        log_test("Stores Statistics", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = requests.get(f"{API_BASE}/admin/stats/stores", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                log_test("Stores Statistics", False, "Response should be a list")
                return False
            
            if len(data) == 0:
                log_test("Stores Statistics", False, "No store statistics found")
                return False
            
            # Validate first store statistics
            store_stats = data[0]
            required_fields = ["id", "name", "code", "users_registered", "active_cashiers"]
            missing_fields = [field for field in required_fields if field not in store_stats]
            if missing_fields:
                log_test("Stores Statistics", False, f"Missing fields in store stats: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(store_stats["users_registered"], int) or not isinstance(store_stats["active_cashiers"], int):
                log_test("Stores Statistics", False, "Invalid data types in store statistics")
                return False
            
            log_test("Stores Statistics", True, f"Store stats: {store_stats['users_registered']} users, {store_stats['active_cashiers']} cashiers")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Stores Statistics", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Stores Statistics", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

def test_admin_endpoints_without_auth():
    """Test admin endpoints require authentication"""
    endpoints_to_test = [
        "/admin/stores",
        "/admin/cashiers", 
        "/admin/stats/dashboard"
    ]
    
    all_passed = True
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            
            if response.status_code != 403:
                log_test(f"Auth Required - {endpoint}", False, f"Should return 403, got {response.status_code}")
                all_passed = False
            else:
                log_test(f"Auth Required - {endpoint}", True, "Correctly requires authentication")
                
        except Exception as e:
            log_test(f"Auth Required - {endpoint}", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_super_admin_only_endpoints():
    """Test super admin only endpoints"""
    if not admin_access_token:
        log_test("Super Admin Only", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Test creating admin (super admin only)
        admin_data = {
            "username": "testadmin2",
            "email": "testadmin2@imagross.it", 
            "password": "TestAdmin123!",
            "full_name": "Test Administrator 2"
        }
        
        response = requests.post(f"{API_BASE}/admin/create", json=admin_data, headers=headers)
        
        # Should work since we're using super admin token
        if response.status_code == 200:
            log_test("Super Admin Only", True, "Super admin can create admin users")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Super Admin Only", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Super Admin Only", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# EXCEL IMPORT SYSTEM TESTS
# ============================================================================

def test_excel_import_endpoint():
    """Test Excel import system endpoint accessibility"""
    if not admin_access_token:
        log_test("Excel Import Endpoint", False, "No admin access token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        # Create a simple test Excel file with pandas
        import tempfile
        import os
        import pandas as pd
        
        # Create test data
        test_data = {
            'nome': ['Mario', 'Lucia'],
            'cognome': ['Rossi', 'Bianchi'],
            'sesso': ['Maschio', 'Femmina'],
            'email': ['mario.rossi@test.it', 'lucia.bianchi@test.it'],
            'tel_cell': ['3331234567', '3339876543'],
            'citta': ['Milano', 'Roma'],
            'card_number': ['TEST001', 'TEST002'],
            'indirizzo': ['Via Roma 1', 'Via Torino 2'],
            'punto_provincia': ['MI', 'RM'],
            'newsletter': [1, 0],
            'numero_figli': [2, 1]
        }
        
        df = pd.DataFrame(test_data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_file_path = f.name
            df.to_excel(temp_file_path, index=False)
        
        try:
            # Test the import endpoint
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_users.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'data_type': 'users'}
                
                response = requests.post(f"{API_BASE}/admin/import/excel", 
                                       files=files, data=data, headers=headers)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ["message", "total_rows", "imported"]
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    log_test("Excel Import Endpoint", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate data types
                if not isinstance(result["total_rows"], int) or not isinstance(result["imported"], int):
                    log_test("Excel Import Endpoint", False, "Invalid data types in import response")
                    return False
                
                # Should have processed some rows
                if result["total_rows"] < 1:
                    log_test("Excel Import Endpoint", False, "No rows processed")
                    return False
                
                log_test("Excel Import Endpoint", True, f"Import processed: {result['imported']}/{result['total_rows']} records")
                return True
                
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                log_test("Excel Import Endpoint", False, f"Status {response.status_code}: {error_detail}")
                return False
                
        except Exception as cleanup_error:
            # Clean up temp file in case of error
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise cleanup_error
            
    except Exception as e:
        log_test("Excel Import Endpoint", False, f"Exception: {str(e)}")
        return False

def test_excel_import_unauthorized():
    """Test Excel import requires super admin access"""
    try:
        # Create a simple test file
        import tempfile
        import os
        
        csv_content = "nome,cognome,email\nTest,User,test@test.it"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Test without authentication
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                data = {'data_type': 'users'}
                
                response = requests.post(f"{API_BASE}/admin/import/excel", 
                                       files=files, data=data)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if response.status_code == 403:
                log_test("Excel Import Unauthorized", True, "Correctly requires super admin authentication")
                return True
            else:
                log_test("Excel Import Unauthorized", False, f"Should return 403, got {response.status_code}")
                return False
                
        except Exception as cleanup_error:
            # Clean up temp file in case of error
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise cleanup_error
            
    except Exception as e:
        log_test("Excel Import Unauthorized", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all backend API tests"""
    print("🚀 Starting ImaGross Loyalty System Backend API Tests")
    print("=" * 80)
    
    # Test API connectivity first
    if not test_api_root():
        print("❌ API not accessible, stopping tests")
        return False
    
    print("\n🔐 SUPER ADMIN AUTHENTICATION TESTS")
    print("-" * 50)
    admin_auth_tests = [
        test_admin_login,
        test_admin_login_invalid,
        test_create_admin_user
    ]
    
    print("\n🏪 STORE MANAGEMENT API TESTS")
    print("-" * 50)
    store_tests = [
        test_create_store,
        test_duplicate_store_code,
        test_get_stores,
        test_update_store
    ]
    
    print("\n💰 CASHIER MANAGEMENT API TESTS")
    print("-" * 50)
    cashier_tests = [
        test_create_cashier,
        test_duplicate_cashier_number,
        test_get_store_cashiers,
        test_get_all_cashiers
    ]
    
    print("\n📱 QR CODE GENERATION & REGISTRATION FLOW TESTS")
    print("-" * 50)
    qr_tests = [
        test_qr_info_retrieval,
        test_qr_invalid_code,
        test_user_registration_with_qr,
        test_cashier_registration_count
    ]
    
    print("\n📊 ADMIN DASHBOARD STATISTICS TESTS")
    print("-" * 50)
    stats_tests = [
        test_dashboard_statistics,
        test_stores_statistics
    ]
    
    print("\n🔒 ACCESS CONTROL TESTS")
    print("-" * 50)
    access_tests = [
        test_admin_endpoints_without_auth,
        test_super_admin_only_endpoints
    ]
    
    print("\n📄 EXCEL IMPORT SYSTEM TESTS")
    print("-" * 50)
    excel_tests = [
        test_excel_import_endpoint,
        test_excel_import_unauthorized
    ]
    
    print("\n👤 USER SYSTEM TESTS")
    print("-" * 50)
    user_tests = [
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
    
    # Run all test suites
    all_tests = (admin_auth_tests + store_tests + cashier_tests + 
                qr_tests + stats_tests + access_tests + excel_tests + user_tests)
    
    passed = 0
    total = len(all_tests)
    failed_tests = []
    
    for test_func in all_tests:
        try:
            if test_func():
                passed += 1
            else:
                failed_tests.append(test_func.__name__)
        except Exception as e:
            print(f"❌ {test_func.__name__}: Exception - {str(e)}")
            failed_tests.append(test_func.__name__)
    
    print("\n" + "=" * 80)
    print(f"📊 FINAL TEST RESULTS: {passed}/{total} tests passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test_name in failed_tests:
            print(f"   • {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ImaGross Super Admin Dashboard Backend is working correctly.")
        print("✅ Super Admin Authentication System: WORKING")
        print("✅ Store Management API: WORKING") 
        print("✅ Cashier Management API: WORKING")
        print("✅ QR Code Generation System: WORKING")
        print("✅ QR Registration Flow: WORKING")
        print("✅ Admin Dashboard Statistics: WORKING")
        print("✅ Excel Import System: WORKING")
        print("✅ Access Control: WORKING")
        print("✅ User System: WORKING")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
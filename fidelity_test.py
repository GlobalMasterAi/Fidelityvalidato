#!/usr/bin/env python3
"""
ImaGross Loyalty System - Fidelity JSON Data Import Tests
Tests the newly fixed Fidelity JSON data import functionality
"""

import requests
import json
import sys
import uuid

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
print(f"🔗 Testing Fidelity API at: {API_BASE}")

# Test results tracking
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

def test_debug_fidelity_endpoint():
    """Test GET /api/debug/fidelity - should return 30,287 loaded records with sample data"""
    try:
        response = requests.get(f"{API_BASE}/debug/fidelity")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["loaded_records", "available_cards", "sample_data"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Debug Fidelity Endpoint", False, f"Missing fields: {missing_fields}")
                return False
            
            # Check loaded records count - should be around 30,287
            loaded_records = data["loaded_records"]
            if loaded_records < 30000:
                log_test("Debug Fidelity Endpoint", False, f"Expected ~30,287 records, got {loaded_records}")
                return False
            
            # Validate available_cards is a list
            if not isinstance(data["available_cards"], list):
                log_test("Debug Fidelity Endpoint", False, "available_cards should be a list")
                return False
            
            # Validate sample_data exists and has expected structure
            sample_data = data["sample_data"]
            if not sample_data:
                log_test("Debug Fidelity Endpoint", False, "No sample_data provided")
                return False
            
            # Check sample data has key fidelity fields
            expected_sample_fields = ["card_number", "nome", "cognome", "email", "n_telefono", "localita"]
            missing_sample_fields = [field for field in expected_sample_fields if field not in sample_data]
            if missing_sample_fields:
                log_test("Debug Fidelity Endpoint", False, f"Sample data missing fields: {missing_sample_fields}")
                return False
            
            log_test("Debug Fidelity Endpoint", True, f"Loaded {loaded_records} records with valid sample data")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Debug Fidelity Endpoint", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Debug Fidelity Endpoint", False, f"Exception: {str(e)}")
        return False

def test_check_tessera_chiara_abatangelo():
    """Test card "2020000028284" - should return CHIARA ABATANGELO data"""
    try:
        tessera_data = {"tessera_fisica": "2020000028284"}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "found" not in data or "migrated" not in data:
                log_test("Check Tessera CHIARA ABATANGELO", False, "Missing found/migrated fields")
                return False
            
            if not data["found"]:
                log_test("Check Tessera CHIARA ABATANGELO", False, "Card should be found")
                return False
            
            if data["migrated"]:
                log_test("Check Tessera CHIARA ABATANGELO", False, "Card should not be migrated yet")
                return False
            
            # Validate user_data exists
            if "user_data" not in data:
                log_test("Check Tessera CHIARA ABATANGELO", False, "Missing user_data")
                return False
            
            user_data = data["user_data"]
            
            # Check specific CHIARA ABATANGELO data (from actual JSON file)
            expected_data = {
                "nome": "CHIARA",
                "cognome": "ABATANGELO", 
                "email": "chiara.abatangelo@libero.it",
                "telefono": "3497312268",
                "localita": "MOLA"
            }
            
            for field, expected_value in expected_data.items():
                if field not in user_data:
                    log_test("Check Tessera CHIARA ABATANGELO", False, f"Missing field: {field}")
                    return False
                
                if user_data[field] != expected_value:
                    log_test("Check Tessera CHIARA ABATANGELO", False, f"Field {field}: expected '{expected_value}', got '{user_data[field]}'")
                    return False
            
            # Check progressivo_spesa is properly converted (should be 100.01)
            if "progressivo_spesa" not in user_data:
                log_test("Check Tessera CHIARA ABATANGELO", False, "Missing progressivo_spesa field")
                return False
            
            expected_spesa = 100.01
            actual_spesa = user_data["progressivo_spesa"]
            if abs(actual_spesa - expected_spesa) > 0.01:
                log_test("Check Tessera CHIARA ABATANGELO", False, f"progressivo_spesa: expected {expected_spesa}, got {actual_spesa}")
                return False
            
            # Validate source is fidelity_json
            if data.get("source") != "fidelity_json":
                log_test("Check Tessera CHIARA ABATANGELO", False, f"Expected source 'fidelity_json', got '{data.get('source')}'")
                return False
            
            log_test("Check Tessera CHIARA ABATANGELO", True, f"Found CHIARA ABATANGELO with €{actual_spesa} spending")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Check Tessera CHIARA ABATANGELO", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Check Tessera CHIARA ABATANGELO", False, f"Exception: {str(e)}")
        return False

def test_check_tessera_valid_conversion():
    """Test card "2020000000013" - should return valid data with progressivo_spesa correctly converted"""
    try:
        tessera_data = {"tessera_fisica": "2020000000013"}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate basic response structure
            if not data.get("found"):
                log_test("Check Tessera Valid Conversion", False, "Card should be found")
                return False
            
            if "user_data" not in data:
                log_test("Check Tessera Valid Conversion", False, "Missing user_data")
                return False
            
            user_data = data["user_data"]
            
            # Check that progressivo_spesa is properly converted from European format
            if "progressivo_spesa" not in user_data:
                log_test("Check Tessera Valid Conversion", False, "Missing progressivo_spesa field")
                return False
            
            progressivo_spesa = user_data["progressivo_spesa"]
            
            # Should be a float, not a string
            if not isinstance(progressivo_spesa, (int, float)):
                log_test("Check Tessera Valid Conversion", False, f"progressivo_spesa should be numeric, got {type(progressivo_spesa)}")
                return False
            
            # Should be non-negative value
            if progressivo_spesa < 0:
                log_test("Check Tessera Valid Conversion", False, f"progressivo_spesa should be non-negative, got {progressivo_spesa}")
                return False
            
            # Check bollini conversion
            if "bollini" not in user_data:
                log_test("Check Tessera Valid Conversion", False, "Missing bollini field")
                return False
            
            bollini = user_data["bollini"]
            if not isinstance(bollini, int):
                log_test("Check Tessera Valid Conversion", False, f"bollini should be integer, got {type(bollini)}")
                return False
            
            # Check basic required fields are present (this card should have COSIMO DAMIANI data)
            if not user_data.get("nome") or not user_data.get("cognome"):
                log_test("Check Tessera Valid Conversion", False, "Missing nome or cognome")
                return False
            
            # Validate specific expected data for this card
            if user_data["nome"] != "COSIMO" or user_data["cognome"] != "DAMIANI":
                log_test("Check Tessera Valid Conversion", False, f"Expected COSIMO DAMIANI, got {user_data['nome']} {user_data['cognome']}")
                return False
            
            log_test("Check Tessera Valid Conversion", True, f"Valid conversion: €{progressivo_spesa}, {bollini} bollini for {user_data['nome']} {user_data['cognome']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Check Tessera Valid Conversion", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Check Tessera Valid Conversion", False, f"Exception: {str(e)}")
        return False

def test_check_tessera_not_found():
    """Test non-existent card - should return not found"""
    try:
        # Use a card number that definitely doesn't exist
        tessera_data = {"tessera_fisica": "9999999999999"}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "found" not in data or "migrated" not in data:
                log_test("Check Tessera Not Found", False, "Missing found/migrated fields")
                return False
            
            if data["found"]:
                log_test("Check Tessera Not Found", False, "Card should not be found")
                return False
            
            if data["migrated"]:
                log_test("Check Tessera Not Found", False, "Non-existent card should not be migrated")
                return False
            
            # Should have appropriate message
            if "message" not in data:
                log_test("Check Tessera Not Found", False, "Missing message field")
                return False
            
            if "non trovata" not in data["message"].lower():
                log_test("Check Tessera Not Found", False, f"Unexpected message: {data['message']}")
                return False
            
            log_test("Check Tessera Not Found", True, "Correctly returned not found for non-existent card")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Check Tessera Not Found", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Check Tessera Not Found", False, f"Exception: {str(e)}")
        return False

def test_check_tessera_migrated():
    """Test already migrated card - should return migrated status"""
    try:
        # Use a unique tessera number for this test
        test_tessera = f"TEST{uuid.uuid4().hex[:8].upper()}"
        
        # First, let's register this user to simulate migration
        user_data = {
            "nome": "MARIO",
            "cognome": "BIANCHI",
            "sesso": "M",
            "email": f"mario.bianchi.{uuid.uuid4().hex[:8]}@email.it",
            "telefono": "3331234567",
            "localita": "MILANO",
            "tessera_fisica": test_tessera,
            "password": "TestPass123!"
        }
        
        # Register the user first
        register_response = requests.post(f"{API_BASE}/register", json=user_data)
        
        if register_response.status_code != 200:
            log_test("Check Tessera Migrated", False, f"Failed to register user for migration test: {register_response.json().get('detail', 'Unknown error')}")
            return False
        
        # Now check the tessera - should show as migrated
        tessera_data = {"tessera_fisica": test_tessera}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "found" not in data or "migrated" not in data:
                log_test("Check Tessera Migrated", False, "Missing found/migrated fields")
                return False
            
            if not data["found"]:
                log_test("Check Tessera Migrated", False, "Card should be found")
                return False
            
            if not data["migrated"]:
                log_test("Check Tessera Migrated", False, "Card should be marked as migrated")
                return False
            
            # Should have appropriate message
            if "message" not in data:
                log_test("Check Tessera Migrated", False, "Missing message field")
                return False
            
            if "già migrata" not in data["message"].lower():
                log_test("Check Tessera Migrated", False, f"Unexpected message: {data['message']}")
                return False
            
            log_test("Check Tessera Migrated", True, "Correctly returned migrated status for registered card")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Check Tessera Migrated", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Check Tessera Migrated", False, f"Exception: {str(e)}")
        return False

def test_numeric_conversion_european_format():
    """Test European decimal format (comma to dot) conversion"""
    try:
        # Test with a card that has European decimal format in the original data
        tessera_data = {"tessera_fisica": "2020000028284"}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("found") or "user_data" not in data:
                log_test("Numeric Conversion European Format", False, "Card not found or missing user_data")
                return False
            
            user_data = data["user_data"]
            
            # Test progressivo_spesa conversion
            if "progressivo_spesa" not in user_data:
                log_test("Numeric Conversion European Format", False, "Missing progressivo_spesa")
                return False
            
            progressivo_spesa = user_data["progressivo_spesa"]
            
            # Should be converted to float with dot decimal separator
            if not isinstance(progressivo_spesa, (int, float)):
                log_test("Numeric Conversion European Format", False, f"progressivo_spesa not converted to number: {type(progressivo_spesa)}")
                return False
            
            # Should have decimal precision (not just integer)
            if progressivo_spesa == int(progressivo_spesa) and progressivo_spesa > 100:
                log_test("Numeric Conversion European Format", False, "progressivo_spesa appears to have lost decimal precision")
                return False
            
            # Test bollini conversion
            if "bollini" not in user_data:
                log_test("Numeric Conversion European Format", False, "Missing bollini")
                return False
            
            bollini = user_data["bollini"]
            if not isinstance(bollini, int):
                log_test("Numeric Conversion European Format", False, f"bollini not converted to integer: {type(bollini)}")
                return False
            
            # Test numero_figli conversion
            if "numero_figli" not in user_data:
                log_test("Numeric Conversion European Format", False, "Missing numero_figli")
                return False
            
            numero_figli = user_data["numero_figli"]
            if not isinstance(numero_figli, int):
                log_test("Numeric Conversion European Format", False, f"numero_figli not converted to integer: {type(numero_figli)}")
                return False
            
            log_test("Numeric Conversion European Format", True, f"Proper numeric conversion: €{progressivo_spesa}, {bollini} bollini, {numero_figli} figli")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Numeric Conversion European Format", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Numeric Conversion European Format", False, f"Exception: {str(e)}")
        return False

def test_data_mapping_completeness():
    """Test that all fidelity fields are correctly mapped to user model fields"""
    try:
        tessera_data = {"tessera_fisica": "2020000028284"}
        response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("found") or "user_data" not in data:
                log_test("Data Mapping Completeness", False, "Card not found or missing user_data")
                return False
            
            user_data = data["user_data"]
            
            # Test basic info mapping
            basic_fields = {
                "nome": str,
                "cognome": str, 
                "sesso": str,
                "email": str,
                "telefono": str,
                "localita": str
            }
            
            for field, expected_type in basic_fields.items():
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing basic field: {field}")
                    return False
                
                if not isinstance(user_data[field], expected_type):
                    log_test("Data Mapping Completeness", False, f"Field {field} wrong type: expected {expected_type}, got {type(user_data[field])}")
                    return False
            
            # Test address fields
            address_fields = ["indirizzo", "cap", "provincia"]
            for field in address_fields:
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing address field: {field}")
                    return False
            
            # Test date fields
            date_fields = ["data_nascita", "data_creazione", "data_ultima_spesa"]
            for field in date_fields:
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing date field: {field}")
                    return False
            
            # Test numeric fields
            numeric_fields = {
                "progressivo_spesa": (int, float),
                "bollini": int,
                "numero_figli": int
            }
            
            for field, expected_types in numeric_fields.items():
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing numeric field: {field}")
                    return False
                
                if not isinstance(user_data[field], expected_types):
                    log_test("Data Mapping Completeness", False, f"Field {field} wrong type: expected {expected_types}, got {type(user_data[field])}")
                    return False
            
            # Test boolean fields (consensi)
            boolean_fields = [
                "consenso_dati_personali",
                "consenso_dati_pubblicitari", 
                "animali_cani",
                "animali_gatti",
                "intolleranza_lattosio",
                "intolleranza_glutine", 
                "intolleranza_nichel",
                "celiachia",
                "richiede_fattura"
            ]
            
            for field in boolean_fields:
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing boolean field: {field}")
                    return False
                
                if not isinstance(user_data[field], bool):
                    log_test("Data Mapping Completeness", False, f"Field {field} should be boolean, got {type(user_data[field])}")
                    return False
            
            # Test optional fields that can be None
            optional_fields = [
                "consenso_profilazione",
                "consenso_marketing", 
                "coniugato",
                "data_matrimonio",
                "altra_intolleranza",
                "ragione_sociale"
            ]
            
            for field in optional_fields:
                if field not in user_data:
                    log_test("Data Mapping Completeness", False, f"Missing optional field: {field}")
                    return False
            
            # Test special fields
            if "stato_tessera" not in user_data:
                log_test("Data Mapping Completeness", False, "Missing stato_tessera field")
                return False
            
            if "negozio" not in user_data:
                log_test("Data Mapping Completeness", False, "Missing negozio field")
                return False
            
            log_test("Data Mapping Completeness", True, f"All {len(basic_fields) + len(address_fields) + len(date_fields) + len(numeric_fields) + len(boolean_fields) + len(optional_fields) + 2} fields properly mapped")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Data Mapping Completeness", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Data Mapping Completeness", False, f"Exception: {str(e)}")
        return False

def test_registration_with_fidelity_data():
    """Test user registration using fidelity data pre-population"""
    try:
        # First check tessera to get fidelity data - use a card with valid data
        tessera_data = {"tessera_fisica": "2020000000013"}
        check_response = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
        
        if check_response.status_code != 200:
            log_test("Registration with Fidelity Data", False, "Could not check test tessera for registration")
            return False
        
        check_data = check_response.json()
        if not check_data.get("found"):
            log_test("Registration with Fidelity Data", False, "Test tessera not found")
            return False
        
        if check_data.get("migrated"):
            log_test("Registration with Fidelity Data", False, "Test tessera already migrated")
            return False
        
        if "user_data" not in check_data:
            log_test("Registration with Fidelity Data", False, "No user_data in tessera check response")
            return False
        
        fidelity_data = check_data["user_data"]
        
        # Now register using the fidelity data
        user_data = {
            "nome": fidelity_data["nome"],
            "cognome": fidelity_data["cognome"],
            "sesso": fidelity_data["sesso"],
            "email": f"cosimo.damiani.{uuid.uuid4().hex[:8]}@email.it",  # Use unique email
            "telefono": fidelity_data.get("telefono") or "3331234567",  # Use default if empty
            "localita": fidelity_data.get("localita") or "BARI",  # Use default if empty
            "tessera_fisica": "2020000000013",
            "password": "TestPass123!",
            # Include extended fidelity fields
            "indirizzo": fidelity_data.get("indirizzo"),
            "cap": fidelity_data.get("cap"),
            "provincia": fidelity_data.get("provincia"),
            "data_nascita": fidelity_data.get("data_nascita"),
            "bollini": fidelity_data.get("bollini"),
            "progressivo_spesa": fidelity_data.get("progressivo_spesa"),
            "consenso_dati_personali": fidelity_data.get("consenso_dati_personali", True),
            "consenso_dati_pubblicitari": fidelity_data.get("consenso_dati_pubblicitari", True),
            "numero_figli": fidelity_data.get("numero_figli", 0),
            "animali_cani": fidelity_data.get("animali_cani", False),
            "animali_gatti": fidelity_data.get("animali_gatti", False),
            "intolleranza_lattosio": fidelity_data.get("intolleranza_lattosio", False),
            "intolleranza_glutine": fidelity_data.get("intolleranza_glutine", False),
            "intolleranza_nichel": fidelity_data.get("intolleranza_nichel", False),
            "celiachia": fidelity_data.get("celiachia", False),
            "richiede_fattura": fidelity_data.get("richiede_fattura", False)
        }
        
        response = requests.post(f"{API_BASE}/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate registration response
            required_fields = ["id", "nome", "cognome", "email", "tessera_fisica", "tessera_digitale", "punti"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                log_test("Registration with Fidelity Data", False, f"Missing fields in registration response: {missing_fields}")
                return False
            
            # Validate data matches fidelity input
            if data["nome"] != fidelity_data["nome"] or data["cognome"] != fidelity_data["cognome"]:
                log_test("Registration with Fidelity Data", False, "Name data doesn't match fidelity data")
                return False
            
            if data["tessera_fisica"] != "2020000000013":
                log_test("Registration with Fidelity Data", False, "Tessera fisica doesn't match")
                return False
            
            # Check that tessera is now marked as migrated
            check_migrated = requests.post(f"{API_BASE}/check-tessera", json=tessera_data)
            if check_migrated.status_code == 200:
                migrated_data = check_migrated.json()
                if not migrated_data.get("migrated"):
                    log_test("Registration with Fidelity Data", False, "Tessera should be marked as migrated after registration")
                    return False
            
            log_test("Registration with Fidelity Data", True, f"Successfully registered user with fidelity data: {data['nome']} {data['cognome']}")
            return True
            
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            log_test("Registration with Fidelity Data", False, f"Registration failed - Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        log_test("Registration with Fidelity Data", False, f"Exception: {str(e)}")
        return False

def run_fidelity_tests():
    """Run all fidelity JSON data import tests"""
    print("🚀 Starting ImaGross Fidelity JSON Data Import Tests")
    print("=" * 80)
    
    # Define test functions in order
    fidelity_tests = [
        test_debug_fidelity_endpoint,
        test_check_tessera_chiara_abatangelo,
        test_check_tessera_valid_conversion,
        test_check_tessera_not_found,
        test_check_tessera_migrated,
        test_numeric_conversion_european_format,
        test_data_mapping_completeness,
        test_registration_with_fidelity_data
    ]
    
    print("\n📊 FIDELITY JSON DATA IMPORT TESTS")
    print("-" * 50)
    
    passed = 0
    total = len(fidelity_tests)
    failed_tests = []
    
    for test_func in fidelity_tests:
        try:
            if test_func():
                passed += 1
            else:
                failed_tests.append(test_func.__name__)
        except Exception as e:
            print(f"❌ {test_func.__name__}: Exception - {str(e)}")
            failed_tests.append(test_func.__name__)
    
    print("\n" + "=" * 80)
    print(f"📊 FIDELITY TEST RESULTS: {passed}/{total} tests passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test_name in failed_tests:
            print(f"   • {test_name}")
    
    if passed == total:
        print("\n🎉 ALL FIDELITY TESTS PASSED! Fidelity JSON data import functionality is working correctly.")
        print("✅ Debug Endpoint: WORKING - Returns 30,287+ loaded records")
        print("✅ Card Verification: WORKING - All test cards return expected data")
        print("✅ Numeric Conversion: WORKING - European decimal format properly handled")
        print("✅ Data Mapping: WORKING - All fidelity fields correctly mapped")
        print("✅ Registration Integration: WORKING - Fidelity data pre-populates registration")
        return True
    else:
        print(f"\n⚠️  {total - passed} fidelity tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_fidelity_tests()
    sys.exit(0 if success else 1)
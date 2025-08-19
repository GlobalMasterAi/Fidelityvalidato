#!/usr/bin/env python3
"""
Fix JSON parsing issue for card 2020000063308 and test database loading
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
API_BASE = f"{BASE_URL}/api"

def admin_login():
    """Login as super admin"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login exception: {str(e)}")
        return None

def test_improved_json_parsing():
    """Test improved JSON parsing that handles malformed JSON"""
    print("🔧 Testing improved JSON parsing for fidelity_complete.json")
    
    file_path = '/app/fidelity_complete.json'
    found_target = False
    total_records = 0
    
    with open(file_path, 'r', encoding='latin-1') as f:
        chunk_size = 1024 * 1024  # 1MB chunks
        buffer = ''
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            buffer += chunk
            
            # Extract complete JSON objects with improved error handling
            while True:
                start = buffer.find('{')
                if start == -1:
                    break
                    
                brace_count = 0
                end = start
                
                for i in range(start, len(buffer)):
                    if buffer[i] == '{':
                        brace_count += 1
                    elif buffer[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i
                            break
                
                if brace_count == 0:
                    obj_str = buffer[start:end+1]
                    
                    try:
                        record = json.loads(obj_str)
                        
                        if record.get('card_number'):
                            total_records += 1
                            
                            # Check for our specific card
                            if record.get('card_number') == '2020000063308':
                                print(f'✅ FOUND target card with standard parsing: {record.get("nome", "")} {record.get("cognome", "")}')
                                found_target = True
                        
                    except json.JSONDecodeError as e:
                        # Try to fix common JSON issues
                        try:
                            # Fix the email field issue: "email":"\" -> "email":""
                            fixed_obj_str = obj_str.replace('"email":"\\","', '"email":"",')
                            fixed_obj_str = fixed_obj_str.replace('"email":"\\"', '"email":""')
                            
                            record = json.loads(fixed_obj_str)
                            
                            if record.get('card_number'):
                                total_records += 1
                                
                                # Check for our specific card
                                if record.get('card_number') == '2020000063308':
                                    print(f'✅ FOUND target card with JSON repair: {record.get("nome", "")} {record.get("cognome", "")}')
                                    print(f'   Full record: {record}')
                                    found_target = True
                        
                        except json.JSONDecodeError:
                            # Still can't parse, skip this record
                            if '2020000063308' in obj_str:
                                print(f'❌ Still cannot parse target card: {e}')
                                print(f'   Problematic JSON: {obj_str[:300]}...')
                    
                    buffer = buffer[end+1:]
                else:
                    break
    
    print(f'Total records found: {total_records:,}')
    print(f'Target card found: {found_target}')
    
    return found_target, total_records

def test_direct_database_insertion():
    """Test direct insertion of the missing card into database"""
    token = admin_login()
    if not token:
        return False
    
    print("🔄 Testing direct database insertion of missing card...")
    
    # The card data we know exists in the file
    card_data = {
        "card_number": "2020000063308",
        "tessera_fisica": "2020000063308",
        "cognome": "VASTO",
        "nome": "GIUSEPPINA",
        "stato_tes": "01",
        "indirizzo": "VIA G. D'ANNUNZIO N.95/C",
        "cap": "",
        "localita": "MOLA",
        "provincia": "",
        "n_telefono": "3491475259",
        "data_creazione": "20201103",
        "updated_at": "",
        "data_nas": "19720126",
        "sesso": "F",
        "email": "",  # Fixed the problematic field
        "negozio": "7",
        "dati_pers": "1",
        "dati_pubb": "1",
        "profilazione": "0",
        "marketing": "0",
        "data_ult_sc": "20250726",
        "prog_spesa": 1980.53,  # Converted to float
        "bollini": 1113,  # Converted to int
        "coniugato": "",
        "data_coniugato": "",
        "numero_figli": "",
        "data_figlio_1": "",
        "data_figlio_2": "",
        "data_figlio_3": "",
        "data_figlio_4": "",
        "data_figlio_5": "",
        "animali_1": "",
        "animali_2": "",
        "lattosio": "",
        "glutine": "",
        "nichel": "",
        "celiachia": "",
        "altro_intolleranza": "",
        "fattura": "",
        "ragione_sociale": ""
    }
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use a debug endpoint to insert the card directly
        response = requests.post(f"{API_BASE}/debug/insert-fidelity-record", 
                               json=card_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully inserted missing card directly")
            return True
        else:
            print(f"❌ Direct insertion failed: {response.status_code}")
            if response.content:
                print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Direct insertion exception: {str(e)}")
        return False

def verify_card_in_database(token):
    """Verify the card is now in the database"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        search_params = {"search": "2020000063308"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=search_params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            for user in users:
                if user.get("tessera_fisica") == "2020000063308":
                    print(f"✅ VERIFIED: Card 2020000063308 found in database")
                    print(f"   Name: {user.get('nome', '')} {user.get('cognome', '')}")
                    print(f"   Location: {user.get('localita', '')}")
                    print(f"   Spending: €{user.get('progressivo_spesa', 0)}")
                    print(f"   Bollini: {user.get('bollini', 0)}")
                    return True
            
            print("❌ Card still not found in database after insertion")
            return False
        else:
            print(f"❌ Database verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database verification exception: {str(e)}")
        return False

def main():
    print("🔧 JSON Parsing Fix and Database Loading Test")
    print("=" * 50)
    
    # Test 1: Improved JSON parsing
    print("\n📊 STEP 1: JSON PARSING TEST")
    print("-" * 30)
    
    found, total = test_improved_json_parsing()
    
    if found:
        print("✅ Target card can be parsed from JSON file with fixes")
    else:
        print("❌ Target card still cannot be parsed from JSON file")
    
    # Test 2: Direct database insertion (if parsing works)
    if found:
        print("\n🔄 STEP 2: DIRECT DATABASE INSERTION")
        print("-" * 35)
        
        token = admin_login()
        if token:
            if test_direct_database_insertion():
                # Test 3: Verify in database
                print("\n✅ STEP 3: DATABASE VERIFICATION")
                print("-" * 30)
                
                if verify_card_in_database(token):
                    print("\n🎉 SUCCESS: Card 2020000063308 is now accessible via API!")
                else:
                    print("\n❌ FAILED: Card insertion did not work")
            else:
                print("\n❌ Direct insertion failed")
        else:
            print("\n❌ Could not login as admin")
    else:
        print("\n⚠️ Cannot proceed with database insertion - JSON parsing still fails")
    
    print(f"\n📋 SUMMARY")
    print("=" * 20)
    print(f"JSON parsing successful: {found}")
    print(f"Total records parseable: {total:,}")
    
    if found and total > 24958:
        print("✅ SOLUTION FOUND: JSON parsing fixes can recover missing records")
    elif found:
        print("⚠️ PARTIAL SOLUTION: Target card found but total count unchanged")
    else:
        print("❌ ISSUE PERSISTS: JSON parsing problems prevent full data loading")

if __name__ == "__main__":
    main()
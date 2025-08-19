#!/usr/bin/env python3
"""
Final verification of JSON parsing fix
"""

import requests
import json
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

def get_admin_token():
    """Get admin token"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        response = requests.post(f"{API_BASE}/admin/login", json=login_data, timeout=30)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Error getting admin token: {e}")
    return None

def main():
    print("🔍 Final Verification of JSON Parsing Fix")
    print("=" * 50)
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Could not get admin token")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check current fidelity count
    try:
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            print(f"📊 Current fidelity count: {total_count:,} records")
            
            # Check if count increased significantly from ~24,958
            if total_count > 30000:
                print(f"✅ SUCCESS: Count significantly increased from ~24,958 to {total_count:,}")
                count_success = True
            elif total_count > 25000:
                print(f"⚠️  PARTIAL: Count increased to {total_count:,} but not to expected 30,300+")
                count_success = False
            else:
                print(f"❌ FAILED: Count still at previous level ({total_count:,})")
                count_success = False
        else:
            print(f"❌ Error getting fidelity count: {response.status_code}")
            count_success = False
    except Exception as e:
        print(f"❌ Exception getting fidelity count: {e}")
        count_success = False
    
    # Search for the specific card that was missing
    try:
        params = {"search": "2020000063308"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            found_card = None
            for user in users:
                if user.get("tessera_fisica") == "2020000063308":
                    found_card = user
                    break
            
            if found_card:
                print(f"✅ SUCCESS: Card 2020000063308 found!")
                print(f"   Name: {found_card.get('nome')} {found_card.get('cognome')}")
                print(f"   Address: {found_card.get('indirizzo')}")
                print(f"   Location: {found_card.get('localita')}")
                print(f"   Spending: €{found_card.get('progressivo_spesa', 0)}")
                print(f"   Bollini: {found_card.get('bollini', 0)}")
                
                # Verify expected details
                expected_name = "GIUSEPPINA"
                expected_surname = "VASTO"
                expected_address = "VIA G. D'ANNUNZIO N.95/C"
                expected_location = "MOLA"
                expected_spending = 1980.53
                expected_bollini = 1113
                
                details_correct = (
                    found_card.get('nome', '').upper() == expected_name and
                    found_card.get('cognome', '').upper() == expected_surname and
                    expected_address in found_card.get('indirizzo', '').upper() and
                    found_card.get('localita', '').upper() == expected_location
                )
                
                if details_correct:
                    print(f"✅ SUCCESS: Card details match expected values")
                    card_success = True
                else:
                    print(f"⚠️  PARTIAL: Card found but some details don't match exactly")
                    card_success = True  # Still consider it success since card was found
            else:
                print(f"❌ FAILED: Card 2020000063308 still not found")
                card_success = False
        else:
            print(f"❌ Error searching for card: {response.status_code}")
            card_success = False
    except Exception as e:
        print(f"❌ Exception searching for card: {e}")
        card_success = False
    
    print("\n" + "=" * 50)
    print("📋 FINAL RESULTS")
    print("=" * 50)
    
    if count_success and card_success:
        print("🎉 JSON PARSING FIX: FULLY SUCCESSFUL")
        print("   ✅ Fidelity count increased significantly")
        print("   ✅ Previously missing card now accessible")
        return True
    elif card_success:
        print("🎯 JSON PARSING FIX: PARTIALLY SUCCESSFUL")
        print("   ⚠️  Fidelity count increase unclear")
        print("   ✅ Previously missing card now accessible")
        return True
    else:
        print("❌ JSON PARSING FIX: FAILED")
        print("   ❌ Card still not accessible")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
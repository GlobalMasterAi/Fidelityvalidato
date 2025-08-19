#!/usr/bin/env python3
"""
Targeted test for card 2020000063308 (VASTO GIUSEPPINA) after force reload
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

def check_fidelity_count(token):
    """Check current fidelity count"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("total", 0)
        else:
            print(f"❌ Fidelity count check failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Fidelity count exception: {str(e)}")
        return None

def search_specific_card(token, card_number):
    """Search for specific card"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        search_params = {"search": card_number}
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, params=search_params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            for user in users:
                if user.get("tessera_fisica") == card_number:
                    return user
            return None
        else:
            print(f"❌ Card search failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Card search exception: {str(e)}")
        return None

def force_reload_data(token):
    """Force reload data"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force reload initiated: {data.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Force reload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Force reload exception: {str(e)}")
        return False

def main():
    print("🎯 Targeted Test for Card 2020000063308 (VASTO GIUSEPPINA)")
    print("=" * 60)
    
    # Login
    token = admin_login()
    if not token:
        return
    
    print("✅ Admin login successful")
    
    # Check initial state
    print("\n📊 INITIAL STATE CHECK")
    print("-" * 30)
    
    initial_count = check_fidelity_count(token)
    print(f"Current fidelity count: {initial_count:,}")
    
    initial_card = search_specific_card(token, "2020000063308")
    if initial_card:
        print(f"✅ Card 2020000063308 FOUND: {initial_card.get('nome', '')} {initial_card.get('cognome', '')}")
    else:
        print("❌ Card 2020000063308 NOT FOUND in database")
    
    # Force reload
    print("\n🔄 FORCE RELOAD")
    print("-" * 20)
    
    if force_reload_data(token):
        print("⏳ Waiting 60 seconds for data loading...")
        time.sleep(60)
        
        # Check post-reload state
        print("\n📈 POST-RELOAD STATE CHECK")
        print("-" * 30)
        
        post_count = check_fidelity_count(token)
        print(f"Post-reload fidelity count: {post_count:,}")
        
        if post_count and initial_count:
            if post_count > initial_count:
                print(f"✅ Count increased by {post_count - initial_count:,} records")
            elif post_count == initial_count:
                print("⚠️ Count unchanged")
            else:
                print(f"❌ Count decreased by {initial_count - post_count:,} records")
        
        post_card = search_specific_card(token, "2020000063308")
        if post_card:
            print(f"✅ Card 2020000063308 FOUND AFTER RELOAD:")
            print(f"   Name: {post_card.get('nome', '')} {post_card.get('cognome', '')}")
            print(f"   Location: {post_card.get('localita', '')}")
            print(f"   Address: {post_card.get('indirizzo', '')}")
            print(f"   Phone: {post_card.get('telefono', '')}")
            print(f"   Spending: €{post_card.get('progressivo_spesa', 0)}")
            print(f"   Bollini: {post_card.get('bollini', 0)}")
            
            # Verify expected data
            expected_data = {
                "nome": "GIUSEPPINA",
                "cognome": "VASTO",
                "localita": "MOLA",
                "indirizzo": "VIA G. D'ANNUNZIO N.95/C"
            }
            
            all_match = True
            for field, expected in expected_data.items():
                actual = post_card.get(field, "")
                if expected.upper() not in actual.upper():
                    print(f"   ❌ {field}: Expected '{expected}', got '{actual}'")
                    all_match = False
                else:
                    print(f"   ✅ {field}: {actual}")
            
            if all_match:
                print("✅ ALL DATA MATCHES EXPECTED VALUES!")
            else:
                print("❌ Some data doesn't match expected values")
                
        else:
            print("❌ Card 2020000063308 STILL NOT FOUND after reload")
            
            # Try alternative searches
            print("\n🔍 ALTERNATIVE SEARCHES")
            print("-" * 25)
            
            vasto_card = search_specific_card(token, "VASTO")
            if vasto_card:
                print("Found VASTO cards in database")
            else:
                print("No VASTO cards found")
                
            giuseppina_card = search_specific_card(token, "GIUSEPPINA")
            if giuseppina_card:
                print("Found GIUSEPPINA cards in database")
            else:
                print("No GIUSEPPINA cards found")
    
    print("\n🏁 TEST COMPLETE")

if __name__ == "__main__":
    main()
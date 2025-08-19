#!/usr/bin/env python3
"""
Quick verification of JSON parsing fix results
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
    print("🔍 Quick Verification of JSON Parsing Fix")
    print("=" * 50)
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Could not get admin token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check current fidelity count
    try:
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            print(f"📊 Current fidelity count: {total_count:,} records")
            
            # Check if count increased significantly
            if total_count > 25000:
                print(f"✅ Count appears to have increased from ~24,958")
            else:
                print(f"⚠️  Count still around previous level")
        else:
            print(f"❌ Error getting fidelity count: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception getting fidelity count: {e}")
    
    # Search for the specific card
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
                print(f"✅ Card 2020000063308 found!")
                print(f"   Name: {found_card.get('nome')} {found_card.get('cognome')}")
                print(f"   Address: {found_card.get('indirizzo')}")
                print(f"   Location: {found_card.get('localita')}")
                print(f"   Spending: €{found_card.get('progressivo_spesa', 0)}")
                print(f"   Bollini: {found_card.get('bollini', 0)}")
            else:
                print(f"❌ Card 2020000063308 still not found")
        else:
            print(f"❌ Error searching for card: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception searching for card: {e}")

if __name__ == "__main__":
    main()
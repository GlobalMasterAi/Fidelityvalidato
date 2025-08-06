#!/usr/bin/env python3
"""
Debug API responses to understand the actual data structure
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
    """Login as super admin to get access token"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            return None
            
    except Exception as e:
        return None

def debug_api_responses():
    """Debug the actual API responses"""
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Cannot get admin token")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Debug Admin Stats Dashboard API
    print("🔍 DEBUGGING ADMIN STATS DASHBOARD API")
    print("=" * 50)
    try:
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received")
            print(f"📋 Full response structure:")
            print(json.dumps(data, indent=2))
            
            if "vendite_stats" in data:
                print(f"\n🎯 vendite_stats keys: {list(data['vendite_stats'].keys())}")
                print(f"📊 vendite_stats content:")
                print(json.dumps(data['vendite_stats'], indent=2))
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Debug Vendite Dashboard API
    print("\n\n🔍 DEBUGGING VENDITE DASHBOARD API")
    print("=" * 50)
    try:
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received")
            print(f"📋 Full response structure:")
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Debug Scontrini Stats API
    print("\n\n🔍 DEBUGGING SCONTRINI STATS API")
    print("=" * 50)
    try:
        response = requests.get(f"{API_BASE}/admin/scontrini/stats", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received")
            print(f"📋 Full response structure:")
            print(json.dumps(data, indent=2))
            
            if "stats" in data:
                print(f"\n🎯 stats keys: {list(data['stats'].keys())}")
                print(f"📊 stats content:")
                print(json.dumps(data['stats'], indent=2))
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_api_responses()
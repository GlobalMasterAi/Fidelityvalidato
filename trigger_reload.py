#!/usr/bin/env python3
"""
Trigger force data reload to test JSON parsing fix
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
    print("🔄 Triggering Force Data Reload")
    print("=" * 40)
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Could not get admin token")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get initial count
    try:
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        if response.status_code == 200:
            initial_count = response.json().get("total", 0)
            print(f"📊 Initial fidelity count: {initial_count:,} records")
        else:
            print(f"⚠️  Could not get initial count: {response.status_code}")
            initial_count = 0
    except Exception as e:
        print(f"⚠️  Error getting initial count: {e}")
        initial_count = 0
    
    # Trigger force reload
    try:
        print("🔄 Triggering force data reload...")
        response = requests.post(f"{API_BASE}/debug/force-reload-data", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Force reload triggered: {data.get('message', 'Success')}")
        else:
            print(f"❌ Force reload failed: {response.status_code}")
            if response.content:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception triggering reload: {e}")
        return False
    
    # Wait and monitor progress
    print("⏳ Waiting for reload to complete...")
    max_wait = 180  # 3 minutes
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait:
        try:
            response = requests.get(f"{API_BASE}/startup-status", headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "data_loading_status" in data:
                    status = data["data_loading_status"]
                    fidelity_status = status.get("fidelity", "unknown")
                    
                    print(f"   Status: {fidelity_status}")
                    
                    if fidelity_status in ["completed", "database_loaded_complete", "database_loaded_real"]:
                        print("✅ Data loading completed!")
                        break
                    elif fidelity_status in ["error", "failed"]:
                        print(f"❌ Data loading failed: {fidelity_status}")
                        return False
            
            time.sleep(10)
            
        except Exception as e:
            print(f"   Error checking status: {e}")
            time.sleep(5)
    else:
        print("⚠️  Timeout waiting for reload completion")
    
    # Check final count
    try:
        time.sleep(5)  # Give it a moment
        response = requests.get(f"{API_BASE}/admin/fidelity-users", headers=headers, timeout=30)
        if response.status_code == 200:
            final_count = response.json().get("total", 0)
            print(f"📊 Final fidelity count: {final_count:,} records")
            
            if final_count > initial_count:
                increase = final_count - initial_count
                print(f"📈 Count increased by {increase:,} records!")
                return True
            else:
                print(f"⚠️  No count increase detected")
                return False
        else:
            print(f"❌ Could not get final count: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting final count: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
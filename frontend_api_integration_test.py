#!/usr/bin/env python3
"""
Frontend API Integration Test
Testing if frontend is correctly configured to call backend APIs
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# Read frontend .env to get the configured backend URL
frontend_env_path = "/app/frontend/.env"
REACT_APP_BACKEND_URL = None

if os.path.exists(frontend_env_path):
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                REACT_APP_BACKEND_URL = line.split('=', 1)[1].strip()
                break

print(f"🔗 Frontend configured backend URL: {REACT_APP_BACKEND_URL}")

# Test both the configured URL and local backend
test_urls = [
    ("Local Backend", "http://localhost:8001"),
    ("Frontend Configured URL", REACT_APP_BACKEND_URL) if REACT_APP_BACKEND_URL else None
]

test_urls = [url for url in test_urls if url is not None]

def test_backend_connectivity(name, base_url):
    """Test basic backend connectivity"""
    print(f"\n🔍 Testing {name}: {base_url}")
    
    try:
        # Test basic API root
        response = requests.get(f"{base_url}/api/", timeout=10)
        if response.status_code == 200:
            print(f"  ✅ API root accessible: {response.status_code}")
        else:
            print(f"  ❌ API root failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ API root connection failed: {str(e)}")
        return False
    
    try:
        # Test admin login
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        response = requests.post(f"{base_url}/api/admin/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"  ✅ Admin login successful")
            
            # Test fidelity users endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{base_url}/api/admin/fidelity-users?limit=10", headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                users_count = len(data.get("users", []))
                print(f"  ✅ Fidelity users endpoint working: {users_count} users returned, total: {total:,}")
                return True
            else:
                print(f"  ❌ Fidelity users endpoint failed: {response.status_code}")
                return False
        else:
            print(f"  ❌ Admin login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Admin login/fidelity test failed: {str(e)}")
        return False

def main():
    print("🚨 FRONTEND API INTEGRATION TEST")
    print("=" * 50)
    
    working_backends = []
    
    for name, url in test_urls:
        if test_backend_connectivity(name, url):
            working_backends.append((name, url))
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    
    if working_backends:
        print(f"✅ Working backends: {len(working_backends)}")
        for name, url in working_backends:
            print(f"   - {name}: {url}")
    else:
        print("❌ No working backends found!")
    
    if len(working_backends) == 1 and working_backends[0][0] == "Local Backend":
        print("\n🚨 CRITICAL FINDING:")
        print("   - Local backend is working perfectly")
        print("   - Frontend configured URL may not be accessible")
        print("   - This suggests a DEPLOYMENT/ROUTING issue, not a backend code issue")
        print("\n💡 RECOMMENDATION:")
        print("   - Check if production URL routing is correctly configured")
        print("   - Verify that the production domain points to the correct backend service")
        print("   - The backend code and database are working correctly")
    
    return len(working_backends) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
PRODUCTION URL COMPARISON TEST
Test admin login on both current URL and production URL
"""

import requests
import json

# Test credentials
ADMIN_CREDENTIALS = {
    "username": "superadmin", 
    "password": "ImaGross2024!"
}

# URLs to test
CURRENT_URL = "https://c1e05f28-1cc8-4c95-adee-7fd4dd71b6a5.preview.emergentagent.com/api"
PRODUCTION_URL = "https://rfm-dashboard-1.emergent.host/api"

def test_admin_login(api_url, url_name):
    """Test admin login on specific URL"""
    print(f"\n🔗 Testing {url_name}: {api_url}")
    print("="*80)
    
    try:
        response = requests.post(f"{api_url}/admin/login", json=ADMIN_CREDENTIALS, timeout=30)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Headers: {dict(response.headers)}")
        
        if response.content:
            try:
                data = response.json()
                print(f"📡 Response: {json.dumps(data, indent=2)}")
                
                if response.status_code == 200 and "access_token" in data:
                    print(f"✅ {url_name}: LOGIN SUCCESSFUL")
                    return True
                else:
                    print(f"❌ {url_name}: LOGIN FAILED - {data.get('detail', 'Unknown error')}")
                    return False
            except:
                print(f"📡 Raw Response: {response.text}")
                print(f"❌ {url_name}: LOGIN FAILED - Invalid JSON response")
                return False
        else:
            print(f"❌ {url_name}: LOGIN FAILED - Empty response")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ {url_name}: TIMEOUT - Server not responding")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ {url_name}: CONNECTION ERROR - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {url_name}: EXCEPTION - {str(e)}")
        return False

def main():
    print("🚨 PRODUCTION URL COMPARISON TEST")
    print("="*80)
    print(f"Testing admin login on both URLs with credentials:")
    print(f"Username: {ADMIN_CREDENTIALS['username']}")
    print(f"Password: {ADMIN_CREDENTIALS['password']}")
    
    # Test current URL (working)
    current_success = test_admin_login(CURRENT_URL, "CURRENT URL")
    
    # Test production URL (reported failing)
    production_success = test_admin_login(PRODUCTION_URL, "PRODUCTION URL")
    
    # Summary
    print("\n" + "="*80)
    print("🔍 COMPARISON SUMMARY")
    print("="*80)
    
    print(f"Current URL ({CURRENT_URL}): {'✅ WORKING' if current_success else '❌ FAILING'}")
    print(f"Production URL ({PRODUCTION_URL}): {'✅ WORKING' if production_success else '❌ FAILING'}")
    
    if current_success and not production_success:
        print("\n🎯 ROOT CAUSE IDENTIFIED:")
        print("- Admin login works on current development URL")
        print("- Admin login FAILS on production URL")
        print("- This indicates a deployment/routing issue")
        print("\n🔧 SOLUTION:")
        print("1. Check if production deployment is using correct backend")
        print("2. Verify production URL routing configuration")
        print("3. Ensure production environment variables are correct")
        print("4. Check if production database connection is working")
    elif production_success:
        print("\n✅ Both URLs working - issue may be intermittent or resolved")
    else:
        print("\n❌ Both URLs failing - broader system issue")

if __name__ == "__main__":
    main()
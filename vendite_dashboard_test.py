#!/usr/bin/env python3
"""
CRITICAL DEBUG: API Dashboard Vendite Test
Focused test for /api/admin/vendite/dashboard endpoint
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
if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🔗 Testing API at: {API_BASE}")

def test_admin_login():
    """Get admin token for testing"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin login successful")
            return data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            if response.content:
                print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login exception: {str(e)}")
        return None

def test_vendite_dashboard_api(admin_token):
    """Test the specific /api/admin/vendite/dashboard endpoint"""
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        print(f"\n🔍 TESTING: GET /api/admin/vendite/dashboard")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response received successfully")
            
            # Check response structure
            print(f"\n📋 RESPONSE STRUCTURE ANALYSIS:")
            print(f"   Response type: {type(data)}")
            print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Check for expected structure: {"success": True, "dashboard": {...}}
            if isinstance(data, dict):
                if "success" in data and "dashboard" in data:
                    print(f"✅ Correct structure: success={data['success']}, dashboard present")
                    
                    dashboard = data["dashboard"]
                    print(f"\n📊 DASHBOARD CONTENT:")
                    print(f"   Dashboard type: {type(dashboard)}")
                    print(f"   Dashboard keys: {list(dashboard.keys()) if isinstance(dashboard, dict) else 'Not a dict'}")
                    
                    # Check overview section
                    if "overview" in dashboard:
                        overview = dashboard["overview"]
                        print(f"\n📈 OVERVIEW SECTION:")
                        print(f"   Overview keys: {list(overview.keys()) if isinstance(overview, dict) else 'Not a dict'}")
                        
                        # Check critical fields
                        critical_fields = ["total_sales", "unique_customers", "total_revenue"]
                        for field in critical_fields:
                            if field in overview:
                                value = overview[field]
                                print(f"   ✅ {field}: {value} ({type(value)})")
                            else:
                                print(f"   ❌ Missing field: {field}")
                    else:
                        print(f"   ❌ Missing 'overview' section in dashboard")
                    
                    # Check monthly_trends section
                    if "monthly_trends" in dashboard:
                        monthly_trends = dashboard["monthly_trends"]
                        print(f"\n📅 MONTHLY TRENDS:")
                        print(f"   Type: {type(monthly_trends)}")
                        if isinstance(monthly_trends, list):
                            print(f"   Count: {len(monthly_trends)} months")
                            if len(monthly_trends) > 0:
                                print(f"   Sample: {monthly_trends[0]}")
                        else:
                            print(f"   ❌ Monthly trends is not a list")
                    else:
                        print(f"   ❌ Missing 'monthly_trends' section")
                    
                    # Check top_customers section
                    if "top_customers" in dashboard:
                        top_customers = dashboard["top_customers"]
                        print(f"\n👥 TOP CUSTOMERS:")
                        print(f"   Type: {type(top_customers)}")
                        if isinstance(top_customers, list):
                            print(f"   Count: {len(top_customers)} customers")
                            if len(top_customers) > 0:
                                print(f"   Sample: {top_customers[0]}")
                        else:
                            print(f"   ❌ Top customers is not a list")
                    else:
                        print(f"   ❌ Missing 'top_customers' section")
                    
                    return True
                    
                else:
                    print(f"❌ WRONG STRUCTURE: Expected {{success: True, dashboard: {{...}}}}")
                    print(f"   Actual structure: {data}")
                    return False
            else:
                print(f"❌ Response is not a dictionary: {data}")
                return False
                
        elif response.status_code == 401:
            print(f"❌ Authentication failed - token invalid")
            return False
        elif response.status_code == 403:
            print(f"❌ Access denied - insufficient permissions")
            return False
        else:
            print(f"❌ API call failed with status {response.status_code}")
            if response.content:
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during API test: {str(e)}")
        return False

def test_with_invalid_token():
    """Test with invalid token to confirm 401 error"""
    try:
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        print(f"\n🔒 TESTING: Invalid token authentication")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected invalid token")
            return True
        else:
            print(f"❌ Should return 401 for invalid token, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during invalid token test: {str(e)}")
        return False

def main():
    print("🚨 CRITICAL DEBUG: API Dashboard Vendite Test")
    print("=" * 60)
    
    # Step 1: Get admin token
    print("\n1️⃣ STEP 1: Admin Authentication")
    admin_token = test_admin_login()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return
    
    print(f"   Token preview: {admin_token[:20]}...")
    
    # Step 2: Test the vendite dashboard API
    print("\n2️⃣ STEP 2: Vendite Dashboard API Test")
    dashboard_success = test_vendite_dashboard_api(admin_token)
    
    # Step 3: Test authentication
    print("\n3️⃣ STEP 3: Authentication Validation")
    auth_success = test_with_invalid_token()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"   Admin Login: {'✅ PASS' if admin_token else '❌ FAIL'}")
    print(f"   Dashboard API: {'✅ PASS' if dashboard_success else '❌ FAIL'}")
    print(f"   Auth Validation: {'✅ PASS' if auth_success else '❌ FAIL'}")
    
    if dashboard_success:
        print("\n🎉 CONCLUSION: API Dashboard Vendite is WORKING correctly")
        print("   The issue is likely in the frontend, not the backend API")
    else:
        print("\n🚨 CONCLUSION: API Dashboard Vendite has ISSUES")
        print("   The backend API is not returning the expected data structure")

if __name__ == "__main__":
    main()
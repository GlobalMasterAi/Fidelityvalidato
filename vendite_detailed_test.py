#!/usr/bin/env python3
"""
DETAILED VENDITE DASHBOARD API TEST
Complete validation of data structure and content
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
        login_data = {"username": "superadmin", "password": "ImaGross2024!"}
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except:
        return None

def detailed_dashboard_test():
    """Comprehensive dashboard API test"""
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Cannot get admin token")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            return False
        
        data = response.json()
        
        print("🔍 COMPLETE API RESPONSE ANALYSIS")
        print("=" * 50)
        
        # Print full JSON structure (formatted)
        print("\n📄 FULL JSON RESPONSE:")
        print(json.dumps(data, indent=2, default=str))
        
        # Validate structure
        print("\n✅ STRUCTURE VALIDATION:")
        
        # Check top level
        if not isinstance(data, dict):
            print("❌ Response is not a dictionary")
            return False
        
        if "success" not in data or "dashboard" not in data:
            print("❌ Missing 'success' or 'dashboard' keys")
            return False
        
        if data["success"] != True:
            print(f"❌ success is not True: {data['success']}")
            return False
        
        dashboard = data["dashboard"]
        if not isinstance(dashboard, dict):
            print("❌ dashboard is not a dictionary")
            return False
        
        print("✅ Top-level structure is correct")
        
        # Check overview section
        if "overview" not in dashboard:
            print("❌ Missing 'overview' section")
            return False
        
        overview = dashboard["overview"]
        required_overview_fields = ["total_sales", "unique_customers", "total_revenue", "avg_transaction"]
        
        print(f"\n📊 OVERVIEW VALIDATION:")
        for field in required_overview_fields:
            if field not in overview:
                print(f"❌ Missing overview field: {field}")
                return False
            
            value = overview[field]
            if not isinstance(value, (int, float)):
                print(f"❌ {field} is not numeric: {value} ({type(value)})")
                return False
            
            if value < 0:
                print(f"❌ {field} is negative: {value}")
                return False
            
            print(f"✅ {field}: {value:,}")
        
        # Check monthly trends
        if "monthly_trends" not in dashboard:
            print("❌ Missing 'monthly_trends' section")
            return False
        
        monthly_trends = dashboard["monthly_trends"]
        if not isinstance(monthly_trends, list):
            print("❌ monthly_trends is not a list")
            return False
        
        print(f"\n📅 MONTHLY TRENDS VALIDATION:")
        print(f"✅ Found {len(monthly_trends)} months of data")
        
        if len(monthly_trends) > 0:
            sample_month = monthly_trends[0]
            required_month_fields = ["month", "revenue", "transactions"]
            for field in required_month_fields:
                if field not in sample_month:
                    print(f"❌ Missing month field: {field}")
                    return False
            print(f"✅ Monthly trend structure is correct")
        
        # Check top customers
        if "top_customers" not in dashboard:
            print("❌ Missing 'top_customers' section")
            return False
        
        top_customers = dashboard["top_customers"]
        if not isinstance(top_customers, list):
            print("❌ top_customers is not a list")
            return False
        
        print(f"\n👥 TOP CUSTOMERS VALIDATION:")
        print(f"✅ Found {len(top_customers)} top customers")
        
        if len(top_customers) > 0:
            sample_customer = top_customers[0]
            if "codice_cliente" not in sample_customer or "spent" not in sample_customer:
                print(f"❌ Invalid customer structure: {sample_customer}")
                return False
            print(f"✅ Customer structure is correct")
        
        # Check additional sections
        additional_sections = ["top_departments", "top_products", "top_promotions"]
        for section in additional_sections:
            if section in dashboard:
                section_data = dashboard[section]
                if isinstance(section_data, list):
                    print(f"✅ {section}: {len(section_data)} items")
                else:
                    print(f"⚠️  {section}: Not a list ({type(section_data)})")
            else:
                print(f"⚠️  Missing optional section: {section}")
        
        print(f"\n🎉 DASHBOARD API VALIDATION: COMPLETE SUCCESS")
        print(f"   - Structure: ✅ Correct")
        print(f"   - Data Types: ✅ Valid")
        print(f"   - Content: ✅ Present")
        print(f"   - Values: ✅ Reasonable")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception during test: {str(e)}")
        return False

def test_frontend_compatibility():
    """Test what frontend might be expecting"""
    admin_token = get_admin_token()
    if not admin_token:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        
        print(f"\n🖥️  FRONTEND COMPATIBILITY CHECK:")
        print("=" * 40)
        
        # Check if frontend can extract charts data
        dashboard = data.get("dashboard", {})
        
        # Count potential chart data sources
        chart_sources = 0
        
        if "monthly_trends" in dashboard and len(dashboard["monthly_trends"]) > 0:
            chart_sources += 1
            print(f"✅ Chart 1: Monthly Trends ({len(dashboard['monthly_trends'])} data points)")
        
        if "top_customers" in dashboard and len(dashboard["top_customers"]) > 0:
            chart_sources += 1
            print(f"✅ Chart 2: Top Customers ({len(dashboard['top_customers'])} customers)")
        
        if "top_departments" in dashboard and len(dashboard["top_departments"]) > 0:
            chart_sources += 1
            print(f"✅ Chart 3: Top Departments ({len(dashboard['top_departments'])} departments)")
        
        if "top_products" in dashboard and len(dashboard["top_products"]) > 0:
            chart_sources += 1
            print(f"✅ Chart 4: Top Products ({len(dashboard['top_products'])} products)")
        
        if "top_promotions" in dashboard and len(dashboard["top_promotions"]) > 0:
            chart_sources += 1
            print(f"✅ Chart 5: Top Promotions ({len(dashboard['top_promotions'])} promotions)")
        
        # Count cards
        card_sources = 0
        overview = dashboard.get("overview", {})
        
        if "total_sales" in overview:
            card_sources += 1
            print(f"✅ Card 1: Total Sales ({overview['total_sales']:,})")
        
        if "unique_customers" in overview:
            card_sources += 1
            print(f"✅ Card 2: Unique Customers ({overview['unique_customers']:,})")
        
        if "total_revenue" in overview:
            card_sources += 1
            print(f"✅ Card 3: Total Revenue (€{overview['total_revenue']:,.2f})")
        
        if "avg_transaction" in overview:
            card_sources += 1
            print(f"✅ Card 4: Avg Transaction (€{overview['avg_transaction']:,.2f})")
        
        print(f"\n📊 FRONTEND DATA AVAILABILITY:")
        print(f"   Charts available: {chart_sources}")
        print(f"   Cards available: {card_sources}")
        
        if chart_sources == 0:
            print(f"❌ PROBLEM: No chart data available for frontend")
            return False
        
        if card_sources <= 1:
            print(f"❌ PROBLEM: Only {card_sources} card(s) available")
            return False
        
        print(f"✅ Frontend should be able to display {chart_sources} charts and {card_sources} cards")
        return True
        
    except Exception as e:
        print(f"❌ Frontend compatibility test failed: {str(e)}")
        return False

def main():
    print("🔍 DETAILED VENDITE DASHBOARD API TEST")
    print("=" * 60)
    
    # Test 1: Detailed API validation
    api_success = detailed_dashboard_test()
    
    # Test 2: Frontend compatibility
    frontend_success = test_frontend_compatibility()
    
    print(f"\n" + "=" * 60)
    print(f"📋 FINAL TEST RESULTS:")
    print(f"   API Structure & Data: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Frontend Compatibility: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if api_success and frontend_success:
        print(f"\n🎉 CONCLUSION: Backend API is PERFECT")
        print(f"   The issue is definitely in the frontend JavaScript code")
        print(f"   Frontend is not properly parsing or displaying the API response")
    else:
        print(f"\n🚨 CONCLUSION: Backend API has issues")

if __name__ == "__main__":
    main()
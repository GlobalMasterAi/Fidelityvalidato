#!/usr/bin/env python3
"""
Focused test for Admin Dashboard Card Endpoints
Tests the three specific API endpoints that provide data for dashboard cards
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
    """Login as super admin to get access token"""
    try:
        login_data = {
            "username": "superadmin",
            "password": "ImaGross2024!"
        }
        
        response = requests.post(f"{API_BASE}/admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Super admin login successful")
            return data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login exception: {str(e)}")
        return None

def test_admin_dashboard_card_endpoints():
    """Test the three specific API endpoints for Admin Dashboard cards"""
    print("\n🎯 TESTING ADMIN DASHBOARD CARD ENDPOINTS")
    print("=" * 60)
    
    # First login as admin
    admin_token = test_admin_login()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    results = []
    
    # Test 1: Admin Stats Dashboard API (/api/admin/stats/dashboard)
    print("\n1️⃣ Testing Admin Stats Dashboard API")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: 200 OK")
            
            # Check for required fields for dashboard cards
            required_fields = ["total_users", "total_stores", "total_cashiers"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                results.append(("Admin Stats Dashboard API", False, f"Missing fields: {missing_fields}"))
            else:
                print(f"✅ Basic fields present: {data['total_users']} users, {data['total_stores']} stores, {data['total_cashiers']} cashiers")
                
                # Check if vendite_stats exists with unique_products and unique_customers
                if "vendite_stats" in data:
                    vendite_stats = data["vendite_stats"]
                    if "unique_products" in vendite_stats and "unique_customers_vendite" in vendite_stats:
                        print(f"✅ Vendite stats present: {vendite_stats.get('unique_products', 0)} products, {vendite_stats.get('unique_customers_vendite', 0)} customers")
                        results.append(("Admin Stats Dashboard API", True, f"Complete data available"))
                    else:
                        print(f"❌ vendite_stats missing unique_products or unique_customers_vendite: {list(vendite_stats.keys())}")
                        results.append(("Admin Stats Dashboard API", False, f"vendite_stats incomplete"))
                else:
                    print(f"❌ Missing vendite_stats field needed for Products card")
                    results.append(("Admin Stats Dashboard API", False, "Missing vendite_stats"))
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            print(f"❌ Status {response.status_code}: {error_detail}")
            results.append(("Admin Stats Dashboard API", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Admin Stats Dashboard API", False, f"Exception: {str(e)}"))
    
    # Test 2: Vendite Dashboard API (/api/admin/vendite/dashboard)
    print("\n2️⃣ Testing Vendite Dashboard API")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: 200 OK")
            
            # Check for proper structure with overview data
            if "success" in data and data["success"]:
                print(f"✅ Success flag: {data['success']}")
                
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    print(f"✅ Dashboard object present")
                    
                    # Check for cards structure with required fields
                    if "cards" in dashboard:
                        cards = dashboard["cards"]
                        required_card_fields = ["total_revenue", "total_sales", "unique_customers", "avg_transaction"]
                        missing_card_fields = [field for field in required_card_fields if field not in cards]
                        
                        if missing_card_fields:
                            print(f"❌ Missing card fields: {missing_card_fields}")
                            results.append(("Vendite Dashboard API", False, f"Missing card fields: {missing_card_fields}"))
                        else:
                            print(f"✅ All card fields present:")
                            print(f"   - Revenue: €{cards.get('total_revenue', 0):,.2f}")
                            print(f"   - Sales: {cards.get('total_sales', 0):,}")
                            print(f"   - Customers: {cards.get('unique_customers', 0):,}")
                            print(f"   - Avg Transaction: €{cards.get('avg_transaction', 0):.2f}")
                            results.append(("Vendite Dashboard API", True, "Complete sales data available"))
                    else:
                        print(f"❌ Missing 'cards' structure in dashboard response")
                        print(f"   Available keys: {list(dashboard.keys())}")
                        results.append(("Vendite Dashboard API", False, "Missing cards structure"))
                else:
                    print(f"❌ Missing 'dashboard' field in response")
                    print(f"   Available keys: {list(data.keys())}")
                    results.append(("Vendite Dashboard API", False, "Missing dashboard field"))
            else:
                print(f"❌ API returned success=false or missing success field")
                print(f"   Response keys: {list(data.keys())}")
                results.append(("Vendite Dashboard API", False, "Success flag missing or false"))
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            print(f"❌ Status {response.status_code}: {error_detail}")
            results.append(("Vendite Dashboard API", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Vendite Dashboard API", False, f"Exception: {str(e)}"))
    
    # Test 3: Scontrini Stats API (/api/admin/scontrini/stats)
    print("\n3️⃣ Testing Scontrini Stats API")
    print("-" * 40)
    try:
        response = requests.get(f"{API_BASE}/admin/scontrini/stats", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: 200 OK")
            
            # Check for required loyalty data fields - data is nested under 'stats'
            if "stats" in data:
                stats = data["stats"]
                required_fields = ["total_bollini", "total_scontrini"]
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    print(f"❌ Missing required fields in stats: {missing_fields}")
                    print(f"   Available keys in stats: {list(stats.keys())}")
                    results.append(("Scontrini Stats API", False, f"Missing fields in stats: {missing_fields}"))
                else:
                    print(f"✅ All loyalty fields present in stats:")
                    print(f"   - Total Bollini: {stats.get('total_bollini', 0):,}")
                    print(f"   - Total Scontrini: {stats.get('total_scontrini', 0):,}")
                    results.append(("Scontrini Stats API", True, "Complete loyalty data available"))
            else:
                print(f"❌ Missing 'stats' object in response")
                print(f"   Available keys: {list(data.keys())}")
                results.append(("Scontrini Stats API", False, "Missing stats object"))
        else:
            error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
            print(f"❌ Status {response.status_code}: {error_detail}")
            results.append(("Scontrini Stats API", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Scontrini Stats API", False, f"Exception: {str(e)}"))
    
    # Test 4: Data Integration Test - Verify all required fields for dashboard cards
    print("\n4️⃣ Dashboard Card Data Integration Test")
    print("-" * 40)
    
    try:
        # Get all three endpoints data
        stats_response = requests.get(f"{API_BASE}/admin/stats/dashboard", headers=headers)
        vendite_response = requests.get(f"{API_BASE}/admin/vendite/dashboard", headers=headers)
        scontrini_response = requests.get(f"{API_BASE}/admin/scontrini/stats", headers=headers)
        
        if all(r.status_code == 200 for r in [stats_response, vendite_response, scontrini_response]):
            stats_data = stats_response.json()
            vendite_data = vendite_response.json()
            scontrini_data = scontrini_response.json()
            
            print("✅ All three APIs responded successfully")
            
            # Extract data for each dashboard card
            card_data = {}
            
            # Customers count (from vendite)
            if "dashboard" in vendite_data and "cards" in vendite_data["dashboard"]:
                card_data["customers"] = vendite_data["dashboard"]["cards"].get("unique_customers", 0)
                print(f"✅ Customers data: {card_data['customers']:,}")
            else:
                card_data["customers"] = "MISSING"
                print(f"❌ Customers data: MISSING")
            
            # Products count (from admin stats vendite_stats)
            if "vendite_stats" in stats_data:
                card_data["products"] = stats_data["vendite_stats"].get("unique_products", 0)
                print(f"✅ Products data: {card_data['products']:,}")
            else:
                card_data["products"] = "MISSING"
                print(f"❌ Products data: MISSING")
            
            # Revenue data (from vendite)
            if "dashboard" in vendite_data and "cards" in vendite_data["dashboard"]:
                card_data["revenue"] = vendite_data["dashboard"]["cards"].get("total_revenue", 0)
                print(f"✅ Revenue data: €{card_data['revenue']:,.2f}")
            else:
                card_data["revenue"] = "MISSING"
                print(f"❌ Revenue data: MISSING")
            
            # Bollini count (from scontrini)
            card_data["bollini"] = scontrini_data.get("total_bollini", 0)
            print(f"✅ Bollini data: {card_data['bollini']:,}")
            
            # Check if all required data is available
            missing_data = [key for key, value in card_data.items() if value == "MISSING"]
            
            if missing_data:
                print(f"❌ Missing data for cards: {missing_data}")
                results.append(("Dashboard Card Data Integration", False, f"Missing data for: {missing_data}"))
            else:
                print(f"✅ ALL DASHBOARD CARD DATA AVAILABLE!")
                print(f"   📊 Summary:")
                print(f"   - Customers: {card_data['customers']:,}")
                print(f"   - Products: {card_data['products']:,}")
                print(f"   - Revenue: €{card_data['revenue']:,.2f}")
                print(f"   - Bollini: {card_data['bollini']:,}")
                results.append(("Dashboard Card Data Integration", True, "All card data available"))
        else:
            failed_apis = []
            if stats_response.status_code != 200:
                failed_apis.append(f"stats({stats_response.status_code})")
            if vendite_response.status_code != 200:
                failed_apis.append(f"vendite({vendite_response.status_code})")
            if scontrini_response.status_code != 200:
                failed_apis.append(f"scontrini({scontrini_response.status_code})")
            
            print(f"❌ One or more API endpoints failed: {', '.join(failed_apis)}")
            results.append(("Dashboard Card Data Integration", False, f"Failed APIs: {failed_apis}"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Dashboard Card Data Integration", False, f"Exception: {str(e)}"))
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 ADMIN DASHBOARD CARD ENDPOINTS TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for test_name, success, message in results:
            if not success:
                print(f"  - {test_name}: {message}")
    else:
        print("\n🎉 ALL ADMIN DASHBOARD CARD ENDPOINTS WORKING PERFECTLY!")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_admin_dashboard_card_endpoints()
    sys.exit(0 if success else 1)
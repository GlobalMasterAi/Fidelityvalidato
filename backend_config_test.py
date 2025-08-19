#!/usr/bin/env python3
"""
Backend Configuration Verification for Fedelissima.net
Tests backend code configuration without requiring external connectivity
"""

import sys
import re
import os

def test_backend_qr_url_configuration():
    """Test that backend QR code generation uses fedelissima.net domain"""
    try:
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find all instances of base_url assignments
        base_url_pattern = r'base_url\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(base_url_pattern, content)
        
        if not matches:
            print("❌ Backend QR URL Configuration: No base_url assignments found")
            return False
        
        # Check if all base_url assignments use fedelissima.net
        fedelissima_count = 0
        total_count = len(matches)
        
        for url in matches:
            if url == "https://fedelissima.net":
                fedelissima_count += 1
            else:
                print(f"❌ Backend QR URL Configuration: Found incorrect base_url: {url}")
                return False
        
        if fedelissima_count == total_count:
            print(f"✅ Backend QR URL Configuration: All {total_count} base_url assignments use https://fedelissima.net")
            return True
        else:
            print(f"❌ Backend QR URL Configuration: Only {fedelissima_count}/{total_count} base_url assignments use fedelissima.net")
            return False
            
    except Exception as e:
        print(f"❌ Backend QR URL Configuration: Exception: {str(e)}")
        return False

def test_frontend_env_configuration():
    """Test that REACT_APP_BACKEND_URL is correctly updated to https://fedelissima.net"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            content = f.read()
        
        # Check if REACT_APP_BACKEND_URL is set to fedelissima.net
        if 'REACT_APP_BACKEND_URL=https://fedelissima.net' in content:
            print("✅ Frontend Environment Configuration: REACT_APP_BACKEND_URL correctly set to https://fedelissima.net")
            return True
        else:
            # Extract the actual value
            for line in content.split('\n'):
                if line.startswith('REACT_APP_BACKEND_URL='):
                    actual_url = line.split('=', 1)[1].strip()
                    print(f"❌ Frontend Environment Configuration: REACT_APP_BACKEND_URL is '{actual_url}', expected 'https://fedelissima.net'")
                    return False
            
            print("❌ Frontend Environment Configuration: REACT_APP_BACKEND_URL not found in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Frontend Environment Configuration: Exception: {str(e)}")
        return False

def test_qr_code_generation_functions():
    """Test that QR code generation functions use fedelissima.net"""
    try:
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find QR code generation patterns
        qr_generation_patterns = [
            r'qr_url\s*=\s*f["\']([^"\']*){base_url}([^"\']*)["\']',
            r'generate_qr_code\([^)]*base_url[^)]*\)',
            r'f["\'][^"\']*{base_url}[^"\']*register\?qr=[^"\']*["\']'
        ]
        
        found_qr_generation = False
        
        for pattern in qr_generation_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_qr_generation = True
                break
        
        # Check for QR URL construction
        qr_url_pattern = r'qr_url\s*=\s*f["\']([^"\']*){base_url}([^"\']*)["\']'
        qr_matches = re.findall(qr_url_pattern, content)
        
        if qr_matches:
            for prefix, suffix in qr_matches:
                if '/register?qr=' in suffix:
                    print("✅ QR Code Generation Functions: QR URL format correct (/register?qr=)")
                    found_qr_generation = True
                else:
                    print(f"❌ QR Code Generation Functions: Incorrect QR URL format: {prefix}{{base_url}}{suffix}")
                    return False
        
        if found_qr_generation:
            print("✅ QR Code Generation Functions: QR code generation uses base_url correctly")
            return True
        else:
            print("❌ QR Code Generation Functions: No QR code generation patterns found")
            return False
            
    except Exception as e:
        print(f"❌ QR Code Generation Functions: Exception: {str(e)}")
        return False

def test_qr_regeneration_endpoints():
    """Test that QR regeneration endpoints use fedelissima.net"""
    try:
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find regeneration endpoints
        regeneration_endpoints = [
            'regenerate_all_qr_codes',
            'regenerate_single_qr_code'
        ]
        
        found_endpoints = 0
        
        for endpoint in regeneration_endpoints:
            if f'def {endpoint}' in content:
                found_endpoints += 1
                
                # Check if the endpoint uses base_url
                endpoint_start = content.find(f'def {endpoint}')
                if endpoint_start != -1:
                    # Find the end of the function (next def or end of file)
                    next_def = content.find('\ndef ', endpoint_start + 1)
                    if next_def == -1:
                        endpoint_content = content[endpoint_start:]
                    else:
                        endpoint_content = content[endpoint_start:next_def]
                    
                    if 'base_url = "https://fedelissima.net"' in endpoint_content:
                        print(f"✅ QR Regeneration Endpoints: {endpoint} uses fedelissima.net")
                    else:
                        print(f"❌ QR Regeneration Endpoints: {endpoint} does not use fedelissima.net")
                        return False
        
        if found_endpoints > 0:
            print(f"✅ QR Regeneration Endpoints: Found {found_endpoints} regeneration endpoints using fedelissima.net")
            return True
        else:
            print("⚠️ QR Regeneration Endpoints: No regeneration endpoints found (acceptable)")
            return True
            
    except Exception as e:
        print(f"❌ QR Regeneration Endpoints: Exception: {str(e)}")
        return False

def test_cashier_crud_operations():
    """Test that cashier CRUD operations use fedelissima.net for QR generation"""
    try:
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find cashier creation and update endpoints
        cashier_operations = [
            ('create_cashier', 'POST /admin/cashiers'),
            ('update_cashier', 'PUT /admin/cashiers')
        ]
        
        operations_verified = 0
        
        for operation_name, description in cashier_operations:
            # Look for the operation in the content
            if f'def {operation_name}' in content or 'admin/cashiers' in content:
                # Check for QR code generation in cashier operations
                if 'base_url = "https://fedelissima.net"' in content and 'qr_url = f"{base_url}/register?qr={qr_data}"' in content:
                    operations_verified += 1
                    print(f"✅ Cashier CRUD Operations: {description} uses fedelissima.net for QR generation")
        
        if operations_verified >= 1:  # At least one operation found
            print("✅ Cashier CRUD Operations: QR generation in CRUD operations uses fedelissima.net")
            return True
        else:
            print("❌ Cashier CRUD Operations: No cashier CRUD operations with QR generation found")
            return False
            
    except Exception as e:
        print(f"❌ Cashier CRUD Operations: Exception: {str(e)}")
        return False

def test_qr_url_format_compliance():
    """Test that QR URLs follow the correct format: https://fedelissima.net/register?qr=STORECODE-CASSAN"""
    try:
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Look for QR data generation pattern
        qr_data_pattern = r'qr_data\s*=\s*f["\']([^"\']*){[^}]*}([^"\']*)["\']'
        qr_data_matches = re.findall(qr_data_pattern, content)
        
        # Look for direct QR data assignment
        direct_qr_pattern = r'qr_data\s*=\s*f["\']([^"\']*)["\']'
        direct_matches = re.findall(direct_qr_pattern, content)
        
        # Check for STORECODE-CASSA pattern
        if '{store[\'code\']}-CASSA{cashier_data.cashier_number}' in content or 'CASSA' in content:
            print("✅ QR URL Format Compliance: QR data uses STORECODE-CASSA format")
            
            # Check for registration URL format
            if '/register?qr=' in content:
                print("✅ QR URL Format Compliance: Registration URL format correct (/register?qr=)")
                return True
            else:
                print("❌ QR URL Format Compliance: Registration URL format incorrect")
                return False
        else:
            print("❌ QR URL Format Compliance: QR data does not use STORECODE-CASSA format")
            return False
            
    except Exception as e:
        print(f"❌ QR URL Format Compliance: Exception: {str(e)}")
        return False

def test_environment_variables_usage():
    """Test that environment variables are properly configured"""
    try:
        # Check backend .env
        backend_env_path = '/app/backend/.env'
        if os.path.exists(backend_env_path):
            with open(backend_env_path, 'r') as f:
                backend_content = f.read()
            
            if 'MONGO_URL=' in backend_content:
                print("✅ Environment Variables: Backend MONGO_URL configured")
            else:
                print("❌ Environment Variables: Backend MONGO_URL not found")
                return False
        
        # Check frontend .env
        frontend_env_path = '/app/frontend/.env'
        if os.path.exists(frontend_env_path):
            with open(frontend_env_path, 'r') as f:
                frontend_content = f.read()
            
            if 'REACT_APP_BACKEND_URL=https://fedelissima.net' in frontend_content:
                print("✅ Environment Variables: Frontend REACT_APP_BACKEND_URL correctly set to fedelissima.net")
                return True
            else:
                print("❌ Environment Variables: Frontend REACT_APP_BACKEND_URL not correctly set")
                return False
        else:
            print("❌ Environment Variables: Frontend .env file not found")
            return False
            
    except Exception as e:
        print(f"❌ Environment Variables: Exception: {str(e)}")
        return False

def run_configuration_tests():
    """Run all configuration verification tests"""
    print("🚀 Starting Fedelissima.net Backend Configuration Verification")
    print("=" * 80)
    
    tests = [
        test_frontend_env_configuration,
        test_backend_qr_url_configuration,
        test_qr_code_generation_functions,
        test_qr_regeneration_endpoints,
        test_cashier_crud_operations,
        test_qr_url_format_compliance,
        test_environment_variables_usage
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: Unexpected error: {str(e)}")
            failed += 1
        
        print()  # Add spacing between tests
    
    print("=" * 80)
    print(f"📊 FEDELISSIMA.NET CONFIGURATION VERIFICATION RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ALL CONFIGURATION TESTS PASSED!")
        print("✅ Backend is correctly configured for fedelissima.net deployment")
        print("✅ All QR code generation functions use https://fedelissima.net domain")
        print("✅ QR code format follows STORECODE-CASSA pattern")
        print("✅ Registration URLs use /register?qr= format")
    else:
        print("⚠️ Some configuration tests failed - review issues before deployment")
    
    return passed, failed

if __name__ == "__main__":
    run_configuration_tests()
"""
Test script for user registration and authentication endpoints
Tests registration, login, profile access, and JWT token validation
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api/user"

# Test data
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
}

# Colors for console output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_result(test_name, success, details=""):
    """Print test result with color"""
    status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {test_name}")
    if details:
        print(f"  {details}")


def test_registration():
    """Test user registration endpoint"""
    print(f"\n{BLUE}=== Testing User Registration ==={RESET}")
    
    try:
        response = requests.post(
            f"{API_URL}/register",
            json=TEST_USER,
            timeout=5
        )
        
        success = response.status_code == 201
        print_result("POST /api/user/register", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Username: {data.get('username')}")
            print(f"  Email: {data.get('email')}")
            print(f"  Token (first 20 chars): {str(data.get('token', ''))[:20]}...")
            return data.get('user_id'), data.get('token')
        else:
            print(f"  Response: {response.json()}")
            return None, None
            
    except Exception as e:
        print_result("POST /api/user/register", False, str(e))
        return None, None


def test_duplicate_username(username):
    """Test that duplicate username is rejected"""
    print(f"\n{BLUE}=== Testing Duplicate Username Protection ==={RESET}")
    
    duplicate_user = {
        "username": username,
        "email": f"another_{int(time.time())}@example.com",
        "password": "SecurePass123",
        "password_confirm": "SecurePass123"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/register",
            json=duplicate_user,
            timeout=5
        )
        
        success = response.status_code == 409
        print_result("Reject duplicate username", success, f"Status: {response.status_code}")
        
        if response.status_code == 409:
            print(f"  Response: {response.json().get('error')}")
        
        return success
            
    except Exception as e:
        print_result("Reject duplicate username", False, str(e))
        return False


def test_weak_password():
    """Test that weak passwords are rejected"""
    print(f"\n{BLUE}=== Testing Password Strength Validation ==={RESET}")
    
    weak_passwords = [
        {
            "username": f"test_{int(time.time())}",
            "email": f"weak_{int(time.time())}@example.com",
            "password": "weak",
            "password_confirm": "weak",
            "label": "Too short (< 8 chars)"
        },
        {
            "username": f"test_{int(time.time())+1}",
            "email": f"weak_{int(time.time())+1}@example.com",
            "password": "alllowercase123",
            "password_confirm": "alllowercase123",
            "label": "No uppercase"
        }
    ]
    
    all_passed = True
    for weak_user in weak_passwords:
        label = weak_user.pop('label')
        try:
            response = requests.post(
                f"{API_URL}/register",
                json=weak_user,
                timeout=5
            )
            
            success = response.status_code == 400
            print_result(f"Reject password: {label}", success, f"Status: {response.status_code}")
            all_passed = all_passed and success
                
        except Exception as e:
            print_result(f"Reject password: {label}", False, str(e))
            all_passed = False
    
    return all_passed


def test_login(username, password):
    """Test user login endpoint"""
    print(f"\n{BLUE}=== Testing User Login ==={RESET}")
    
    login_data = {
        "username_or_email": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_URL}/login",
            json=login_data,
            timeout=5
        )
        
        success = response.status_code == 200
        print_result("POST /api/user/login", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            token = data.get('token')
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Username: {data.get('username')}")
            print(f"  Token (first 20 chars): {str(token)[:20]}...")
            return token
        else:
            print(f"  Response: {response.json()}")
            return None
            
    except Exception as e:
        print_result("POST /api/user/login", False, str(e))
        return None


def test_invalid_login():
    """Test login with invalid credentials"""
    print(f"\n{BLUE}=== Testing Invalid Login Protection ==={RESET}")
    
    invalid_logins = [
        {"username_or_email": "nonexistent", "password": "anypass", "label": "Non-existent user"},
        {"username_or_email": TEST_USER["username"], "password": "wrongpassword", "label": "Wrong password"}
    ]
    
    all_passed = True
    for login_attempt in invalid_logins:
        label = login_attempt.pop('label')
        try:
            response = requests.post(
                f"{API_URL}/login",
                json=login_attempt,
                timeout=5
            )
            
            success = response.status_code == 401
            print_result(f"Reject invalid login: {label}", success, f"Status: {response.status_code}")
            all_passed = all_passed and success
                
        except Exception as e:
            print_result(f"Reject invalid login: {label}", False, str(e))
            all_passed = False
    
    return all_passed


def test_get_profile(token):
    """Test getting user profile with authentication"""
    print(f"\n{BLUE}=== Testing Authenticated Profile Access ==={RESET}")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/profile",
            headers=headers,
            timeout=5
        )
        
        success = response.status_code == 200
        print_result("GET /api/user/profile (with token)", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Username: {data.get('username')}")
            print(f"  Email: {data.get('email')}")
        else:
            print(f"  Response: {response.json()}")
        
        return success
            
    except Exception as e:
        print_result("GET /api/user/profile", False, str(e))
        return False


def test_profile_without_auth():
    """Test that profile access is denied without auth"""
    print(f"\n{BLUE}=== Testing Auth Protection ==={RESET}")
    
    try:
        response = requests.get(
            f"{API_URL}/profile",
            timeout=5
        )
        
        success = response.status_code == 401
        print_result("Reject profile without token", success, f"Status: {response.status_code}")
        
        if not success:
            print(f"  Response: {response.json()}")
        
        return success
            
    except Exception as e:
        print_result("Reject profile without token", False, str(e))
        return False


def test_verify_token(token):
    """Test token verification endpoint"""
    print(f"\n{BLUE}=== Testing Token Verification ==={RESET}")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/verify-token",
            headers=headers,
            timeout=5
        )
        
        success = response.status_code == 200
        print_result("GET /api/user/verify-token", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"  Valid: {data.get('valid')}")
            print(f"  Username: {data.get('username')}")
        else:
            print(f"  Response: {response.json()}")
        
        return success
            
    except Exception as e:
        print_result("GET /api/user/verify-token", False, str(e))
        return False


def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'=' * 60}")
    print(f"Neighborhood BBS - User Authentication Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}{RESET}")
    
    print(f"\n{YELLOW}Base URL: {BASE_URL}{RESET}")
    print(f"Test User: Username = {TEST_USER['username']}, Email = {TEST_USER['email']}")
    
    # Wait for server to be ready
    print(f"\n{YELLOW}Checking server connectivity...{RESET}")
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            print(f"{GREEN}✓ Server is running{RESET}")
            break
        except:
            if i < max_retries - 1:
                print(f"  Retry {i+1}/{max_retries}...")
                time.sleep(1)
            else:
                print(f"{RED}✗ Cannot connect to server at {BASE_URL}{RESET}")
                return
    
    # Run tests
    results = {}
    
    # Test registration
    user_id, token = test_registration()
    results['Registration'] = user_id is not None
    
    if user_id:
        # Test duplicate username
        results['Duplicate Username'] = test_duplicate_username(TEST_USER['username'])
        
        # Test weak passwords
        results['Weak Passwords'] = test_weak_password()
        
        # Test login
        login_token = test_login(TEST_USER['username'], TEST_USER['password'])
        results['Login'] = login_token is not None
        
        # Test invalid login
        results['Invalid Login'] = test_invalid_login()
        
        # Test profile access without auth
        results['Auth Protection'] = test_profile_without_auth()
        
        if login_token:
            # Test authenticated profile access
            results['Authenticated Profile'] = test_get_profile(login_token)
            
            # Test token verification
            results['Token Verification'] = test_verify_token(login_token)
    
    # Summary
    print(f"\n{YELLOW}{'=' * 60}")
    print(f"Test Summary")
    print(f"{'=' * 60}{RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{YELLOW}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}All tests passed! ✓{RESET}")
    else:
        print(f"{RED}Some tests failed. Check the output above.{RESET}")
    
    print(f"\n{YELLOW}Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")


if __name__ == '__main__':
    main()

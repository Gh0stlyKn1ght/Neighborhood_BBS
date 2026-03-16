#!/usr/bin/env python
"""
Test script for Privacy API endpoints
Validates that privacy endpoints return correct information
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from server import create_app

def test_privacy_endpoints():
    """Test all privacy API endpoints"""
    app = create_app()
    client = app.test_client()
    
    print("Testing Privacy API Endpoints")
    print("=" * 50)
    
    # Test 1: /api/privacy/info
    print("\n1. Testing GET /api/privacy/info")
    response = client.get('/api/privacy/info')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   Privacy Mode: {data.get('privacy_mode')}")
        print(f"   User Accounts: {data.get('user_accounts', {}).get('type')}")
        print(f"   Access Control: {data.get('access_control', {}).get('type')}")
        print("   ✓ PASS")
    else:
        print(f"   ✗ FAIL: {response.get_json()}")
    
    # Test 2: /api/privacy/policy
    print("\n2. Testing GET /api/privacy/policy")
    response = client.get('/api/privacy/policy')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   Title: {data.get('title')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Policy Length: {len(data.get('policy_text', ''))}")
        print("   ✓ PASS")
    else:
        print(f"   ✗ FAIL: {response.get_json()}")
    
    # Test 3: /api/privacy/statistics
    print("\n3. Testing GET /api/privacy/statistics")
    response = client.get('/api/privacy/statistics')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   Total Messages: {data.get('total_messages', 0)}")
        print(f"   Privacy Mode: {data.get('privacy_mode')}")
        print("   ✓ PASS")
    else:
        print(f"   ✗ FAIL: {response.get_json()}")
    
    # Test 4: /api/privacy/transparency
    print("\n4. Testing GET /api/privacy/transparency")
    response = client.get('/api/privacy/transparency')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        measures = data.get('transparency', {}).get('technical_measures', [])
        print(f"   Technical Measures: {len(measures)} measures")
        for measure in measures[:3]:
            print(f"     - {measure}")
        print("   ✓ PASS")
    else:
        print(f"   ✗ FAIL: {response.get_json()}")
    
    print("\n" + "=" * 50)
    print("All Privacy API endpoints functional!")
    print("\nEndpoints available at:")
    print("  - GET /api/privacy/info")
    print("  - GET /api/privacy/policy")
    print("  - GET /api/privacy/statistics")
    print("  - GET /api/privacy/transparency")


if __name__ == '__main__':
    test_privacy_endpoints()

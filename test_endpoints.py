#!/usr/bin/env python
"""
Endpoint testing script to verify security fixes in HTTP routes.
This tests real-world scenarios after the security fixes.
"""

import sys
import os
sys.path.insert(0, 'server/src')

# Setup environment
os.environ['SECRET_KEY'] = 'test-secret-key-' + '0' * 32
os.environ['JWT_SECRET'] = 'test-secret-key-' + '0' * 32
os.environ['FLASK_ENV'] = 'development'  # Use test admin password

from server import create_app
from models import Database


def ensure_setup_complete():
    """Ensure setup middleware won't redirect protected endpoints during tests."""
    db_instance = Database()
    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setup_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            encrypted BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute(
        'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
        ('setup_complete', 'true')
    )
    conn.commit()
    conn.close()

print('=' * 70)
print('NEIGHBORHOOD BBS - ENDPOINT SECURITY TESTING')
print('=' * 70)
print()

# Ensure predictable app behavior for endpoint tests
ensure_setup_complete()

# Create test app
app = create_app()
client = app.test_client()

# Initialize database for testing
db_instance = Database()
db = db_instance.get_connection()
db.execute('DELETE FROM sessions')  # Clear test sessions
db.commit()

test_results = []

print('=== SECTION 1: Authentication Endpoints ===')
print()

# Test 1: POST /api/user/join (nickname collision)
print('Test 1: Nickname collision prevention')
try:
    # Create first user
    response1 = client.post('/api/user/join',
        json={'nickname': 'TestUser'},
        content_type='application/json'
    )
    assert response1.status_code in [200, 201], f"First user creation failed: {response1.status_code}"
    
    # Try to create second user with same nickname
    response2 = client.post('/api/user/join',
        json={'nickname': 'TestUser'},
        content_type='application/json'
    )
    
    if response2.status_code == 409 or (response2.status_code == 400 and 'nickname_taken' in response2.get_json().get('error', '')):
        print('  ✓ Nickname collision correctly rejected (HTTP 409 or error: nickname_taken)')
        test_results.append(('endpoint.nickname_collision', True, None))
    else:
        print(f'  ⚠ Nickname collision handling: {response2.status_code} - {response2.get_json()}')
        test_results.append(('endpoint.nickname_collision', False, f'Status {response2.status_code}'))
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.nickname_collision', False, str(e)))

print()

# Test 2: CSRF + Admin protection on protected endpoint
print('Test 2: CSRF and admin protection (DELETE /api/board/posts/<id>)')
try:
    # 2a) Missing CSRF should be blocked before auth
    no_csrf = client.delete('/api/board/posts/999',
        content_type='application/json'
    )

    # 2b) With CSRF token, request should pass CSRF and then fail admin auth
    csrf_resp = client.get('/api/csrf/token')
    csrf_token = (csrf_resp.get_json() or {}).get('csrf_token')
    with_csrf = client.delete('/api/board/posts/999',
        content_type='application/json',
        headers={'X-CSRF-Token': csrf_token} if csrf_token else {}
    )

    if no_csrf.status_code == 403 and with_csrf.status_code in [401, 403]:
        print(f'  ✓ DELETE /posts enforces CSRF (403) then auth (HTTP {with_csrf.status_code})')
        test_results.append(('endpoint.admin_auth', True, None))
    else:
        print(
            '  ⚠ Unexpected protection behavior: '
            f'missing_csrf={no_csrf.status_code}, with_csrf={with_csrf.status_code}'
        )
        test_results.append(
            ('endpoint.admin_auth', False, f'missing_csrf={no_csrf.status_code}, with_csrf={with_csrf.status_code}')
        )
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.admin_auth', False, str(e)))

print()

# Test 3: Error responses don't leak internal details
print('Test 3: Error responses don\'t leak exception details')
try:
    # Trigger a controlled server-side exception path (invalid JSON body)
    response = client.post('/api/admin/login',
        data='not-json',
        content_type='text/plain'
    )
    
    response_data = response.get_json() or {}
    response_text = str(response_data)
    
    # Check that response doesn't contain Python exception details
    bad_keywords = [
        'Traceback',
        'File "',
        'line ',
        'TypeError',
        'KeyError',
        'AttributeError',
        'IndexError',
        'sqlite3.OperationalError',
        'ConnectionError',
        '.py',
        'Exception:',
    ]
    
    has_leak = any(keyword in response_text for keyword in bad_keywords)
    
    if not has_leak:
        print(f'  ✓ Error response is sanitized (no exception leaks)')
        test_results.append(('endpoint.error_sanitization', True, None))
    else:
        print(f'  ✗ Error response leaks details: {response_text[:100]}...')
        test_results.append(('endpoint.error_sanitization', False, 'Exception details visible'))
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.error_sanitization', False, str(e)))

print()

print('=== SECTION 2: Session Security ===')
print()

# Test 4: Session cookie flags
print('Test 4: Session cookie flags')
try:
    response = client.post('/api/user/join',
        json={'nickname': 'CookieTest'},
        content_type='application/json'
    )
    
    set_cookie_header = response.headers.get('Set-Cookie', '')
    
    checks = {
        'HttpOnly': 'HttpOnly' in set_cookie_header,
        'SameSite': 'SameSite' in set_cookie_header,
        'Secure (if HTTPS)': True,  # Will be enforced in production
    }
    
    if checks['HttpOnly'] and checks['SameSite']:
        print(f'  ✓ Session cookies have HttpOnly and SameSite flags')
        test_results.append(('endpoint.cookie_flags', True, None))
    else:
        print(f'  ⚠ Cookie security flags: {checks}')
        test_results.append(('endpoint.cookie_flags', False, str(checks)))
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.cookie_flags', False, str(e)))

print()

print('=== SECTION 3: Password Security ===')
print()

# Test 5: Admin password validation
print('Test 5: Admin password handling doesn\'t leak hints')
try:
    # Endpoint requires X-Admin-Password; response must not include hint fields
    response = client.get('/api/auth/admin/passcode-status')

    response_data = response.get_json() or {}

    if 'hint' not in response_data:
        print('  ✓ Admin auth response doesn\'t leak hints')
        test_results.append(('endpoint.password_hints', True, None))
    else:
        print(f'  ✗ Admin auth response contains hint: {response_data.get("hint")}')
        test_results.append(('endpoint.password_hints', False, 'Hint field present'))
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.password_hints', False, str(e)))

print()

print('=== SECTION 4: HTTP Headers Security ===')
print()

# Test 6: No deprecated security headers
print('Test 6: No deprecated X-XSS-Protection header')
try:
    response = client.get('/api/health')
    
    # Check that X-XSS-Protection is NOT present (deprecated)
    if 'X-XSS-Protection' not in response.headers:
        print(f'  ✓ X-XSS-Protection header correctly removed')
        test_results.append(('endpoint.deprecated_headers', True, None))
    else:
        print(f'  ⚠ X-XSS-Protection header still present: {response.headers.get("X-XSS-Protection")}')
        test_results.append(('endpoint.deprecated_headers', False, 'Header still present'))
except Exception as e:
    print(f'  ✗ Test failed: {e}')
    test_results.append(('endpoint.deprecated_headers', False, str(e)))

print()

print('=' * 70)
print('ENDPOINT TEST SUMMARY')
print('=' * 70)
print()

passed = sum(1 for _, result, _ in test_results if result)
failed = sum(1 for _, result, _ in test_results if not result)

print(f'Total Tests: {len(test_results)}')
print(f'Passed: {passed}')
print(f'Failed: {failed}')

if failed > 0:
    print(f'\nFailed Tests:')
    for name, result, error in test_results:
        if not result:
            print(f'  ✗ {name}: {error}')

print()
if failed == 0:
    print('🎉 All endpoint tests passed! Hardened code is working correctly.')
else:
    print(f'⚠️  {failed} endpoint test(s) failed. Check above for details.')

# Cleanup
db_instance = Database()
db = db_instance.get_connection()
db.execute('DELETE FROM sessions')
db.commit()

"""
Phase 4 Week 11: Admin Management API Endpoints Tests
Comprehensive test suite for admin user management REST API

Tests:
- Public endpoints (login, token validation)
- Protected endpoints (profile, password change, logout)
- Admin CRUD (super_admin only)
- Role-based access control
- Audit log endpoints
- Error scenarios and edge cases
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Test client setup
@pytest.fixture
def client():
    """Create Flask test client"""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_admin_service():
    """Mock AdminUserService"""
    with patch('admin.admin_management.get_admin_user_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


# ============================================================================
# PUBLIC ENDPOINT TESTS
# ============================================================================

class TestPublicEndpoints:
    """Test public endpoints (no authentication required)"""
    
    def test_health_check(self, client):
        """Health check endpoint should always work"""
        response = client.get('/api/admin-management/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['service'] == 'admin-management-api'
        assert 'timestamp' in data
    
    def test_login_success(self, client, mock_admin_service):
        """Test successful admin login"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice Moderator',
            'email': 'alice@example.com'
        }
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['username'] == 'alice_mod'
        assert data['role'] == 'moderator'
        assert 'token' in data
        assert 'expires_at' in data
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_invalid_credentials(self, client, mock_admin_service):
        """Test login with invalid credentials"""
        mock_admin_service.authenticate.return_value = (False, 'Invalid credentials', None)
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'WrongPassword123'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid username or password' in data['error']
    
    def test_login_no_request_body(self, client):
        """Test login with no request body"""
        response = client.post('/api/admin-management/login', json=None)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_validate_token_success(self, client):
        """Test token validation with valid token"""
        # First login to get token
        with patch('admin.admin_management.get_admin_user_service') as mock:
            service = MagicMock()
            mock.return_value = service
            service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
            service.get_admin.return_value = {
                'admin_id': 'admin-uuid-1',
                'username': 'alice_mod',
                'role': 'moderator',
                'display_name': 'Alice'
            }
            
            login_response = client.post('/api/admin-management/login', json={
                'username': 'alice_mod',
                'password': 'SecurePass123!'
            })
            
            token = json.loads(login_response.data)['token']
        
        # Now validate the token
        response = client.post('/api/admin-management/validate-token', json={
            'token': token
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['valid'] is True
        assert data['username'] == 'alice_mod'
    
    def test_validate_token_invalid(self, client):
        """Test token validation with invalid token"""
        response = client.post('/api/admin-management/validate-token', json={
            'token': 'invalid-token-xyz'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['valid'] is False


# ============================================================================
# PROTECTED SELF-SERVICE ENDPOINTS
# ============================================================================

class TestProtectedSelfServiceEndpoints:
    """Test protected endpoints for self-service operations"""
    
    @pytest.fixture
    def admin_token(self, client, mock_admin_service):
        """Get admin token for testing"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice'
        }
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'SecurePass123!'
        })
        
        return json.loads(response.data)['token']
    
    def test_get_profile_success(self, client, mock_admin_service, admin_token):
        """Test getting own profile"""
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice Moderator',
            'email': 'alice@example.com',
            'is_active': True,
            'permissions': ['moderate_content', 'manage_moderation'],
            'last_login': datetime.utcnow().isoformat()
        }
        
        response = client.get(
            '/api/admin-management/profile',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['admin']['username'] == 'alice_mod'
        assert data['admin']['role'] == 'moderator'
    
    def test_get_profile_no_token(self, client):
        """Test getting profile without token"""
        response = client.get('/api/admin-management/profile')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Admin authentication required'
    
    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token"""
        response = client.get(
            '/api/admin-management/profile',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid or expired token' in data['error']
    
    def test_change_password_success(self, client, mock_admin_service, admin_token):
        """Test changing password successfully"""
        mock_admin_service.change_password.return_value = (True, 'Password changed successfully')
        
        response = client.post(
            '/api/admin-management/change-password',
            json={
                'old_password': 'SecurePass123!',
                'new_password': 'NewSecurePass456!'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['success'] is True
    
    def test_change_password_weak_password(self, client, mock_admin_service, admin_token):
        """Test changing password with weak password"""
        mock_admin_service.change_password.return_value = (False, 'Password must be at least 8 characters')
        
        response = client.post(
            '/api/admin-management/change-password',
            json={
                'old_password': 'SecurePass123!',
                'new_password': 'weak'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_change_password_wrong_old_password(self, client, mock_admin_service, admin_token):
        """Test changing password with wrong old password"""
        mock_admin_service.change_password.return_value = (False, 'Old password is incorrect')
        
        response = client.post(
            '/api/admin-management/change-password',
            json={
                'old_password': 'WrongOldPassword',
                'new_password': 'NewSecurePass456!'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_logout_success(self, client, admin_token):
        """Test logout successfully invalidates token"""
        response = client.post(
            '/api/admin-management/logout',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['success'] is True
        
        # Token should be invalid now
        response = client.post('/api/admin-management/validate-token', json={'token': admin_token})
        assert response.status_code == 401


# ============================================================================
# ADMIN MANAGEMENT ENDPOINTS (super_admin only)
# ============================================================================

class TestAdminManagementEndpoints:
    """Test admin management endpoints (super_admin only)"""
    
    @pytest.fixture
    def super_admin_token(self, client, mock_admin_service):
        """Get super_admin token for testing"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-0')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-0',
            'username': 'super_admin',
            'role': 'super_admin',
            'display_name': 'Super Admin'
        }
        
        response = client.post('/api/admin-management/login', json={
            'username': 'super_admin',
            'password': 'SuperAdmin123!'
        })
        
        return json.loads(response.data)['token']
    
    @pytest.fixture
    def moderator_token(self, client, mock_admin_service):
        """Get moderator token for testing"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice'
        }
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'SecurePass123!'
        })
        
        return json.loads(response.data)['token']
    
    def test_create_admin_success(self, client, mock_admin_service, super_admin_token):
        """Test creating new admin"""
        mock_admin_service.create_admin.return_value = (True, 'Admin created successfully', 'admin-uuid-2')
        
        response = client.post(
            '/api/admin-management/admin/create',
            json={
                'username': 'bob_approver',
                'password': 'BobPass123!',
                'role': 'approver',
                'display_name': 'Bob Approver',
                'email': 'bob@example.com'
            },
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['success'] is True
        assert data['username'] == 'bob_approver'
        assert data['role'] == 'approver'
    
    def test_create_admin_duplicate_username(self, client, mock_admin_service, super_admin_token):
        """Test creating admin with duplicate username"""
        mock_admin_service.create_admin.return_value = (False, 'Username already exists', None)
        
        response = client.post(
            '/api/admin-management/admin/create',
            json={
                'username': 'alice_mod',
                'password': 'NewPass123!',
                'role': 'approver'
            },
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_admin_moderator_denied(self, client, moderator_token):
        """Test that moderator cannot create admin"""
        response = client.post(
            '/api/admin-management/admin/create',
            json={
                'username': 'new_admin',
                'password': 'Pass123!',
                'role': 'approver'
            },
            headers={'Authorization': f'Bearer {moderator_token}'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Insufficient permissions'
    
    def test_list_admins_success(self, client, mock_admin_service, super_admin_token):
        """Test listing all admins"""
        mock_admin_service.get_all_admins.return_value = [
            {
                'admin_id': 'admin-uuid-0',
                'username': 'super_admin',
                'role': 'super_admin',
                'display_name': 'Super Admin'
            },
            {
                'admin_id': 'admin-uuid-1',
                'username': 'alice_mod',
                'role': 'moderator',
                'display_name': 'Alice'
            }
        ]
        
        response = client.get(
            '/api/admin-management/admin/list',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert len(data['admins']) == 2
        assert data['count'] == 2
    
    def test_list_admins_with_limit(self, client, mock_admin_service, super_admin_token):
        """Test listing admins with limit parameter"""
        mock_admin_service.get_all_admins.return_value = []
        
        response = client.get(
            '/api/admin-management/admin/list?limit=50',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 200
        mock_admin_service.get_all_admins.assert_called_with(limit=50)
    
    def test_get_admin_details_success(self, client, mock_admin_service, super_admin_token):
        """Test getting admin details"""
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice',
            'email': 'alice@example.com',
            'is_active': True
        }
        
        response = client.get(
            '/api/admin-management/admin/admin-uuid-1',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['admin']['username'] == 'alice_mod'
    
    def test_get_admin_details_not_found(self, client, mock_admin_service, super_admin_token):
        """Test getting non-existent admin"""
        mock_admin_service.get_admin.return_value = None
        
        response = client.get(
            '/api/admin-management/admin/invalid-uuid',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Admin not found'
    
    def test_update_admin_role_success(self, client, mock_admin_service, super_admin_token):
        """Test updating admin role"""
        mock_admin_service.update_role.return_value = (True, 'Role updated successfully')
        
        response = client.post(
            '/api/admin-management/admin/admin-uuid-1/role',
            json={'role': 'viewer'},
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_deactivate_admin_success(self, client, mock_admin_service, super_admin_token):
        """Test deactivating admin"""
        mock_admin_service.deactivate_admin.return_value = (True, 'Admin deactivated successfully')
        
        response = client.post(
            '/api/admin-management/admin/admin-uuid-1/deactivate',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_deactivate_self_denied(self, client, mock_admin_service, super_admin_token):
        """Test that admin cannot deactivate themselves"""
        response = client.post(
            '/api/admin-management/admin/admin-uuid-0/deactivate',
            headers={'Authorization': f'Bearer {super_admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Cannot deactivate your own account' in data['error']


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

class TestAuditLogEndpoints:
    """Test audit log endpoints"""
    
    @pytest.fixture
    def moderator_with_audit_token(self, client, mock_admin_service):
        """Get moderator token with audit permission"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice'
        }
        mock_admin_service.check_permission.return_value = True
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'SecurePass123!'
        })
        
        return json.loads(response.data)['token']
    
    def test_get_audit_log_success(self, client, mock_admin_service, moderator_with_audit_token):
        """Test getting audit log"""
        mock_admin_service.get_audit_log.return_value = [
            {
                'log_id': 'log1',
                'admin_id': 'admin-uuid-0',
                'action': 'admin_created',
                'resource_type': 'admin',
                'resource_id': 'admin-uuid-1',
                'success': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        response = client.get(
            '/api/admin-management/audit-log',
            headers={'Authorization': f'Bearer {moderator_with_audit_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert len(data['audit_log']) == 1
        assert data['count'] == 1
    
    def test_get_audit_log_with_filter(self, client, mock_admin_service, moderator_with_audit_token):
        """Test getting audit log with admin_id filter"""
        mock_admin_service.get_audit_log.return_value = []
        
        response = client.get(
            '/api/admin-management/audit-log?limit=50&admin_id=admin-uuid-1',
            headers={'Authorization': f'Bearer {moderator_with_audit_token}'}
        )
        
        assert response.status_code == 200
        mock_admin_service.get_audit_log.assert_called_with(limit=50, admin_id='admin-uuid-1')
    
    def test_get_audit_log_permission_denied(self, client, mock_admin_service):
        """Test getting audit log without permission"""
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-1')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-1',
            'username': 'alice_mod',
            'role': 'moderator',
            'display_name': 'Alice'
        }
        mock_admin_service.check_permission.return_value = False
        
        response = client.post('/api/admin-management/login', json={
            'username': 'alice_mod',
            'password': 'SecurePass123!'
        })
        
        token = json.loads(response.data)['token']
        
        response = client.get(
            '/api/admin-management/audit-log',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

class TestRateLimiting:
    """Test rate limiting on endpoints"""
    
    def test_login_rate_limit(self, client, mock_admin_service):
        """Test login rate limiting (10/minute)"""
        mock_admin_service.authenticate.return_value = (False, 'Invalid credentials', None)
        
        # Make 10 failed login attempts (should succeed)
        for i in range(10):
            response = client.post('/api/admin-management/login', json={
                'username': 'admin',
                'password': 'wrong'
            })
            assert response.status_code == 401
        
        # 11th attempt should be rate limited
        response = client.post('/api/admin-management/login', json={
            'username': 'admin',
            'password': 'wrong'
        })
        assert response.status_code == 429


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_admin_full_lifecycle(self, client, mock_admin_service):
        """Test complete admin lifecycle: login -> operations -> logout"""
        # Setup
        mock_admin_service.authenticate.return_value = (True, 'Login successful', 'admin-uuid-0')
        mock_admin_service.get_admin.return_value = {
            'admin_id': 'admin-uuid-0',
            'username': 'super_admin',
            'role': 'super_admin',
            'display_name': 'Super Admin'
        }
        mock_admin_service.create_admin.return_value = (True, 'Admin created', 'admin-uuid-1')
        mock_admin_service.get_all_admins.return_value = [
            {'admin_id': 'admin-uuid-0', 'username': 'super_admin', 'role': 'super_admin'},
            {'admin_id': 'admin-uuid-1', 'username': 'new_admin', 'role': 'moderator'}
        ]
        
        # Login
        response = client.post('/api/admin-management/login', json={
            'username': 'super_admin',
            'password': 'SuperAdmin123!'
        })
        assert response.status_code == 200
        token = json.loads(response.data)['token']
        
        # Create new admin
        response = client.post(
            '/api/admin-management/admin/create',
            json={
                'username': 'new_admin',
                'password': 'NewPass123!',
                'role': 'moderator'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 201
        
        # List admins
        response = client.get(
            '/api/admin-management/admin/list',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['admins']) == 2
        
        # Logout
        response = client.post(
            '/api/admin-management/logout',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

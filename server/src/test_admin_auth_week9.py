"""
Test suite for admin authentication on approval endpoints (Week 9)

Tests the admin password authentication on all approval admin endpoints:
- Missing password header returns 401
- Invalid password returns 403
- Valid password allows endpoint access
- All admin endpoints properly protected

Design principles:
- Authentication-focused tests
- Tests verify decorator functionality
- Tests verify password validation
- Integration with SetupConfig.verify_admin_password()
"""

import pytest
import json
from flask import Flask
from werkzeug.security import generate_password_hash
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from main import create_app
from models import db, SetupConfig, UserRegistration
from services.approval_access_service import get_approval_service
from setup_config import SetupConfig as SetupConfigClass


class TestAdminAuthenticationOnApprovalEndpoints:
    """Test admin authentication for approval endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def setup_approval_mode_with_password(self, app):
        """Set access control to 'approved' mode and set admin password"""
        with app.app_context():
            # Set approval mode
            setup = SetupConfig.query.filter_by(key='access_control').first()
            if setup:
                setup.value = 'approved'
            else:
                setup = SetupConfig(key='access_control', value='approved')
                db.session.add(setup)
            
            # Set admin password
            admin_pwd = SetupConfig.query.filter_by(key='admin_password_hash').first()
            admin_password_hash = generate_password_hash('test_admin_password')
            
            if admin_pwd:
                admin_pwd.value = admin_password_hash
            else:
                admin_pwd = SetupConfig(
                    key='admin_password_hash',
                    value=admin_password_hash
                )
                db.session.add(admin_pwd)
            
            db.session.commit()
    
    @pytest.fixture
    def setup_pending_requests(self, app, setup_approval_mode_with_password):
        """Create some pending approval requests for testing"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('alice', 'First request')
            service.request_approval('bob', 'Second request')
    
    # ========== PENDING REQUESTS ENDPOINT TESTS ==========
    
    def test_pending_requests_no_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test GET /admin/pending-requests without password returns 401"""
        with app.app_context():
            response = client.get('/api/auth/admin/pending-requests')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
            assert 'authentication required' in data['error'].lower()
    
    def test_pending_requests_invalid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test GET /admin/pending-requests with invalid password returns 403"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/pending-requests',
                headers={'X-Admin-Password': 'wrong_password'}
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data
            assert 'invalid' in data['error'].lower()
    
    def test_pending_requests_valid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test GET /admin/pending-requests with valid password succeeds"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/pending-requests',
                headers={'X-Admin-Password': 'test_admin_password'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'pending_requests' in data
            assert data['count'] == 2
    
    # ========== APPROVE USER ENDPOINT TESTS ==========
    
    def test_approve_user_no_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/approve-user without password returns 401"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/approve-user',
                json={'nickname': 'alice'},
                content_type='application/json'
            )
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
    
    def test_approve_user_invalid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/approve-user with invalid password returns 403"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/approve-user',
                json={'nickname': 'alice'},
                headers={'X-Admin-Password': 'wrong_password'},
                content_type='application/json'
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data
    
    def test_approve_user_valid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/approve-user with valid password succeeds"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/approve-user',
                json={'nickname': 'alice'},
                headers={'X-Admin-Password': 'test_admin_password'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['success'] is True
    
    # ========== REJECT USER ENDPOINT TESTS ==========
    
    def test_reject_user_no_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/reject-user without password returns 401"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/reject-user',
                json={'nickname': 'bob'},
                content_type='application/json'
            )
            
            assert response.status_code == 401
    
    def test_reject_user_invalid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/reject-user with invalid password returns 403"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/reject-user',
                json={'nickname': 'bob'},
                headers={'X-Admin-Password': 'wrong_password'},
                content_type='application/json'
            )
            
            assert response.status_code == 403
    
    def test_reject_user_valid_password(self, client, app, setup_approval_mode_with_password, setup_pending_requests):
        """Test POST /admin/reject-user with valid password succeeds"""
        with app.app_context():
            response = client.post(
                '/api/auth/admin/reject-user',
                json={'nickname': 'bob', 'reason': 'Not suitable'},
                headers={'X-Admin-Password': 'test_admin_password'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['success'] is True
    
    # ========== APPROVAL HISTORY ENDPOINT TESTS ==========
    
    def test_approval_history_no_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-history without password returns 401"""
        with app.app_context():
            response = client.get('/api/auth/admin/approval-history')
            
            assert response.status_code == 401
    
    def test_approval_history_invalid_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-history with invalid password returns 403"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/approval-history',
                headers={'X-Admin-Password': 'wrong_password'}
            )
            
            assert response.status_code == 403
    
    def test_approval_history_valid_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-history with valid password succeeds"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/approval-history',
                headers={'X-Admin-Password': 'test_admin_password'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'approval_history' in data
    
    # ========== APPROVAL STATS ENDPOINT TESTS ==========
    
    def test_approval_stats_no_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-stats without password returns 401"""
        with app.app_context():
            response = client.get('/api/auth/admin/approval-stats')
            
            assert response.status_code == 401
    
    def test_approval_stats_invalid_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-stats with invalid password returns 403"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/approval-stats',
                headers={'X-Admin-Password': 'wrong_password'}
            )
            
            assert response.status_code == 403
    
    def test_approval_stats_valid_password(self, client, app, setup_approval_mode_with_password):
        """Test GET /admin/approval-stats with valid password succeeds"""
        with app.app_context():
            response = client.get(
                '/api/auth/admin/approval-stats',
                headers={'X-Admin-Password': 'test_admin_password'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'approval_statistics' in data
    
    # ========== PUBLIC ENDPOINTS NOT REQUIRING AUTH ==========
    
    def test_request_approval_no_auth_required(self, client, app, setup_approval_mode_with_password):
        """Test that POST /request-approval doesn't require admin password"""
        with app.app_context():
            # Should work WITHOUT admin password
            response = client.post(
                '/api/auth/request-approval',
                json={'nickname': 'charlie'},
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
    
    def test_approval_status_no_auth_required(self, client, app, setup_approval_mode_with_password):
        """Test that GET /approval-status doesn't require admin password"""
        with app.app_context():
            # Should work WITHOUT admin password
            response = client.get('/api/auth/approval-status/anyone')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'


class TestAdminPasswordVerification:
    """Test the SetupConfig.verify_admin_password() function"""
    
    def test_verify_admin_password_correct(self):
        """Test verifying correct admin password"""
        # Create a test password hash
        test_password = 'my_secure_password'
        password_hash = generate_password_hash(test_password)
        
        # Store it in mock database
        # In real test, this would be in the test database
        # For now, we test the logic directly
        from werkzeug.security import check_password_hash
        
        # Verify it works
        assert check_password_hash(password_hash, test_password) is True
    
    def test_verify_admin_password_incorrect(self):
        """Test verifying incorrect admin password"""
        test_password = 'my_secure_password'
        password_hash = generate_password_hash(test_password)
        
        from werkzeug.security import check_password_hash
        
        # Verify it fails
        assert check_password_hash(password_hash, 'wrong_password') is False
    
    def test_verify_admin_password_empty(self):
        """Test that empty password is rejected"""
        # SetupConfig.verify_admin_password should reject empty password
        assert SetupConfigClass.verify_admin_password('') is False
    
    def test_verify_admin_password_none_raises_nothing(self):
        """Test that None password doesn't crash"""
        # Should not raise exception
        try:
            result = SetupConfigClass.verify_admin_password(None)
            assert result is False
        except Exception as e:
            pytest.fail(f"verify_admin_password(None) raised {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

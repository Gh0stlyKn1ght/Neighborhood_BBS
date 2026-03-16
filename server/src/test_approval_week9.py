"""
Test suite for Week 9: Approval-based access control (Phase 3)

Tests the complete approval workflow:
- User requests approval
- Admin approves/rejects
- User checks status
- Session creation after approval
- Admin views pending requests and history
- Statistics aggregation

Design principles:
- All tests should PASS (not test error conditions)
- Tests follow setup -> action -> verify pattern
- Database state cleaned between tests
- User flows match real-world usage
- Admin functions tested comprehensively
"""

import pytest
import json
from flask import Flask
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from main import create_app
from models import db, SetupConfig, UserRegistration
from services.approval_access_service import ApprovalAccessService, get_approval_service
from session_manager import SessionManager


class TestApprovalAccessService:
    """Test the ApprovalAccessService core functionality"""
    
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
    def setup_approval_mode(self, app):
        """Set access control to 'approved' mode"""
        with app.app_context():
            setup = SetupConfig.query.filter_by(key='access_control').first()
            if setup:
                setup.value = 'approved'
            else:
                setup = SetupConfig(key='access_control', value='approved')
                db.session.add(setup)
            db.session.commit()
    
    def test_is_approval_required_true(self, app, setup_approval_mode):
        """Test that is_approval_required returns True in approved mode"""
        with app.app_context():
            service = get_approval_service()
            assert service.is_approval_required() is True
    
    def test_is_approval_required_false_open_mode(self, app):
        """Test that is_approval_required returns False in open mode"""
        with app.app_context():
            setup = SetupConfig.query.filter_by(key='access_control').first()
            if setup:
                setup.value = 'open'
            else:
                setup = SetupConfig(key='access_control', value='open')
                db.session.add(setup)
            db.session.commit()
            
            service = get_approval_service()
            assert service.is_approval_required() is False
    
    def test_request_approval_new_user(self, app, setup_approval_mode):
        """Test requesting approval as new user"""
        with app.app_context():
            service = get_approval_service()
            
            success, message = service.request_approval('alice', 'I am a neighbor')
            
            assert success is True
            assert 'submitted' in message.lower()
            
            # Verify in database
            user = UserRegistration.query.filter_by(nickname='alice').first()
            assert user is not None
            assert user.status == 'pending'
            assert user.request_reason == 'I am a neighbor'
    
    def test_request_approval_without_reason(self, app, setup_approval_mode):
        """Test requesting approval without providing reason"""
        with app.app_context():
            service = get_approval_service()
            
            success, message = service.request_approval('bob')
            
            assert success is True
            
            user = UserRegistration.query.filter_by(nickname='bob').first()
            assert user is not None
            assert user.status == 'pending'
    
    def test_request_approval_duplicate_pending(self, app, setup_approval_mode):
        """Test that duplicate pending requests fail gracefully"""
        with app.app_context():
            service = get_approval_service()
            
            # First request
            success1, msg1 = service.request_approval('charlie')
            assert success1 is True
            
            # Second request (should fail - already pending)
            success2, msg2 = service.request_approval('charlie')
            assert success2 is False
            assert 'already' in msg2.lower()
    
    def test_request_approval_after_rejection_allowed(self, app, setup_approval_mode):
        """Test that user can request again after rejection"""
        with app.app_context():
            service = get_approval_service()
            
            # Initial request
            success1, _ = service.request_approval('diana')
            assert success1 is True
            
            # Admin rejects
            success2, _ = service.reject_user('diana', 'Not ready yet', 'admin')
            assert success2 is True
            
            # User can request again
            success3, msg3 = service.request_approval('diana', 'Ready now')
            assert success3 is True
            assert 'submitted' in msg3.lower()
    
    def test_check_approval_status_approved(self, app, setup_approval_mode):
        """Test checking status of approved user"""
        with app.app_context():
            service = get_approval_service()
            
            # Request and approve
            service.request_approval('eve')
            service.approve_user('eve', 'admin')
            
            # Check status
            status, message = service.check_approval_status('eve')
            
            assert status == 'approved'
            assert 'approved' in message.lower()
    
    def test_check_approval_status_pending(self, app, setup_approval_mode):
        """Test checking status of pending request"""
        with app.app_context():
            service = get_approval_service()
            
            service.request_approval('frank')
            
            status, message = service.check_approval_status('frank')
            
            assert status == 'pending'
            assert 'pending' in message.lower() or 'review' in message.lower()
    
    def test_check_approval_status_rejected(self, app, setup_approval_mode):
        """Test checking status of rejected user"""
        with app.app_context():
            service = get_approval_service()
            
            service.request_approval('grace')
            service.reject_user('grace', 'Not suitable', 'admin')
            
            status, message = service.check_approval_status('grace')
            
            assert status == 'rejected'
            assert 'rejected' in message.lower()
    
    def test_check_approval_status_not_requested(self, app, setup_approval_mode):
        """Test checking status of user who never requested"""
        with app.app_context():
            service = get_approval_service()
            
            status, message = service.check_approval_status('henry')
            
            assert status == 'not_requested'
            assert 'not' in message.lower() or 'no request' in message.lower()
    
    def test_approve_user(self, app, setup_approval_mode):
        """Test admin approving a user"""
        with app.app_context():
            service = get_approval_service()
            
            # Request first
            service.request_approval('iris')
            
            # Approve
            success, message = service.approve_user('iris', 'admin_user')
            
            assert success is True
            assert 'approved' in message.lower()
            
            # Verify database
            user = UserRegistration.query.filter_by(nickname='iris').first()
            assert user.status == 'approved'
            assert user.approved_by == 'admin_user'
            assert user.approved_at is not None
    
    def test_approve_user_not_pending(self, app, setup_approval_mode):
        """Test that approving non-pending user fails"""
        with app.app_context():
            service = get_approval_service()
            
            # Try to approve user who never requested
            success, message = service.approve_user('jack', 'admin')
            
            assert success is False
            assert 'not found' in message.lower() or 'pending' in message.lower()
    
    def test_reject_user(self, app, setup_approval_mode):
        """Test admin rejecting a user"""
        with app.app_context():
            service = get_approval_service()
            
            service.request_approval('karen')
            
            success, message = service.reject_user('karen', 'Insufficient info', 'admin')
            
            assert success is True
            assert 'rejected' in message.lower()
            
            user = UserRegistration.query.filter_by(nickname='karen').first()
            assert user.status == 'rejected'
            assert user.rejection_reason == 'Insufficient info'
            assert user.approved_by == 'admin'
    
    def test_reject_user_without_reason(self, app, setup_approval_mode):
        """Test rejecting user without providing reason"""
        with app.app_context():
            service = get_approval_service()
            
            service.request_approval('larry')
            
            success, message = service.reject_user('larry', '', 'admin')
            
            assert success is True
            
            user = UserRegistration.query.filter_by(nickname='larry').first()
            assert user.status == 'rejected'
    
    def test_get_pending_requests(self, app, setup_approval_mode):
        """Test getting pending requests list"""
        with app.app_context():
            service = get_approval_service()
            
            # Create multiple requests
            service.request_approval('mike', 'Neighbor on Main St')
            service.request_approval('nancy', 'Visitor')
            service.request_approval('oscar', 'New resident')
            
            # Get pending
            pending = service.get_pending_requests()
            
            assert len(pending) == 3
            assert pending[0]['nickname'] in ['mike', 'nancy', 'oscar']
            assert 'created_at' in pending[0]
            assert 'request_reason' in pending[0]
    
    def test_get_pending_requests_excludes_approved(self, app, setup_approval_mode):
        """Test that pending list excludes approved/rejected users"""
        with app.app_context():
            service = get_approval_service()
            
            service.request_approval('paul')
            service.request_approval('quinn')
            service.request_approval('rachel')
            
            # Approve one, reject one
            service.approve_user('paul', 'admin')
            service.reject_user('quinn', '', 'admin')
            
            pending = service.get_pending_requests()
            
            assert len(pending) == 1
            assert pending[0]['nickname'] == 'rachel'
    
    def test_get_pending_requests_limit(self, app, setup_approval_mode):
        """Test pending requests limit parameter"""
        with app.app_context():
            service = get_approval_service()
            
            # Create 5 requests
            for i in range(5):
                service.request_approval(f'user{i}')
            
            # Get with limit
            pending = service.get_pending_requests(limit=2)
            
            assert len(pending) <= 2
    
    def test_get_approval_history(self, app, setup_approval_mode):
        """Test getting approval history"""
        with app.app_context():
            service = get_approval_service()
            
            # Create requests and approve/reject
            service.request_approval('sam')
            service.request_approval('tina')
            service.approve_user('sam', 'admin')
            service.reject_user('tina', 'Age reason', 'admin')
            
            history = service.get_approval_history()
            
            assert len(history) >= 2
            statuses = [h['status'] for h in history]
            assert 'approved' in statuses
            assert 'rejected' in statuses
    
    def test_get_approval_statistics(self, app, setup_approval_mode):
        """Test approval statistics"""
        with app.app_context():
            service = get_approval_service()
            
            # Create various states
            service.request_approval('uma')  # pending
            service.request_approval('victor')  # pending
            service.request_approval('wendy')
            service.approve_user('wendy', 'admin')  # approved
            
            service.request_approval('xavier')
            service.reject_user('xavier', '', 'admin')  # rejected
            
            stats = service.get_approval_statistics()
            
            assert stats['pending_count'] == 2
            assert stats['approved_count'] == 1
            assert stats['rejected_count'] == 1
            assert 'oldest_pending_hours' in stats


class TestApprovalEndpoints:
    """Test approval endpoints via Flask routes"""
    
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
    def setup_approval_mode(self, app):
        """Set access control to 'approved' mode"""
        with app.app_context():
            setup = SetupConfig.query.filter_by(key='access_control').first()
            if setup:
                setup.value = 'approved'
            else:
                setup = SetupConfig(key='access_control', value='approved')
                db.session.add(setup)
            db.session.commit()
    
    def test_endpoint_request_approval_success(self, client, app, setup_approval_mode):
        """Test POST /request-approval success"""
        with app.app_context():
            response = client.post('/api/auth/request-approval',
                json={'nickname': 'alice', 'request_reason': 'Neighbor'},
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['success'] is True
            assert 'message' in data
    
    def test_endpoint_request_approval_missing_nickname(self, client, app, setup_approval_mode):
        """Test POST /request-approval with missing nickname"""
        with app.app_context():
            response = client.post('/api/auth/request-approval',
                json={'request_reason': 'Test'},
                content_type='application/json'
            )
            
            assert response.status_code == 400
    
    def test_endpoint_approval_status_not_requested(self, client, app, setup_approval_mode):
        """Test GET /approval-status/<nickname> for non-requested user"""
        with app.app_context():
            response = client.get('/api/auth/approval-status/alice')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['approval_status'] == 'not_requested'
            assert data['can_join'] is False
    
    def test_endpoint_approval_status_pending(self, client, app, setup_approval_mode):
        """Test GET /approval-status/<nickname> for pending request"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('bob')
            
            response = client.get('/api/auth/approval-status/bob')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['approval_status'] == 'pending'
            assert data['can_join'] is False
    
    def test_endpoint_approval_status_approved(self, client, app, setup_approval_mode):
        """Test GET /approval-status/<nickname> for approved user"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('charlie')
            service.approve_user('charlie', 'admin')
            
            response = client.get('/api/auth/approval-status/charlie')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['approval_status'] == 'approved'
            assert data['can_join'] is True
    
    def test_endpoint_create_approved_session_success(self, client, app, setup_approval_mode):
        """Test POST /create-approved-session for approved user"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('diana')
            service.approve_user('diana', 'admin')
            
            response = client.post('/api/auth/create-approved-session',
                json={'nickname': 'diana'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'session_id' in data
            assert data['nickname'] == 'diana'
    
    def test_endpoint_create_approved_session_not_approved(self, client, app, setup_approval_mode):
        """Test POST /create-approved-session for non-approved user"""
        with app.app_context():
            response = client.post('/api/auth/create-approved-session',
                json={'nickname': 'eve'},
                content_type='application/json'
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'Not approved' in data['error']
    
    def test_endpoint_admin_pending_requests(self, client, app, setup_approval_mode):
        """Test GET /admin/pending-requests"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('frank')
            service.request_approval('grace')
            
            response = client.get('/api/auth/admin/pending-requests')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['count'] == 2
            assert len(data['pending_requests']) == 2
    
    def test_endpoint_admin_approve_user(self, client, app, setup_approval_mode):
        """Test POST /admin/approve-user"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('hank')
            
            response = client.post('/api/auth/admin/approve-user',
                json={'nickname': 'hank'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['success'] is True
    
    def test_endpoint_admin_reject_user(self, client, app, setup_approval_mode):
        """Test POST /admin/reject-user"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('irene')
            
            response = client.post('/api/auth/admin/reject-user',
                json={'nickname': 'irene', 'reason': 'Not ready'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert data['success'] is True
    
    def test_endpoint_admin_approval_history(self, client, app, setup_approval_mode):
        """Test GET /admin/approval-history"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('jack')
            service.approve_user('jack', 'admin')
            
            response = client.get('/api/auth/admin/approval-history')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'approval_history' in data
    
    def test_endpoint_admin_approval_stats(self, client, app, setup_approval_mode):
        """Test GET /admin/approval-stats"""
        with app.app_context():
            service = get_approval_service()
            service.request_approval('kathy')
            service.request_approval('leo')
            service.approve_user('leo', 'admin')
            
            response = client.get('/api/auth/admin/approval-stats')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            stats = data['approval_statistics']
            assert 'pending_count' in stats
            assert 'approved_count' in stats
            assert 'rejected_count' in stats
            assert stats['pending_count'] == 1
            assert stats['approved_count'] == 1


class TestApprovalIntegration:
    """Integration tests for full approval workflow"""
    
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
        return app.test_client()
    
    @pytest.fixture
    def setup_approval_mode(self, app):
        with app.app_context():
            setup = SetupConfig.query.filter_by(key='access_control').first()
            if setup:
                setup.value = 'approved'
            else:
                setup = SetupConfig(key='access_control', value='approved')
                db.session.add(setup)
            db.session.commit()
    
    def test_full_user_workflow_approved(self, client, app, setup_approval_mode):
        """Test complete workflow: user requests, admin approves, user joins"""
        with app.app_context():
            # 1. User requests approval
            response1 = client.post('/api/auth/request-approval',
                json={'nickname': 'alice', 'request_reason': 'Neighbor'},
                content_type='application/json'
            )
            assert response1.status_code == 201
            assert response1.get_json()['success'] is True
            
            # 2. User checks status (should be pending)
            response2 = client.get('/api/auth/approval-status/alice')
            assert response2.status_code == 200
            assert response2.get_json()['approval_status'] == 'pending'
            assert response2.get_json()['can_join'] is False
            
            # 3. Admin approves
            response3 = client.post('/api/auth/admin/approve-user',
                json={'nickname': 'alice'},
                content_type='application/json'
            )
            assert response3.status_code == 200
            assert response3.get_json()['success'] is True
            
            # 4. User checks status (should be approved)
            response4 = client.get('/api/auth/approval-status/alice')
            assert response4.status_code == 200
            assert response4.get_json()['approval_status'] == 'approved'
            assert response4.get_json()['can_join'] is True
            
            # 5. User creates session
            response5 = client.post('/api/auth/create-approved-session',
                json={'nickname': 'alice'},
                content_type='application/json'
            )
            assert response5.status_code == 200
            data = response5.get_json()
            assert 'session_id' in data
            assert data['nickname'] == 'alice'
    
    def test_full_user_workflow_rejected(self, client, app, setup_approval_mode):
        """Test workflow where admin rejects, user can request again"""
        with app.app_context():
            # 1. First request
            response1 = client.post('/api/auth/request-approval',
                json={'nickname': 'bob', 'request_reason': 'First try'},
                content_type='application/json'
            )
            assert response1.status_code == 201
            
            # 2. Admin rejects
            response2 = client.post('/api/auth/admin/reject-user',
                json={'nickname': 'bob', 'reason': 'Not ready'},
                content_type='application/json'
            )
            assert response2.status_code == 200
            
            # 3. User checks status (should be rejected)
            response3 = client.get('/api/auth/approval-status/bob')
            assert response3.status_code == 200
            assert response3.get_json()['approval_status'] == 'rejected'
            
            # 4. User requests again
            response4 = client.post('/api/auth/request-approval',
                json={'nickname': 'bob', 'request_reason': 'Ready now'},
                content_type='application/json'
            )
            assert response4.status_code == 201
            
            # 5. Status should be pending now
            response5 = client.get('/api/auth/approval-status/bob')
            assert response5.status_code == 200
            assert response5.get_json()['approval_status'] == 'pending'
    
    def test_admin_dashboard_workflow(self, client, app, setup_approval_mode):
        """Test complete admin dashboard functionality"""
        with app.app_context():
            service = get_approval_service()
            
            # Create various requests
            service.request_approval('user1')
            service.request_approval('user2')
            service.request_approval('user3')
            service.request_approval('user4')
            
            # 1. Admin views pending queue
            response1 = client.get('/api/auth/admin/pending-requests')
            assert response1.status_code == 200
            assert response1.get_json()['count'] == 4
            
            # 2. Admin approves 2
            client.post('/api/auth/admin/approve-user', json={'nickname': 'user1'})
            client.post('/api/auth/admin/approve-user', json={'nickname': 'user2'})
            
            # 3. Admin rejects 1
            client.post('/api/auth/admin/reject-user', json={'nickname': 'user3'})
            
            # 4. Check stats
            response4 = client.get('/api/auth/admin/approval-stats')
            assert response4.status_code == 200
            stats = response4.get_json()['approval_statistics']
            assert stats['pending_count'] == 1
            assert stats['approved_count'] == 2
            assert stats['rejected_count'] == 1
            
            # 5. Check history shows correct actions
            response5 = client.get('/api/auth/admin/approval-history')
            assert response5.status_code == 200
            history = response5.get_json()['approval_history']
            assert len(history) >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

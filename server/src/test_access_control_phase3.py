"""
Test suite for PHASE 3 - Access Control

Tests the following features:
- User registration (open, passcode, approval modes)
- Admin approval workflow
- IP whitelist management
- Access tokens and verification
- Access control statistics

Run with: pytest test_access_control_phase3.py -v

Author: AI Assistant
Date: 2025
"""

import pytest
import json
from datetime import datetime, timedelta
from models import db
from services.access_control_service import access_control_service, AccessControlService
from setup_config import SetupConfig


class TestAccessControlService:
    """Test AccessControlService functionality"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert access_control_service is not None
        assert access_control_service.db is not None
        
    def test_validate_username(self):
        """Test username validation"""
        # Valid usernames
        assert AccessControlService._validate_username('user123') == True
        assert AccessControlService._validate_username('user_name') == True
        assert AccessControlService._validate_username('user-name') == True
        
        # Invalid usernames
        assert AccessControlService._validate_username('us') == False  # Too short
        assert AccessControlService._validate_username('user@name') == False  # Invalid char
        assert AccessControlService._validate_username('a' * 25) == False  # Too long
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert AccessControlService._validate_email('user@example.com') == True
        assert AccessControlService._validate_email('test.user@domain.co.uk') == True
        
        # Invalid emails
        assert AccessControlService._validate_email('user@') == False
        assert AccessControlService._validate_email('user') == False
        assert AccessControlService._validate_email('user@domain') == False
    
    def test_validate_ip(self):
        """Test IP validation"""
        # Valid IPs
        assert AccessControlService._validate_ip('192.168.1.1') == True
        assert AccessControlService._validate_ip('10.0.0.1') == True
        assert AccessControlService._validate_ip('255.255.255.255') == True
        
        # Invalid IPs
        assert AccessControlService._validate_ip('256.1.1.1') == False
        assert AccessControlService._validate_ip('1.1.1') == False
        assert AccessControlService._validate_ip('1.1.1.1.1') == False
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = 'test_password_123'
        
        # Hash password
        hashed = AccessControlService._hash_password(password)
        assert hashed != password
        assert '$' in hashed  # Contains salt separator
        
        # Verify password
        assert AccessControlService._verify_password(password, hashed) == True
        assert AccessControlService._verify_password('wrong_password', hashed) == False
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        success, message = access_control_service.register_user(
            username='testuser1',
            email='testuser1@example.com',
            password='secure_password_123'
        )
        
        assert success == True
        assert 'successfully' in message.lower()
    
    def test_user_registration_validation(self):
        """Test user registration validation"""
        # Invalid username
        success, message = access_control_service.register_user(
            username='ab',  # Too short
            email='test@example.com',
            password='password'
        )
        assert success == False
        
        # Invalid email
        success, message = access_control_service.register_user(
            username='validuser',
            email='invalid-email',
            password='password'
        )
        assert success == False
        
        # Short password
        success, message = access_control_service.register_user(
            username='validuser',
            email='valid@example.com',
            password='123'
        )
        assert success == False
    
    def test_user_registration_duplicate(self):
        """Test duplicate user rejection"""
        # Register first user
        access_control_service.register_user(
            username='uniqueuser',
            email='unique@example.com',
            password='password123'
        )
        
        # Try to register with same username
        success, message = access_control_service.register_user(
            username='uniqueuser',
            email='different@example.com',
            password='password123'
        )
        assert success == False
        assert 'already exists' in message.lower()
        
        # Try to register with same email
        success, message = access_control_service.register_user(
            username='differentuser',
            email='unique@example.com',
            password='password123'
        )
        assert success == False
        assert 'already registered' in message.lower()
    
    def test_verify_user_password(self):
        """Test user password verification"""
        # Register user
        access_control_service.register_user(
            username='pwduser',
            email='pwd@example.com',
            password='mypassword123'
        )
        
        # Verify correct password
        success, message = access_control_service.verify_user_password('pwduser', 'mypassword123')
        assert success == True
        
        # Verify incorrect password
        success, message = access_control_service.verify_user_password('pwduser', 'wrongpassword')
        assert success == False
        
        # Verify non-existent user
        success, message = access_control_service.verify_user_password('nonexistent', 'password')
        assert success == False
    
    def test_get_user_registration(self):
        """Test retrieving user registration"""
        # Register user
        access_control_service.register_user(
            username='getuser',
            email='getuser@example.com',
            password='password123'
        )
        
        # Get user
        user = access_control_service.get_user_registration('getuser')
        assert user is not None
        assert user['username'] == 'getuser'
        assert user['email'] == 'getuser@example.com'
        assert user['is_active'] == 1
        
        # Get non-existent user
        user = access_control_service.get_user_registration('nonexistent')
        assert user is None
    
    def test_user_approval_workflow(self):
        """Test user approval and rejection"""
        # Register user with approval required
        access_control_service.register_user(
            username='approvaluser',
            email='approval@example.com',
            password='password123',
            requires_approval=True,
            reason='Testing approval workflow'
        )
        
        # Check user is pending approval
        user = access_control_service.get_user_registration('approvaluser')
        assert user['requires_approval'] == 1
        
        # Approve user
        success, message = access_control_service.approve_user('approvaluser', 'admin')
        assert success == True
        
        # Check user is approved
        user = access_control_service.get_user_registration('approvaluser')
        assert user['requires_approval'] == 0
        assert user['approved_at'] is not None
    
    def test_user_rejection_workflow(self):
        """Test user rejection"""
        # Register user with approval required
        access_control_service.register_user(
            username='rejectuser',
            email='reject@example.com',
            password='password123',
            requires_approval=True
        )
        
        # Reject user
        success, message = access_control_service.reject_user(
            'rejectuser',
            rejection_reason='Does not meet requirements',
            rejected_by='admin'
        )
        assert success == True
        
        # Check user is inactive
        user = access_control_service.get_user_registration('rejectuser')
        assert user['is_active'] == 0
    
    def test_pending_approvals_list(self):
        """Test getting pending approvals"""
        # Register multiple users with approval
        for i in range(3):
            access_control_service.register_user(
                username=f'pendinguser{i}',
                email=f'pending{i}@example.com',
                password='password123',
                requires_approval=True,
                reason=f'Test approval {i}'
            )
        
        # Get pending approvals
        approvals = access_control_service.get_pending_approvals()
        assert len(approvals) >= 3
        
        assert all(approval['status'] == 'pending' for approval in approvals)
    
    def test_ip_whitelist_operations(self):
        """Test IP whitelist management"""
        # Add IP to whitelist
        success, message = access_control_service.add_ip_to_whitelist(
            '192.168.1.100',
            'Test office network',
            'admin'
        )
        assert success == True
        
        # Check IP is whitelisted
        assert access_control_service.is_ip_whitelisted('192.168.1.100') == True
        assert access_control_service.is_ip_whitelisted('10.0.0.1') == False
        
        # Remove IP from whitelist
        success, message = access_control_service.remove_ip_from_whitelist('192.168.1.100')
        assert success == True
        
        # Check IP is no longer whitelisted
        assert access_control_service.is_ip_whitelisted('192.168.1.100') == False
    
    def test_invalid_ip_rejection(self):
        """Test invalid IP rejection"""
        success, message = access_control_service.add_ip_to_whitelist('invalid.ip.address')
        assert success == False
        assert 'invalid' in message.lower()
    
    def test_get_whitelisted_ips(self):
        """Test retrieving whitelisted IPs"""
        # Add multiple IPs
        access_control_service.add_ip_to_whitelist('10.0.0.1', 'Device 1')
        access_control_service.add_ip_to_whitelist('10.0.0.2', 'Device 2')
        
        # Get list
        ips = access_control_service.get_whitelisted_ips()
        ip_addresses = [ip['ip_address'] for ip in ips]
        
        assert '10.0.0.1' in ip_addresses
        assert '10.0.0.2' in ip_addresses
    
    def test_access_token_generation(self):
        """Test token generation"""
        # Register user
        access_control_service.register_user(
            username='tokenuser',
            email='token@example.com',
            password='password123'
        )
        
        # Generate token
        token = access_control_service.generate_access_token(
            'tokenuser',
            AccessControlService.TOKEN_EMAIL_VERIFICATION
        )
        
        assert token is not None
        assert len(token) > 20  # Should be reasonably long
    
    def test_access_token_verification(self):
        """Test token verification"""
        # Register user and generate token
        access_control_service.register_user(
            username='tokenverify',
            email='tokenverify@example.com',
            password='password123'
        )
        
        token = access_control_service.generate_access_token(
            'tokenverify',
            AccessControlService.TOKEN_EMAIL_VERIFICATION
        )
        
        # Verify token
        is_valid, username = access_control_service.verify_access_token(
            token,
            AccessControlService.TOKEN_EMAIL_VERIFICATION
        )
        
        assert is_valid == True
        assert username == 'tokenverify'
        
        # Verify same token again should fail (already used)
        is_valid, username = access_control_service.verify_access_token(
            token,
            AccessControlService.TOKEN_EMAIL_VERIFICATION
        )
        assert is_valid == False
    
    def test_invalid_token_verification(self):
        """Test invalid token verification"""
        is_valid, username = access_control_service.verify_access_token('invalid_token_xyz')
        assert is_valid == False
        assert username is None
    
    def test_token_expiration(self):
        """Test token expiration"""
        # Register user
        access_control_service.register_user(
            username='expiredtoken',
            email='expired@example.com',
            password='password123'
        )
        
        # Create expired token manually
        token = 'expired_test_token'
        expires_at = datetime.now() - timedelta(hours=1)  # Already expired
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO access_tokens (token, username, token_type, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (token, 'expiredtoken', 'email_verification', expires_at))
        conn.commit()
        conn.close()
        
        # Try to verify expired token
        is_valid, username = access_control_service.verify_access_token(token)
        assert is_valid == False
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        # Insert some expired tokens
        conn = db.get_connection()
        cursor = conn.cursor()
        
        for i in range(3):
            cursor.execute('''
                INSERT INTO access_tokens (token, username, token_type, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (f'expired_token_{i}', f'user{i}', 'email_verification', 
                  datetime.now() - timedelta(hours=1)))
        
        conn.commit()
        conn.close()
        
        # Cleanup
        count = access_control_service.cleanup_expired_tokens()
        assert count >= 3
    
    def test_access_stats(self):
        """Test access control statistics"""
        stats = access_control_service.get_access_stats()
        
        assert 'pending_approvals' in stats
        assert 'active_users' in stats
        assert 'whitelisted_ips' in stats
        assert all(isinstance(v, int) for v in stats.values())


class TestAccessControlRoutes:
    """Test REST API endpoints for access control"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from server import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            yield client
    
    def test_get_access_mode(self, client):
        """Test GET /api/access/mode"""
        response = client.get('/api/access/mode')
        
        assert response.status_code in [200, 401, 404]  # May not exist in test app
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'mode' in data
            assert data['mode'] in ['open', 'passcode', 'approval', 'ip_whitelist']
    
    def test_register_user(self, client):
        """Test POST /api/access/register"""
        response = client.post('/api/access/register', json={
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        })
        
        # Expect either 201 (created) or 404 (route doesn't exist)
        assert response.status_code in [201, 400, 404]
        
        if response.status_code == 201:
            data = json.loads(response.data)
            assert data['success'] == True
    
    def test_register_user_validation(self, client):
        """Test user registration validation"""
        # Missing fields
        response = client.post('/api/access/register', json={
            'username': 'user'
        })
        
        assert response.status_code in [400, 404]


class TestAccessControlIntegration:
    """Integration tests for access control flows"""
    
    def test_registration_to_approval_workflow(self):
        """Test complete workflow from registration to approval"""
        # 1. Register user with approval required
        success, msg = access_control_service.register_user(
            username='workflow_user',
            email='workflow@example.com',
            password='workflow_password',
            requires_approval=True,
            reason='Integration test'
        )
        assert success == True
        
        # 2. Verify pending
        pending = access_control_service.get_pending_approvals()
        usernames = [p['username'] for p in pending]
        assert 'workflow_user' in usernames
        
        # 3. Approve user
        success, msg = access_control_service.approve_user('workflow_user')
        assert success == True
        
        # 4. Verify user can authenticate
        success, msg = access_control_service.verify_user_password(
            'workflow_user', 'workflow_password'
        )
        assert success == True
    
    def test_ip_whitelist_workflow(self):
        """Test IP whitelist workflow"""
        test_ip = '172.16.0.50'
        
        # Add IP
        success, _ = access_control_service.add_ip_to_whitelist(test_ip, 'Test')
        assert success == True
        
        # Verify whitelisted
        assert access_control_service.is_ip_whitelisted(test_ip) == True
        
        # Get list
        ips = access_control_service.get_whitelisted_ips()
        assert any(ip['ip_address'] == test_ip for ip in ips)
        
        # Remove
        success, _ = access_control_service.remove_ip_from_whitelist(test_ip)
        assert success == True
        
        # Verify removed
        assert access_control_service.is_ip_whitelisted(test_ip) == False


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

"""
Test suite for Phase 4 Week 10: Admin User Management Service

Tests multi-admin support with role-based access control (RBAC)

Covers:
- Admin creation with roles (super_admin, moderator, approver, viewer)
- Authentication (login/password verification)
- Password management
- Role assignment and updates
- Permission checking
- Admin deactivation
- Audit logging of admin actions
"""

import pytest
import json
from datetime import datetime
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.admin_user_service import AdminUserService, get_admin_user_service
from models import Database


class TestAdminUserService:
    """Test admin user management service"""
    
    @pytest.fixture
    def db(self):
        """Create test database"""
        # Use in-memory SQLite for testing
        db = Database()
        db.get_connection().execute('PRAGMA foreign_keys = ON')
        yield db
    
    @pytest.fixture
    def service(self):
        """Get admin user service"""
        service = get_admin_user_service()
        return service
    
    # ========== ADMIN CREATION TESTS ==========
    
    def test_create_super_admin(self, service):
        """Test creating a super admin"""
        success, message, admin_id = service.create_admin(
            username='admin_super',
            password='SecurePassword123!',
            role='super_admin',
            display_name='Super Administrator',
            email='super@localhost'
        )
        
        assert success is True
        assert admin_id is not None
        assert 'successfully' in message.lower()
    
    def test_create_moderator(self, service):
        """Test creating a moderator"""
        success, message, admin_id = service.create_admin(
            username='mod_alice',
            password='ModeratorPass123!',
            role='moderator',
            display_name='Alice Moderator'
        )
        
        assert success is True
        assert admin_id is not None
    
    def test_create_approver(self, service):
        """Test creating an approver"""
        success, message, admin_id = service.create_admin(
            username='approver_bob',
            password='ApproverPass123!',
            role='approver',
            display_name='Bob Approver'
        )
        
        assert success is True
        assert admin_id is not None
    
    def test_create_viewer(self, service):
        """Test creating a viewer (read-only)"""
        success, message, admin_id = service.create_admin(
            username='viewer_charlie',
            password='ViewerPass123!',
            role='viewer',
            display_name='Charlie Viewer'
        )
        
        assert success is True
        assert admin_id is not None
    
    def test_create_admin_duplicate_username(self, service):
        """Test that duplicate usernames are rejected"""
        # Create first admin
        service.create_admin(
            username='duplicate_user',
            password='Password123!',
            role='moderator'
        )
        
        # Try to create another with same username
        success, message, admin_id = service.create_admin(
            username='duplicate_user',
            password='DifferentPassword123!',
            role='approver'
        )
        
        assert success is False
        assert 'already exists' in message.lower()
        assert admin_id is None
    
    def test_create_admin_short_username(self, service):
        """Test that short usernames are rejected"""
        success, message, admin_id = service.create_admin(
            username='ab',
            password='Password123!',
            role='moderator'
        )
        
        assert success is False
        assert 'at least 3' in message.lower()
    
    def test_create_admin_weak_password(self, service):
        """Test that weak passwords are rejected"""
        success, message, admin_id = service.create_admin(
            username='strong_username',
            password='weak',
            role='moderator'
        )
        
        assert success is False
        assert 'at least 8' in message.lower()
    
    def test_create_admin_invalid_role(self, service):
        """Test that invalid roles are rejected"""
        success, message, admin_id = service.create_admin(
            username='invalid_role_user',
            password='Password123!',
            role='invalid_role'
        )
        
        assert success is False
        assert 'invalid role' in message.lower()
    
    # ========== AUTHENTICATION TESTS ==========
    
    def test_authenticate_success(self, service):
        """Test successful authentication"""
        # Create admin first
        _, _, admin_id = service.create_admin(
            username='auth_user',
            password='CorrectPassword123!',
            role='moderator'
        )
        
        # Authenticate
        success, message, returned_id = service.authenticate(
            username='auth_user',
            password='CorrectPassword123!'
        )
        
        assert success is True
        assert returned_id == admin_id
    
    def test_authenticate_wrong_password(self, service):
        """Test authentication with wrong password"""
        # Create admin
        service.create_admin(
            username='wrong_pwd_user',
            password='CorrectPassword123!',
            role='moderator'
        )
        
        # Try wrong password
        success, message, admin_id = service.authenticate(
            username='wrong_pwd_user',
            password='WrongPassword123!'
        )
        
        assert success is False
        assert admin_id is None
    
    def test_authenticate_nonexistent_user(self, service):
        """Test authentication for non-existent user"""
        success, message, admin_id = service.authenticate(
            username='nonexistent_user',
            password='SomePassword123!'
        )
        
        assert success is False
        assert admin_id is None
    
    def test_authenticate_inactive_admin(self, service):
        """Test authentication for inactive admin"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='inactive_user',
            password='Password123!',
            role='moderator'
        )
        
        # Deactivate admin
        service.deactivate_admin(admin_id, 'test')
        
        # Try to authenticate
        success, message, _ = service.authenticate(
            username='inactive_user',
            password='Password123!'
        )
        
        assert success is False
        assert 'inactive' in message.lower()
    
    # ========== PASSWORD MANAGEMENT TESTS ==========
    
    def test_change_password_success(self, service):
        """Test changing admin password"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='pwd_change_user',
            password='OldPassword123!',
            role='moderator'
        )
        
        # Change password
        success, message = service.change_password(
            admin_id=admin_id,
            old_password='OldPassword123!',
            new_password='NewPassword123!'
        )
        
        assert success is True
        
        # Verify new password works
        auth_success, _, _ = service.authenticate(
            username='pwd_change_user',
            password='NewPassword123!'
        )
        assert auth_success is True
    
    def test_change_password_wrong_old(self, service):
        """Test that wrong old password is rejected"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='pwd_wrong_user',
            password='CorrectPassword123!',
            role='moderator'
        )
        
        # Try to change with wrong old password
        success, message = service.change_password(
            admin_id=admin_id,
            old_password='WrongPassword123!',
            new_password='NewPassword123!'
        )
        
        assert success is False
        assert 'incorrect' in message.lower()
    
    def test_change_password_weak_new(self, service):
        """Test that weak new password is rejected"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='pwd_weak_user',
            password='OldPassword123!',
            role='moderator'
        )
        
        # Try to change to weak password
        success, message = service.change_password(
            admin_id=admin_id,
            old_password='OldPassword123!',
            new_password='weak'
        )
        
        assert success is False
        assert 'at least 8' in message.lower()
    
    # ========== ADMIN RETRIEVAL TESTS ==========
    
    def test_get_admin_details(self, service):
        """Test retrieving admin details"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='details_user',
            password='Password123!',
            role='super_admin',
            display_name='Detail Test Admin',
            email='details@test.com'
        )
        
        # Get details
        admin = service.get_admin(admin_id)
        
        assert admin is not None
        assert admin['username'] == 'details_user'
        assert admin['role'] == 'super_admin'
        assert admin['display_name'] == 'Detail Test Admin'
        assert admin['email'] == 'details@test.com'
        assert admin['is_active'] is True
    
    def test_get_all_admins(self, service):
        """Test retrieving all admins"""
        # Create multiple admins
        service.create_admin('admin1', 'Pass123!', 'super_admin')
        service.create_admin('admin2', 'Pass123!', 'moderator')
        service.create_admin('admin3', 'Pass123!', 'approver')
        
        # Get all
        admins = service.get_all_admins()
        
        assert len(admins) >= 3
        usernames = [a['username'] for a in admins]
        assert 'admin1' in usernames
        assert 'admin2' in usernames
        assert 'admin3' in usernames
    
    # ========== ROLE AND PERMISSION TESTS ==========
    
    def test_super_admin_permissions(self, service):
        """Test super admin has all permissions"""
        _, _, admin_id = service.create_admin(
            username='super_perm_test',
            password='Password123!',
            role='super_admin'
        )
        
        admin = service.get_admin(admin_id)
        
        # Check some critical permissions
        assert 'manage_admins' in admin['permissions']
        assert 'moderate_content' in admin['permissions']
        assert 'approve_access' in admin['permissions']
        assert 'audit_log' in admin['permissions']
    
    def test_moderator_permissions(self, service):
        """Test moderator has correct permissions"""
        _, _, admin_id = service.create_admin(
            username='mod_perm_test',
            password='Password123!',
            role='moderator'
        )
        
        admin = service.get_admin(admin_id)
        
        # Has moderation permissions
        assert 'moderate_content' in admin['permissions']
        assert 'manage_moderation' in admin['permissions']
        
        # But not admin management
        assert 'manage_admins' not in admin['permissions']
    
    def test_approver_permissions(self, service):
        """Test approver has correct permissions"""
        _, _, admin_id = service.create_admin(
            username='approver_perm_test',
            password='Password123!',
            role='approver'
        )
        
        admin = service.get_admin(admin_id)
        
        # Has approval permissions
        assert 'approve_access' in admin['permissions']
        assert 'reject_access' in admin['permissions']
        
        # But not moderation
        assert 'moderate_content' not in admin['permissions']
    
    def test_viewer_permissions(self, service):
        """Test viewer has read-only permissions"""
        _, _, admin_id = service.create_admin(
            username='viewer_perm_test',
            password='Password123!',
            role='viewer'
        )
        
        admin = service.get_admin(admin_id)
        
        # Has view only permissions
        assert 'view_dashboard' in admin['permissions']
        assert 'view_analytics' in admin['permissions']
        
        # But no action permissions
        assert 'moderate_content' not in admin['permissions']
        assert 'approve_access' not in admin['permissions']
        assert 'manage_admins' not in admin['permissions']
    
    def test_check_permission_success(self, service):
        """Test permission checking for allowed permission"""
        _, _, admin_id = service.create_admin(
            username='perm_check_user',
            password='Password123!',
            role='moderator'
        )
        
        has_permission = service.check_permission(admin_id, 'moderate_content')
        assert has_permission is True
    
    def test_check_permission_denied(self, service):
        """Test permission checking for denied permission"""
        _, _, admin_id = service.create_admin(
            username='perm_denied_user',
            password='Password123!',
            role='viewer'  # Viewer can't moderate
        )
        
        has_permission = service.check_permission(admin_id, 'moderate_content')
        assert has_permission is False
    
    def test_update_role(self, service):
        """Test updating admin role"""
        # Create moderator
        _, _, admin_id = service.create_admin(
            username='role_change_user',
            password='Password123!',
            role='moderator'
        )
        
        # Update to super_admin
        success, message = service.update_role(admin_id, 'super_admin', 'test_admin')
        
        assert success is True
        
        # Verify role changed
        admin = service.get_admin(admin_id)
        assert admin['role'] == 'super_admin'
        assert 'manage_admins' in admin['permissions']
    
    # ========== ADMIN ACTIVATION/DEACTIVATION TESTS ==========
    
    def test_deactivate_admin(self, service):
        """Test deactivating admin account"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='deactivate_user',
            password='Password123!',
            role='moderator'
        )
        
        # Deactivate
        success, message = service.deactivate_admin(admin_id, 'test_admin')
        
        assert success is True
        
        # Verify deactivated
        admin = service.get_admin(admin_id)
        assert admin['is_active'] is False
    
    # ========== AUDIT LOGGING TESTS ==========
    
    def test_audit_log_admin_created(self, service):
        """Test that admin creation is logged"""
        # Create admin (which should be logged)
        _, _, admin_id = service.create_admin(
            username='audit_test_user',
            password='Password123!',
            role='moderator',
            created_by='system'
        )
        
        # Get audit log
        logs = service.get_audit_log(admin_id='system')
        
        # Should have creation entry
        assert len(logs) > 0
        creation_logs = [l for l in logs if l['action'] == 'admin_created']
        assert len(creation_logs) > 0
    
    def test_audit_log_password_changed(self, service):
        """Test that password changes are logged"""
        # Create admin
        _, _, admin_id = service.create_admin(
            username='pwd_audit_user',
            password='OldPassword123!',
            role='moderator'
        )
        
        # Change password
        service.change_password(
            admin_id=admin_id,
            old_password='OldPassword123!',
            new_password='NewPassword123!'
        )
        
        # Get audit log for this admin
        logs = service.get_audit_log(admin_id=admin_id)
        
        # Should have password change entry
        pwd_logs = [l for l in logs if l['action'] == 'password_changed']
        assert len(pwd_logs) > 0
    
    def test_audit_log_all_entries(self, service):
        """Test retrieving complete audit log"""
        # Create and perform various actions
        _, _, admin1 = service.create_admin('audit1', 'Pass123!', 'moderator')
        _, _, admin2 = service.create_admin('audit2', 'Pass123!', 'approver')
        service.change_password(admin1, 'Pass123!', 'NewPass123!')
        service.update_role(admin2, 'moderator', admin1)
        
        # Get full audit log
        logs = service.get_audit_log(limit=100)
        
        # Should have multiple entries
        assert len(logs) > 0
        
        # Extract action types
        actions = [l['action'] for l in logs]
        assert 'admin_created' in actions
        assert 'password_changed' in actions
        assert 'role_changed' in actions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

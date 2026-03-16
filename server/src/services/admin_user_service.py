"""
Phase 4 Week 10: Admin User Management Service
Multi-admin support with role-based access control (RBAC)

Supports three admin roles:
- super_admin: Full access to all system functions
- moderator: Can moderate content, manage violations, view analytics
- approver: Can approve/reject user access requests
- viewer: Read-only access to system status and analytics

Features:
- Create/read/update/delete admin users
- Assign roles and permissions
- Track admin activity in audit log
- Password management with bcrypt
- Session/token tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import hashlib
import secrets
from threading import Lock

from models import Database
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


class AdminUserService:
    """Manage admin users with roles and permissions"""
    
    # Admin roles and their permissions
    ROLES = {
        'super_admin': {
            'description': 'Full system access',
            'permissions': [
                'view_dashboard', 'manage_admins', 'manage_users',
                'moderate_content', 'manage_moderation', 'approve_access',
                'ban_devices', 'reset_passcode', 'view_analytics', 'audit_log'
            ]
        },
        'moderator': {
            'description': 'Content moderation and user management',
            'permissions': [
                'view_dashboard', 'moderate_content', 'manage_moderation',
                'view_violations', 'ban_devices', 'view_analytics'
            ]
        },
        'approver': {
            'description': 'User approval and access control',
            'permissions': [
                'view_dashboard', 'approve_access', 'reject_access',
                'view_pending', 'view_approval_history'
            ]
        },
        'viewer': {
            'description': 'Read-only system access',
            'permissions': [
                'view_dashboard', 'view_analytics', 'view_violations', 'view_approval_history'
            ]
        }
    }
    
    def __init__(self):
        self._lock = Lock()
        self._init_tables()
    
    def _init_tables(self):
        """Create admin_users and admin_audit_log tables if not exist"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Admin users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    admin_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    display_name TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    created_by TEXT,
                    CHECK(role IN ('super_admin', 'moderator', 'approver', 'viewer'))
                )
            ''')
            
            # Admin audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_audit_log (
                    log_id TEXT PRIMARY KEY,
                    admin_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY(admin_id) REFERENCES admin_users(admin_id)
                )
            ''')
            
            # Admin sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    session_id TEXT PRIMARY KEY,
                    admin_id TEXT NOT NULL,
                    token_hash TEXT,
                    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY(admin_id) REFERENCES admin_users(admin_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Admin user management tables initialized")
        
        except Exception as e:
            logger.error(f"Error initializing admin tables: {e}")
    
    def create_admin(
        self,
        username: str,
        password: str,
        role: str,
        display_name: str = '',
        email: str = '',
        created_by: str = 'system'
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new admin user.
        
        Args:
            username: Admin username (must be unique)
            password: Plain text password (will be hashed)
            role: One of (super_admin, moderator, approver, viewer)
            display_name: Full name for display
            email: Admin email address
            created_by: Username of admin creating this user
        
        Returns:
            (success, message, admin_id)
        """
        try:
            # Validate role
            if role not in self.ROLES:
                return False, f"Invalid role: {role}", None
            
            # Validate username
            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters", None
            
            if len(username) > 50:
                return False, "Username must be less than 50 characters", None
            
            # Validate password
            if not password or len(password) < 8:
                return False, "Password must be at least 8 characters", None
            
            # Generate admin_id
            admin_id = f"admin_{secrets.token_hex(8)}"
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check username doesn't exist
            cursor.execute(
                'SELECT admin_id FROM admin_users WHERE username = ?',
                (username,)
            )
            if cursor.fetchone():
                conn.close()
                return False, f"Username already exists: {username}", None
            
            # Insert new admin
            cursor.execute('''
                INSERT INTO admin_users (
                    admin_id, username, password_hash, role,
                    display_name, email, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (admin_id, username, password_hash, role, display_name, email, created_by))
            
            conn.commit()
            conn.close()
            
            # Log action
            self._log_action(created_by, 'admin_created', 'admin_user', admin_id, f"Created {role}: {username}")
            
            logger.info(f"Admin created: {username} ({role})")
            return True, f"Admin {username} created successfully", admin_id
        
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            return False, f"Error creating admin: {str(e)}", None
    
    def get_admin(self, admin_id: str) -> Optional[Dict]:
        """Get admin user details"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT admin_id, username, role, display_name, email,
                       is_active, created_at, last_login
                FROM admin_users WHERE admin_id = ?
            ''', (admin_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                'admin_id': row[0],
                'username': row[1],
                'role': row[2],
                'display_name': row[3],
                'email': row[4],
                'is_active': row[5],
                'created_at': row[6],
                'last_login': row[7],
                'permissions': self.ROLES[row[2]]['permissions']
            }
        
        except Exception as e:
            logger.error(f"Error getting admin: {e}")
            return None
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Authenticate admin with username and password.
        
        Returns:
            (success, message, admin_id)
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT admin_id, password_hash, is_active FROM admin_users
                WHERE username = ?
            ''', (username,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.warning(f"Authentication failed: user not found: {username}")
                return False, "Invalid username or password", None
            
            admin_id, password_hash, is_active = row
            
            if not is_active:
                logger.warning(f"Authentication failed: user inactive: {username}")
                return False, "Admin account is inactive", None
            
            # Verify password
            if not check_password_hash(password_hash, password):
                logger.warning(f"Authentication failed: invalid password: {username}")
                return False, "Invalid username or password", None
            
            # Update last login
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE admin_users SET last_login = ? WHERE admin_id = ?',
                (datetime.utcnow(), admin_id)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Admin authenticated: {username}")
            return True, "Authentication successful", admin_id
        
        except Exception as e:
            logger.error(f"Error authenticating admin: {e}")
            return False, "Authentication error", None
    
    def change_password(self, admin_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change admin password"""
        try:
            # Verify old password
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT password_hash FROM admin_users WHERE admin_id = ?',
                (admin_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "Admin not found"
            
            if not check_password_hash(row[0], old_password):
                conn.close()
                return False, "Old password is incorrect"
            
            # Validate new password
            if not new_password or len(new_password) < 8:
                conn.close()
                return False, "New password must be at least 8 characters"
            
            # Update password
            new_hash = generate_password_hash(new_password)
            cursor.execute(
                'UPDATE admin_users SET password_hash = ? WHERE admin_id = ?',
                (new_hash, admin_id)
            )
            conn.commit()
            conn.close()
            
            self._log_action(admin_id, 'password_changed', 'admin_user', admin_id)
            logger.info(f"Admin password changed: {admin_id}")
            return True, "Password changed successfully"
        
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False, f"Error: {str(e)}"
    
    def update_role(self, admin_id: str, new_role: str, updated_by: str) -> Tuple[bool, str]:
        """Update admin role (super_admin only)"""
        try:
            if new_role not in self.ROLES:
                return False, f"Invalid role: {new_role}"
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE admin_users SET role = ? WHERE admin_id = ?',
                (new_role, admin_id)
            )
            conn.commit()
            conn.close()
            
            self._log_action(updated_by, 'role_changed', 'admin_user', admin_id, f"New role: {new_role}")
            logger.info(f"Admin role updated: {admin_id} -> {new_role}")
            return True, "Role updated successfully"
        
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return False, f"Error: {str(e)}"
    
    def deactivate_admin(self, admin_id: str, deactivated_by: str) -> Tuple[bool, str]:
        """Deactivate admin account"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE admin_users SET is_active = FALSE WHERE admin_id = ?',
                (admin_id,)
            )
            conn.commit()
            conn.close()
            
            self._log_action(deactivated_by, 'admin_deactivated', 'admin_user', admin_id)
            logger.info(f"Admin deactivated: {admin_id}")
            return True, "Admin deactivated"
        
        except Exception as e:
            logger.error(f"Error deactivating admin: {e}")
            return False, f"Error: {str(e)}"
    
    def get_all_admins(self, limit: int = 100) -> List[Dict]:
        """Get all admin users"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT admin_id, username, role, display_name, is_active, last_login
                FROM admin_users ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            
            admins = []
            for row in cursor.fetchall():
                admins.append({
                    'admin_id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'display_name': row[3],
                    'is_active': row[4],
                    'last_login': row[5],
                    'permissions': self.ROLES[row[2]]['permissions']
                })
            
            conn.close()
            return admins
        
        except Exception as e:
            logger.error(f"Error getting admins: {e}")
            return []
    
    def check_permission(self, admin_id: str, permission: str) -> bool:
        """Check if admin has specific permission"""
        try:
            admin = self.get_admin(admin_id)
            if not admin:
                return False
            
            return permission in admin['permissions']
        
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def _log_action(
        self,
        admin_id: str,
        action: str,
        resource_type: str = '',
        resource_id: str = '',
        details: str = '',
        success: bool = True
    ):
        """Log admin action to audit trail"""
        try:
            log_id = f"log_{secrets.token_hex(8)}"
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO admin_audit_log (
                    log_id, admin_id, action, resource_type, resource_id,
                    details, success, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (log_id, admin_id, action, resource_type, resource_id, details, success, datetime.utcnow()))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error logging action: {e}")
    
    def get_audit_log(self, limit: int = 100, admin_id: str = None) -> List[Dict]:
        """Get admin audit log"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if admin_id:
                cursor.execute('''
                    SELECT log_id, admin_id, action, resource_type, resource_id,
                           details, success, timestamp
                    FROM admin_audit_log WHERE admin_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (admin_id, limit))
            else:
                cursor.execute('''
                    SELECT log_id, admin_id, action, resource_type, resource_id,
                           details, success, timestamp
                    FROM admin_audit_log
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'log_id': row[0],
                    'admin_id': row[1],
                    'action': row[2],
                    'resource_type': row[3],
                    'resource_id': row[4],
                    'details': row[5],
                    'success': row[6],
                    'timestamp': row[7]
                })
            
            conn.close()
            return logs
        
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            return []


# Singleton instance
_admin_user_service = None
_service_lock = Lock()


def get_admin_user_service() -> AdminUserService:
    """Get singleton AdminUserService instance"""
    global _admin_user_service
    
    if _admin_user_service is None:
        with _service_lock:
            if _admin_user_service is None:
                _admin_user_service = AdminUserService()
    
    return _admin_user_service

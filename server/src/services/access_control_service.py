"""
Access Control Service - PHASE 3

Handles user registration, approval workflows, and access control logic:
- Passcode-based entry (Week 8)
- Admin approval system (Week 9)
- IP whitelist management
- Email verification tokens
- User registration persistence

Author: AI Assistant
Date: 2025
"""

from datetime import datetime, timedelta
import hashlib
import secrets
import re
from typing import Dict, List, Tuple, Optional
import logging

from models import db

logger = logging.getLogger(__name__)


class AccessControlService:
    """
    Comprehensive access control management service for Neighborhood BBS.
    
    Supports multiple access modes:
    1. Open: No restrictions (default)
    2. Passcode: Shared passcode required for entry
    3. Approval: Admin approval workflow required
    4. IP Whitelist: Only whitelisted IPs allowed
    """
    
    # Access control modes
    MODE_OPEN = 'open'
    MODE_PASSCODE = 'passcode'
    MODE_APPROVAL = 'approval'
    MODE_IP_WHITELIST = 'ip_whitelist'
    
    # Token types
    TOKEN_EMAIL_VERIFICATION = 'email_verification'
    TOKEN_PASSWORD_RESET = 'password_reset'
    TOKEN_APPROVAL = 'approval'
    
    # Token validity periods
    TOKEN_VALIDITY_HOURS = 24
    
    # Regex patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,20}$'
    
    def __init__(self):
        """Initialize the access control service"""
        self.db = db
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load access control configuration from database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT setting_value FROM network_config 
                WHERE setting_name IN ('access_mode', 'passcode', 'ip_whitelist_enabled')
                ORDER BY setting_name
            ''')
            
            config = {}
            for row in cursor.fetchall():
                setting_name = row[0]
                setting_value = row[1]
                config[setting_name] = setting_value
            
            conn.close()
            return config
        except Exception as e:
            logger.warning(f"Failed to load access control config: {e}")
            return {}
    
    def get_access_mode(self) -> str:
        """Get current access control mode"""
        from server.src.setup.models import SetupConfig
        mode = SetupConfig.get('access_mode', self.MODE_OPEN)
        return mode
    
    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM ip_whitelist 
                WHERE ip_address = ? AND is_active = 1
            ''', (ip_address,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error checking IP whitelist: {e}")
            return False
    
    def add_ip_to_whitelist(self, ip_address: str, description: str = '', 
                           added_by: str = 'system') -> Tuple[bool, str]:
        """
        Add IP address to whitelist
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate IP format (basic validation)
            if not self._validate_ip(ip_address):
                return False, "Invalid IP address format"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ip_whitelist (ip_address, description, added_by)
                VALUES (?, ?, ?)
            ''', (ip_address, description, added_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"IP {ip_address} added to whitelist by {added_by}")
            return True, f"IP {ip_address} added to whitelist"
        except Exception as e:
            logger.error(f"Error adding IP to whitelist: {e}")
            return False, f"Error adding IP to whitelist: {str(e)}"
    
    def remove_ip_from_whitelist(self, ip_address: str) -> Tuple[bool, str]:
        """Remove IP address from whitelist"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE ip_whitelist SET is_active = 0
                WHERE ip_address = ?
            ''', (ip_address,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"IP {ip_address} removed from whitelist")
                conn.close()
                return True, f"IP {ip_address} removed from whitelist"
            else:
                conn.close()
                return False, f"IP {ip_address} not found in whitelist"
        except Exception as e:
            logger.error(f"Error removing IP from whitelist: {e}")
            return False, f"Error removing IP: {str(e)}"
    
    def get_whitelisted_ips(self, active_only: bool = True) -> List[Dict]:
        """Get all whitelisted IPs"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute('''
                    SELECT ip_address, description, added_by, added_at
                    FROM ip_whitelist
                    WHERE is_active = 1
                    ORDER BY added_at DESC
                ''')
            else:
                cursor.execute('''
                    SELECT ip_address, description, added_by, added_at, is_active
                    FROM ip_whitelist
                    ORDER BY added_at DESC
                ''')
            
            ips = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return ips
        except Exception as e:
            logger.error(f"Error retrieving whitelisted IPs: {e}")
            return []
    
    def register_user(self, username: str, email: str, password: str,
                     requires_approval: bool = False, 
                     ip_address: str = '', device_info: str = '',
                     reason: str = '') -> Tuple[bool, str]:
        """
        Register a new user
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate inputs
            if not self._validate_username(username):
                return False, "Invalid username format (3-20 characters, alphanumeric/underscore/dash)"
            
            if not self._validate_email(email):
                return False, "Invalid email format"
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            # Check for duplicate username/email
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM user_registrations WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"
            
            cursor.execute('SELECT id FROM user_registrations WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Email already registered"
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Insert user registration
            cursor.execute('''
                INSERT INTO user_registrations (username, email, password_hash, requires_approval)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, 1 if requires_approval else 0))
            
            conn.commit()
            
            # If approval required, create approval request
            if requires_approval:
                cursor.execute('''
                    INSERT INTO access_approvals (username, email, reason, ip_address, device_info, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                ''', (username, email, reason, ip_address, device_info))
                conn.commit()
            
            conn.close()
            
            logger.info(f"User {username} registered successfully")
            return True, f"User {username} registered successfully"
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, f"Error registering user: {str(e)}"
    
    def verify_user_password(self, username: str, password: str) -> Tuple[bool, str]:
        """Verify user credentials"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT password_hash, is_active FROM user_registrations 
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, "User not found"
            
            password_hash, is_active = result
            
            if not is_active:
                return False, "User account is inactive"
            
            if self._verify_password(password, password_hash):
                return True, "User authenticated"
            else:
                return False, "Incorrect password"
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False, "Error verifying password"
    
    def get_user_registration(self, username: str) -> Optional[Dict]:
        """Get user registration details"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, is_active, requires_approval, approved_by, 
                       approved_at, created_at, last_login
                FROM user_registrations 
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Error getting user registration: {e}")
            return None
    
    def approve_user(self, username: str, approved_by: str = 'admin') -> Tuple[bool, str]:
        """Approve a pending user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Update user registration
            cursor.execute('''
                UPDATE user_registrations 
                SET requires_approval = 0, approved_by = ?, approved_at = ?
                WHERE username = ? AND requires_approval = 1
            ''', (approved_by, datetime.now(), username))
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "User not found or already approved"
            
            # Update approval request
            cursor.execute('''
                UPDATE access_approvals
                SET status = 'approved', approved_by = ?, approved_at = ?
                WHERE username = ? AND status = 'pending'
            ''', (approved_by, datetime.now(), username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {username} approved by {approved_by}")
            return True, f"User {username} approved"
        except Exception as e:
            logger.error(f"Error approving user: {e}")
            return False, f"Error approving user: {str(e)}"
    
    def reject_user(self, username: str, rejection_reason: str = '', 
                   rejected_by: str = 'admin') -> Tuple[bool, str]:
        """Reject a pending user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Deactivate user registration
            cursor.execute('''
                UPDATE user_registrations 
                SET is_active = 0
                WHERE username = ? AND requires_approval = 1
            ''', (username,))
            
            # Update approval request
            cursor.execute('''
                UPDATE access_approvals
                SET status = 'rejected', approved_by = ?, approved_at = ?, rejection_reason = ?
                WHERE username = ? AND status = 'pending'
            ''', (rejected_by, datetime.now(), rejection_reason, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {username} rejected by {rejected_by}")
            return True, f"User {username} rejected"
        except Exception as e:
            logger.error(f"Error rejecting user: {e}")
            return False, f"Error rejecting user: {str(e)}"
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, reason, ip_address, device_info, requested_at, status
                FROM access_approvals
                WHERE status = 'pending'
                ORDER BY requested_at ASC
            ''')
            
            approvals = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return approvals
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return []
    
    def generate_access_token(self, username: str, token_type: str = TOKEN_EMAIL_VERIFICATION,
                             validity_hours: int = TOKEN_VALIDITY_HOURS) -> str:
        """Generate access token for verification"""
        try:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=validity_hours)
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_tokens (token, username, token_type, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (token, username, token_type, expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Access token generated for {username} ({token_type})")
            return token
        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            return ""
    
    def verify_access_token(self, token: str, token_type: str = TOKEN_EMAIL_VERIFICATION) -> Tuple[bool, Optional[str]]:
        """
        Verify access token
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, username)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, expires_at, used_at
                FROM access_tokens
                WHERE token = ? AND token_type = ?
            ''', (token, token_type))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, None
            
            username, expires_at, used_at = result
            
            # Check if already used
            if used_at:
                conn.close()
                return False, None
            
            # Check if expired
            if datetime.fromisoformat(expires_at) < datetime.now():
                conn.close()
                return False, None
            
            # Mark as used
            cursor.execute('''
                UPDATE access_tokens SET used_at = ?
                WHERE token = ?
            ''', (datetime.now(), token))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Access token verified for {username}")
            return True, username
        except Exception as e:
            logger.error(f"Error verifying access token: {e}")
            return False, None
    
    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM access_tokens WHERE expires_at < ?
            ''', (datetime.now(),))
            
            count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired access tokens")
            
            return count
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    def get_access_stats(self) -> Dict:
        """Get access control statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Pending approvals
            cursor.execute('SELECT COUNT(*) FROM access_approvals WHERE status = "pending"')
            stats['pending_approvals'] = cursor.fetchone()[0]
            
            # Active users
            cursor.execute('SELECT COUNT(*) FROM user_registrations WHERE is_active = 1')
            stats['active_users'] = cursor.fetchone()[0]
            
            # Whitelisted IPs
            cursor.execute('SELECT COUNT(*) FROM ip_whitelist WHERE is_active = 1')
            stats['whitelisted_ips'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting access stats: {e}")
            return {}
    
    # Helper methods
    @staticmethod
    def _validate_username(username: str) -> bool:
        """Validate username format"""
        return bool(re.match(AccessControlService.USERNAME_PATTERN, username))
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        return bool(re.match(AccessControlService.EMAIL_PATTERN, email))
    
    @staticmethod
    def _validate_ip(ip_address: str) -> bool:
        """Basic IP validation"""
        parts = ip_address.split('.')
        if len(parts) != 4:
            return False
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, pwd_hash = password_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False


# Service instance
access_control_service = AccessControlService()

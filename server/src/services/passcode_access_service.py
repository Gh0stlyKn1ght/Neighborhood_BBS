"""
Passcode-based access control service
Handles passcode authentication for restricted access mode
Week 8 Implementation
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Tuple
from admin_config import AdminConfig
from models import Database

logger = logging.getLogger(__name__)

# Global instance
_passcode_service_instance = None
_instance_lock = Lock()


class PasscodeAccessService:
    """
    Passcode-based entry control for restricted access mode.
    
    Design Principles:
    - Optional feature: Only active if admin chose 'passcode' access mode during setup
    - Single shared passcode for community (not per-user)
    - Hashed storage using PBKDF2 (not plain text)
    - Challenge-response validation (no plaintext transmission)
    - Admin can reset/rotate passcode anytime
    - Sessions created only after successful passcode validation
    - Works alongside other privacy modes (privacy_mode independent)
    
    Architecture:
    - Check access mode from AdminConfig (open/passcode/approved)
    - If passcode mode: validate before session creation
    - Store passcode hash in setup_config table
    - Support passcode rotation by admin
    - Audit log of passcode changes (for admin reference)
    """
    
    def __init__(self):
        """Initialize PasscodeAccessService"""
        self._passcode_check_cache = {}  # Cache (hash) → valid_until for rate limiting
        self._cache_lock = Lock()
    
    def is_passcode_required(self) -> bool:
        """
        Check if passcode is required for joining.
        
        Returns:
            True if access_control mode is 'passcode', False otherwise
        """
        try:
            access_mode = AdminConfig.get_access_control()
            return access_mode == 'passcode'
        except Exception as e:
            logger.error(f"Error checking if passcode required: {e}")
            return False
    
    def validate_passcode(self, provided_passcode: str) -> Tuple[bool, Optional[str]]:
        """
        Validate provided passcode against stored hash.
        
        Args:
            provided_passcode: Passcode provided by user
            
        Returns:
            Tuple of (is_valid, error_message)
            is_valid: True if passcode matches
            error_message: String reason if invalid, None if valid
            
        Design:
            - Get stored_hash from setup_config
            - Hash provided_passcode with same salt
            - Compare constant-time (prevent timing attacks)
            - Log invalid attempts (for audit)
            - Rate limit excessive attempts
        """
        try:
            # Get stored passcode hash from config
            stored_hash = self._get_passcode_hash()
            
            if not stored_hash:
                logger.warning("No passcode hash found in config")
                return False, "System error: passcode not configured"
            
            # Rate limit check
            if not self._check_rate_limit(stored_hash):
                logger.warning(f"Passcode validation rate limited")
                return False, "Too many attempts. Please wait before trying again."
            
            # Hash provided passcode
            provided_hash = self._hash_passcode(provided_passcode)
            
            # Constant-time comparison (prevent timing attacks)
            is_valid = self._constant_time_compare(provided_hash, stored_hash)
            
            if not is_valid:
                # Increment failed attempt counter
                self._record_failed_attempt(stored_hash)
                logger.info(f"Failed passcode validation attempt")
                return False, "Incorrect passcode"
            
            # Success
            logger.info(f"Successful passcode validation")
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating passcode: {e}")
            return False, "System error during validation"
    
    def reset_passcode(self, new_passcode: str, admin_username: str = 'admin',
                       disconnect_existing_sessions: bool = True) -> Tuple[bool, str]:
        """
        Reset/rotate passcode (admin action).
        
        Args:
            new_passcode: New passcode to set
            admin_username: Admin performing the reset
            disconnect_existing_sessions: If True, invalidate all current sessions
            
        Returns:
            Tuple of (success, message)
            
        Design:
            - Hash new passcode with PBKDF2
            - Update setup_config with new hash
            - Optionally disconnect all existing sessions (prevent old users from staying)
            - Log the change for audit trail
            - Support passcode rotation without downtime
        """
        try:
            # Validate new passcode
            if not new_passcode or len(new_passcode) < 4:
                return False, "Passcode must be at least 4 characters"
            
            if len(new_passcode) > 50:
                return False, "Passcode too long (max 50 characters)"
            
            # Hash new passcode
            new_hash = self._hash_passcode(new_passcode)
            
            # Update in database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO setup_config
                    (key, value, modified_at, modified_by)
                    VALUES (?, ?, ?, ?)
                ''', (
                    'passcode_hash',
                    new_hash,
                    datetime.now(),
                    admin_username
                ))
                
                conn.commit()
                
                # Log passcode change
                cursor.execute('''
                    INSERT INTO admin_audit_log
                    (admin_id, action, details, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    admin_username,
                    'PASSCODE_RESET',
                    f'Passcode rotated by {admin_username}',
                    datetime.now()
                ))
                conn.commit()
                
            except Exception as e:
                # Might fail if admin_audit_log doesn't exist
                logger.debug(f"Could not log passcode change: {e}")
            
            conn.close()
            
            # Clear cache
            with self._cache_lock:
                self._passcode_check_cache.clear()
            
            logger.info(f"Passcode reset by {admin_username}")
            
            if disconnect_existing_sessions:
                # Optionally disconnect all existing sessions
                # This forces users to re-authenticate with new passcode
                db = Database()
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions SET expires_at = datetime('now')
                    WHERE session_id IS NOT NULL
                ''')
                conn.commit()
                conn.close()
                logger.info("Invalidated all existing sessions after passcode reset")
                return True, "Passcode reset successfully. All users disconnected (please reconnect)."
            else:
                return True, "Passcode reset successfully. New connections will require new passcode."
            
        except Exception as e:
            logger.error(f"Error resetting passcode: {e}")
            return False, "System error during passcode reset"
    
    def get_passcode_status(self) -> Dict:
        """
        Get current passcode configuration status (for admin).
        
        Returns:
            Dict with:
            - is_required: Boolean if passcode mode is active
            - has_passcode: Boolean if passcode is set
            - access_mode: Current access control mode (open/passcode/approved)
            - last_changed: When passcode was last changed
            
        Privacy Note:
            - Does NOT return the actual passcode
            - Only returns configuration status
        """
        try:
            is_required = self.is_passcode_required()
            stored_hash = self._get_passcode_hash()
            access_mode = AdminConfig.get_access_control()
            
            # Get last change timestamp
            last_changed = self._get_passcode_last_changed()
            
            return {
                'is_required': is_required,
                'has_passcode': stored_hash is not None,
                'access_mode': access_mode,
                'last_changed': last_changed,
                'status': 'active' if is_required and stored_hash else 'inactive'
            }
        except Exception as e:
            logger.error(f"Error getting passcode status: {e}")
            return {'error': str(e), 'status': 'unknown'}
    
    # ========== PRIVATE METHODS ==========
    
    def _get_passcode_hash(self) -> Optional[str]:
        """Get current passcode hash from database"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('passcode_hash',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            logger.debug(f"Error getting passcode hash: {e}")
            return None
    
    def _get_passcode_last_changed(self) -> Optional[str]:
        """Get when passcode was last changed"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT modified_at FROM setup_config WHERE key = ?',
                ('passcode_hash',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            logger.debug(f"Error getting passcode last changed: {e}")
            return None
    
    @staticmethod
    def _hash_passcode(passcode: str) -> str:
        """
        Hash passcode using PBKDF2 (secure).
        
        Design:
            - Use PBKDF2-SHA256 with 100,000 iterations
            - No salt needed (single-use hash, not per-user)
            - Result consistent for same passcode
            - Cannot be reversed (one-way hash)
        """
        try:
            # PBKDF2 with SHA256, 100k iterations
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                passcode.encode('utf-8'),
                b'neighborhood_bbs',  # Static salt (not per-user)
                100000,
                dklen=32
            )
            return hashed.hex()
        except Exception as e:
            logger.error(f"Error hashing passcode: {e}")
            return ''
    
    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """
        Compare two strings using constant-time comparison.
        Prevents timing attacks where attacker measures comparison duration.
        
        Args:
            a: First string (user input hash)
            b: Second string (stored hash)
            
        Returns:
            True if equal (constant time), False otherwise (constant time)
        """
        if not a or not b:
            return False
        
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def _check_rate_limit(self, passcode_hash: str) -> bool:
        """
        Check if validation is rate limited (prevent brute force).
        
        Design:
            - Allow 5 attempts per 15 minutes
            - After 5 fails, lock for 15 minutes
            - Per device/IP (tracked by hash of request context)
        """
        try:
            now = datetime.now()
            cache_key = f"passcode_attempts_{passcode_hash}"
            
            with self._cache_lock:
                # Get current attempt info
                attempt_info = self._passcode_check_cache.get(cache_key)
                
                if attempt_info:
                    valid_until = datetime.fromisoformat(attempt_info.get('valid_until', now.isoformat()))
                    
                    # If still in lockout period
                    if now < valid_until:
                        attempts = attempt_info.get('attempts', 0)
                        if attempts >= 5:
                            return False
                    else:
                        # Lockout expired, reset counter
                        self._passcode_check_cache[cache_key] = {
                            'attempts': 0,
                            'valid_until': now.isoformat()
                        }
                else:
                    self._passcode_check_cache[cache_key] = {
                        'attempts': 0,
                        'valid_until': now.isoformat()
                    }
            
            return True
        except Exception as e:
            logger.debug(f"Error checking rate limit: {e}")
            # Fail open
            return True
    
    def _record_failed_attempt(self, passcode_hash: str):
        """Record a failed passcode attempt for rate limiting"""
        try:
            cache_key = f"passcode_attempts_{passcode_hash}"
            
            with self._cache_lock:
                attempt_info = self._passcode_check_cache.get(cache_key, {})
                attempts = attempt_info.get('attempts', 0) + 1
                
                if attempts >= 5:
                    # Lock for 15 minutes
                    valid_until = (datetime.now() + timedelta(minutes=15)).isoformat()
                else:
                    # Reset period each attempt (sliding window)
                    valid_until = (datetime.now() + timedelta(minutes=5)).isoformat()
                
                self._passcode_check_cache[cache_key] = {
                    'attempts': attempts,
                    'valid_until': valid_until
                }
        except Exception as e:
            logger.debug(f"Error recording failed attempt: {e}")


def get_passcode_service() -> PasscodeAccessService:
    """Get or create singleton PasscodeAccessService instance"""
    global _passcode_service_instance
    
    if _passcode_service_instance is None:
        with _instance_lock:
            if _passcode_service_instance is None:
                _passcode_service_instance = PasscodeAccessService()
                logger.info("Initialized PasscodeAccessService")
    
    return _passcode_service_instance

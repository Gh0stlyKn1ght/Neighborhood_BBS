"""
Authentication utilities - Password hashing, JWT token generation, and validation
"""

import jwt
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from models import db

logger = logging.getLogger(__name__)

# JWT configuration constants (read at runtime, not cached at import)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))


def _get_jwt_secret() -> str:
    """Return the JWT secret, failing fast if not configured.
    
    Reads from environment variable at runtime (not cached) to support
    dynamic configuration during testing and deployment.
    """
    secret = os.environ.get('JWT_SECRET')
    if not secret:
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. "
            "Set it to a cryptographically random value before starting the server."
        )
    if len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be at least 32 characters long. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return secret


class PasswordUtils:
    """Password hashing and verification utilities"""

    @staticmethod
    def hash_password(password, salt=None):  # salt param kept for API compat but ignored
        """
        Hash password using PBKDF2-SHA256 via Werkzeug (260k iterations).
        The salt parameter is ignored — Werkzeug generates a secure random salt internally.
        """
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password, stored_hash):
        """
        Verify password against stored Werkzeug hash.
        Uses constant-time comparison internally to prevent timing attacks.
        Also handles legacy SHA-256 'hash:salt' format for migration.
        """
        if not stored_hash:
            return False
        # Werkzeug hashes start with 'pbkdf2:' or 'scrypt:'; legacy start with hex chars
        if stored_hash.startswith('pbkdf2:') or stored_hash.startswith('scrypt:'):
            return check_password_hash(stored_hash, password)
        # Legacy SHA-256 format: "hexhash:salt" — migrate on next login
        try:
            import hashlib, hmac as _hmac
            stored_password_hash, legacy_salt = stored_hash.split(':', 1)
            computed = hashlib.sha256(f"{password}{legacy_salt}".encode()).hexdigest()
            return _hmac.compare_digest(computed, stored_password_hash)
        except (ValueError, AttributeError):
            logger.error("Invalid password hash format")
            return False

    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength.
        Returns: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"

        if len(password) < 12:
            return False, "Password must be at least 12 characters"

        if len(password) > 128:
            return False, "Password must be 128 characters or less"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numbers"

        return True, None


class TokenUtils:
    """JWT token generation and validation"""

    @staticmethod
    def _ensure_blacklist_table():
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jti TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    token_type TEXT DEFAULT 'user',
                    reason TEXT,
                    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti ON token_blacklist(jti)')
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _is_token_revoked(jti):
        """Check token revocation blacklist."""
        if not jti:
            return True

        try:
            TokenUtils._ensure_blacklist_table()
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT 1 FROM token_blacklist WHERE jti = ? LIMIT 1', (jti,))
                return cursor.fetchone() is not None
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Token blacklist check failed: {e}")
            return True

    @staticmethod
    def revoke_token(token, reason='logout', token_type='user'):
        """Revoke a JWT by persisting its JTI in token_blacklist."""
        try:
            payload = jwt.decode(
                token,
                _get_jwt_secret(),
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False},
            )
            jti = payload.get('jti')
            user_id = payload.get('user_id')
            if not jti:
                return False

            TokenUtils._ensure_blacklist_table()
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO token_blacklist (jti, user_id, token_type, reason)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (jti, user_id, token_type, reason),
                )
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")
            return False
    
    @staticmethod
    def generate_token(user_id, username, email, role='user', expires_in_hours=None):
        """
        Generate JWT token for user.
        
        Args:
            user_id: User ID
            username: Username
            email: User email
            role: User role (default: 'user')
            expires_in_hours: Token expiration time in hours (default: from config)
        
        Returns:
            JWT token string
        """
        if expires_in_hours is None:
            expires_in_hours = JWT_EXPIRATION_HOURS
        
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'role': role,
            'iat': now,
            'exp': now + timedelta(hours=expires_in_hours),
            'jti': secrets.token_hex(16),
        }

        token = jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
        logger.debug(f"Generated token for user {username}")
        return token
    
    @staticmethod
    def verify_token(token):
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            if TokenUtils._is_token_revoked(payload.get('jti')):
                logger.warning("Token revoked")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def extract_token_from_header(request_obj):
        """
        Extract JWT token from Authorization header.
        Expected format: Bearer <token>
        
        Returns:
            Token string or None
        """
        auth_header = request_obj.headers.get('Authorization', '')
        
        if not auth_header:
            return None
        
        try:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                return parts[1]
        except Exception as e:
            logger.warning(f"Error parsing Authorization header: {e}")
        
        return None


# Decorator for routes requiring user authentication
def require_user_auth(f):
    """
    Decorator to require user authentication via JWT token.
    Validates token and adds user info to request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = TokenUtils.extract_token_from_header(request)
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = TokenUtils.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request for use in route handler
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.user_role = payload.get('role', 'user')
        request.user_email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated_function


# Decorator for routes requiring admin authentication
def require_admin_auth(f):
    """
    Decorator to require admin user authentication.
    Must have JWT token with 'admin' or 'manager' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = TokenUtils.extract_token_from_header(request)
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = TokenUtils.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check for admin role
        role = payload.get('role', 'user')
        if role not in ['admin', 'manager', 'super_admin', 'moderator']:
            return jsonify({'error': 'Insufficient permissions', 'required_role': 'admin'}), 403
        
        # Add user info to request
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.user_role = role
        
        return f(*args, **kwargs)
    
    return decorated_function


class SessionTokenUtils:
    """Utilities for managing session-based tokens for anonymous and approved users"""
    
    @staticmethod
    def generate_session_token(session_id, nickname, expires_in_hours=24):
        """
        Generate a session token for tracking purposes.
        Used for anonymous users and pre-approved sessions.
        """
        payload = {
            'session_id': session_id,
            'nickname': nickname,
            'type': 'session',
            'jti': secrets.token_hex(16),
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }

        token = jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_session_token(token):
        """Verify session token and return payload"""
        try:
            payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            if TokenUtils._is_token_revoked(payload.get('jti')):
                return None
            return payload
        except jwt.InvalidTokenError:
            return None

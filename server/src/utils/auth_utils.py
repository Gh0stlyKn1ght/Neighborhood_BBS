"""
Authentication utilities - Password hashing, JWT token generation, and validation
"""

import jwt
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

# Secret key for JWT tokens (should be read from environment)
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-jwt-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))


class PasswordUtils:
    """Password hashing and verification utilities"""
    
    @staticmethod
    def hash_password(password, salt=None):
        """
        Hash password with SHA256 and optional salt.
        For security, consider using bcrypt in production.
        """
        if salt is None:
            salt = secrets.token_hex(16)  # Generate random 32-character salt
        
        # Create hash of password + salt
        hash_object = hashlib.sha256(f"{password}{salt}".encode())
        password_hash = hash_object.hexdigest()
        
        # Return hash:salt format for storage
        return f"{password_hash}:{salt}"
    
    @staticmethod
    def verify_password(password, stored_hash):
        """
        Verify password against stored hash.
        Stored hash should be in format "hash:salt"
        """
        try:
            stored_password_hash, salt = stored_hash.split(':')
            hash_object = hashlib.sha256(f"{password}{salt}".encode())
            computed_hash = hash_object.hexdigest()
            return computed_hash == stored_password_hash
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
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if len(password) > 128:
            return False, "Password must be 128 characters or less"
        
        # Check for at least one uppercase, one lowercase, one digit
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numbers"
        
        return True, None


class TokenUtils:
    """JWT token generation and validation"""
    
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
        
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
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
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
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
            return jsonify({'error': 'No token provided', 'hint': 'Include Authorization: Bearer <token> header'}), 401
        
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
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_session_token(token):
        """Verify session token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.InvalidTokenError:
            return None

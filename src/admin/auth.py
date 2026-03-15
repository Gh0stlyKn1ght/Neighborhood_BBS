"""
Admin authentication and authorization
"""

from functools import wraps
from flask import request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
import os
from models import AdminUser

# Admin session configuration
ADMIN_SESSION_TIMEOUT = int(os.environ.get('ADMIN_SESSION_TIMEOUT', 3600))  # 1 hour default


def hash_password(password):
    """Hash a password for secure storage"""
    return generate_password_hash(password)


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session
        if 'admin_id' not in session:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        # Check admin exists and is active
        admin_user = AdminUser.get_by_username(session.get('admin_username'))
        if not admin_user or not admin_user.get('is_active'):
            session.clear()
            return jsonify({'error': 'Admin account inactive or invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_role_required(required_role='admin'):
    """Decorator to require specific admin role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check if admin is authenticated
            if 'admin_id' not in session:
                return jsonify({'error': 'Admin authentication required'}), 401
            
            # Check role
            admin_user = AdminUser.get_by_username(session.get('admin_username'))
            if not admin_user or admin_user.get('role') != required_role:
                return jsonify({'error': f'Admin role "{required_role}" required'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

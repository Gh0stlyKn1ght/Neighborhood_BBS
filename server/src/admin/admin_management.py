"""
Phase 4 Week 11: Admin User Management API Routes
REST endpoints for multi-admin management with role-based access control

Endpoints:
  Public (no auth):
    - POST /api/admin-management/login - Admin authentication
    - POST /api/admin-management/validate-token - Validate admin token
  
  Protected (require admin auth):
    - Admin Management (super_admin only):
      - POST /api/admin-management/admin/create - Create new admin
      - GET /api/admin-management/admin/list - List all admins
      - GET /api/admin-management/admin/:admin_id - Get admin details
      - POST /api/admin-management/admin/:admin_id/role - Update admin role
      - POST /api/admin-management/admin/:admin_id/deactivate - Deactivate admin
    
    - Self-Service (all admins):
      - GET /api/admin-management/profile - Get own profile
      - POST /api/admin-management/change-password - Change own password
      - POST /api/admin-management/logout - Logout
    
    - Audit (all admins):
      - GET /api/admin-management/audit-log - View audit log

Author: AI Assistant
Date: 2026
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import secrets
import logging
import threading

from server import limiter
from services.admin_user_service import get_admin_user_service

logger = logging.getLogger(__name__)

admin_management_bp = Blueprint('admin_management', __name__, url_prefix='/api/admin-management')

# Session storage (in production, use Redis or database)
_admin_sessions = {}  # token -> {admin_id, username, role, expires_at, last_activity}
_sessions_lock = threading.Lock()

# Configuration
ADMIN_SESSION_TIMEOUT = 3600  # 1 hour
ADMIN_TOKEN_LENGTH = 32


# ============================================================================
# ADMIN AUTHENTICATION MIDDLEWARE
# ============================================================================

def require_admin_token(f):
    """Decorator to require valid admin token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.warning(f"Admin endpoint accessed without token: {request.path}")
            return jsonify({
                'status': 'error',
                'error': 'Admin authentication required',
                'hint': 'Include Authorization: Bearer <token> header'
            }), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate token
        with _sessions_lock:
            session = _admin_sessions.get(token)
        
        if not session:
            logger.warning(f"Invalid or expired token used")
            return jsonify({
                'status': 'error',
                'error': 'Invalid or expired token',
                'hint': 'Login again to get a new token'
            }), 401
        
        # Check expiration
        if datetime.utcnow() > session['expires_at']:
            with _sessions_lock:
                if token in _admin_sessions:
                    del _admin_sessions[token]
            logger.warning(f"Expired token used")
            return jsonify({
                'status': 'error',
                'error': 'Session expired',
                'hint': 'Login again to continue'
            }), 401
        
        # Add session to request context
        request.admin_id = session['admin_id']
        request.admin_username = session['username']
        request.admin_role = session['role']
        request.admin_token = token
        
        # Update last activity
        with _sessions_lock:
            if token in _admin_sessions:
                session['last_activity'] = datetime.utcnow()
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin_role(*required_roles):
    """Decorator to require specific admin role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'admin_role') or request.admin_role not in required_roles:
                logger.warning(f"Admin with role {getattr(request, 'admin_role', 'none')} tried to access {request.path}")
                return jsonify({
                    'status': 'error',
                    'error': 'Insufficient permissions',
                    'required_roles': list(required_roles),
                    'your_role': getattr(request, 'admin_role', 'none')
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            service = get_admin_user_service()
            
            if not service.check_permission(request.admin_id, permission):
                logger.warning(f"Admin {request.admin_id} denied permission: {permission}")
                return jsonify({
                    'status': 'error',
                    'error': 'Permission denied',
                    'required_permission': permission
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@admin_management_bp.route('/login', methods=['POST'])
@limiter.limit("10/minute")
def admin_login():
    """
    Authenticate admin and create session token.
    
    Request body:
    {
        "username": "admin_username",
        "password": "admin_password"
    }
    
    Returns:
    {
        "status": "ok",
        "token": "session_token",
        "admin_id": "admin_uuid",
        "username": "admin_username",
        "role": "super_admin|moderator|approver|viewer",
        "display_name": "Display Name",
        "expires_at": "2026-03-16T...Z",
        "message": "Welcome Admin!"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Validate inputs
        if not username or not password:
            logger.warning(f"Login attempt with missing credentials")
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate
        service = get_admin_user_service()
        success, message, admin_id = service.authenticate(username, password)
        
        if not success:
            logger.warning(f"Failed login attempt: {username}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid username or password'
            }), 401
        
        # Get admin details
        admin = service.get_admin(admin_id)
        
        # Create session token
        token = secrets.token_urlsafe(ADMIN_TOKEN_LENGTH)
        expires_at = datetime.utcnow() + timedelta(seconds=ADMIN_SESSION_TIMEOUT)
        
        with _sessions_lock:
            _admin_sessions[token] = {
                'admin_id': admin_id,
                'username': username,
                'role': admin['role'],
                'expires_at': expires_at,
                'last_activity': datetime.utcnow()
            }
        
        logger.info(f"Admin logged in: {username} ({admin['role']})")
        
        return jsonify({
            'status': 'ok',
            'token': token,
            'admin_id': admin_id,
            'username': username,
            'role': admin['role'],
            'display_name': admin['display_name'],
            'expires_at': expires_at.isoformat(),
            'message': f'Welcome {admin["display_name"] or username}!'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in admin_login: {e}", exc_info=True)
        return jsonify({'error': 'Login failed'}), 500


@admin_management_bp.route('/validate-token', methods=['POST'])
@limiter.limit("60/minute")
def validate_token():
    """
    Validate admin token without requiring re-authentication.
    
    Request body:
    {
        "token": "admin_token"
    }
    
    Returns:
    {
        "status": "ok",
        "valid": true,
        "admin_id": "admin_uuid",
        "username": "admin_username",
        "role": "super_admin|moderator|approver|viewer",
        "expires_at": "2026-03-16T...Z"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '').strip() if data else ''
        
        if not token:
            return jsonify({'valid': False, 'error': 'Token required'}), 400
        
        with _sessions_lock:
            session = _admin_sessions.get(token)
        
        if not session:
            return jsonify({'valid': False, 'error': 'Token not found'}), 401
        
        # Check expiration
        if datetime.utcnow() > session['expires_at']:
            with _sessions_lock:
                if token in _admin_sessions:
                    del _admin_sessions[token]
            return jsonify({'valid': False, 'error': 'Token expired'}), 401
        
        return jsonify({
            'status': 'ok',
            'valid': True,
            'admin_id': session['admin_id'],
            'username': session['username'],
            'role': session['role'],
            'expires_at': session['expires_at'].isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        return jsonify({'valid': False, 'error': 'Validation failed'}), 500


# ============================================================================
# PROTECTED: SELF-SERVICE ENDPOINTS
# ============================================================================

@admin_management_bp.route('/profile', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_token
def get_admin_profile():
    """
    Get current admin's profile.
    
    Returns:
    {
        "status": "ok",
        "admin": {
            "admin_id": "uuid",
            "username": "admin_username",
            "role": "super_admin|moderator|approver|viewer",
            "display_name": "Full Name",
            "email": "admin@example.com",
            "is_active": true,
            "permissions": [...],
            "last_login": "2026-03-16T...Z"
        }
    }
    """
    try:
        service = get_admin_user_service()
        admin = service.get_admin(request.admin_id)
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'admin': admin
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get profile'}), 500


@admin_management_bp.route('/change-password', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_token
def change_password():
    """
    Change own password.
    
    Request body:
    {
        "old_password": "current_password",
        "new_password": "new_password_min_8_chars"
    }
    
    Returns:
    {
        "status": "ok",
        "success": true,
        "message": "Password changed successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        # Validate
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords required'}), 400
        
        # Change password
        service = get_admin_user_service()
        success, message = service.change_password(
            request.admin_id,
            old_password,
            new_password
        )
        
        if success:
            logger.info(f"Admin changed password: {request.admin_username}")
            return jsonify({
                'status': 'ok',
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error changing password: {e}", exc_info=True)
        return jsonify({'error': 'Password change failed'}), 500


@admin_management_bp.route('/logout', methods=['POST'])
@limiter.limit("30/minute")
@require_admin_token
def admin_logout():
    """
    Logout admin and invalidate token.
    
    Returns:
    {
        "status": "ok",
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        # Remove token from sessions
        with _sessions_lock:
            if request.admin_token in _admin_sessions:
                del _admin_sessions[request.admin_token]
        
        logger.info(f"Admin logged out: {request.admin_username}")
        
        return jsonify({
            'status': 'ok',
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error logging out: {e}", exc_info=True)
        return jsonify({'error': 'Logout failed'}), 500


# ============================================================================
# PROTECTED: ADMIN MANAGEMENT ENDPOINTS (super_admin only)
# ============================================================================

@admin_management_bp.route('/admin/create', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_token
@require_admin_role('super_admin')
def create_admin():
    """
    Create new admin user (super_admin only).
    
    Request body:
    {
        "username": "new_admin",
        "password": "AdminPassword123!",
        "role": "moderator|approver|viewer",
        "display_name": "Full Name",
        "email": "admin@example.com"
    }
    
    Returns:
    {
        "status": "ok",
        "success": true,
        "admin_id": "uuid",
        "username": "new_admin",
        "role": "moderator",
        "message": "Admin created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', '').strip()
        display_name = data.get('display_name', '').strip()
        email = data.get('email', '').strip()
        
        # Validate required fields
        if not all([username, password, role]):
            return jsonify({'error': 'username, password, and role required'}), 400
        
        # Create admin
        service = get_admin_user_service()
        success, message, admin_id = service.create_admin(
            username=username,
            password=password,
            role=role,
            display_name=display_name,
            email=email,
            created_by=request.admin_username
        )
        
        if success:
            logger.info(f"New admin created by {request.admin_username}: {username} ({role})")
            return jsonify({
                'status': 'ok',
                'success': True,
                'admin_id': admin_id,
                'username': username,
                'role': role,
                'message': message
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error creating admin: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create admin'}), 500


@admin_management_bp.route('/admin/list', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_token
@require_admin_role('super_admin')
def list_admins():
    """
    List all admin users (super_admin only).
    
    Query parameters:
    - limit: Max number of results (default 100, max 1000)
    
    Returns:
    {
        "status": "ok",
        "admins": [...],
        "count": 5
    }
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        
        service = get_admin_user_service()
        admins = service.get_all_admins(limit=limit)
        
        return jsonify({
            'status': 'ok',
            'admins': admins,
            'count': len(admins)
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing admins: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list admins'}), 500


@admin_management_bp.route('/admin/<admin_id>', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_token
@require_admin_role('super_admin')
def get_admin_details(admin_id):
    """
    Get details for specific admin (super_admin only).
    
    Path parameter:
    - admin_id: ID of admin to retrieve
    
    Returns:
    {
        "status": "ok",
        "admin": {...}
    }
    """
    try:
        service = get_admin_user_service()
        admin = service.get_admin(admin_id)
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'admin': admin
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting admin details: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get admin details'}), 500


@admin_management_bp.route('/admin/<admin_id>/role', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_token
@require_admin_role('super_admin')
def update_admin_role(admin_id):
    """
    Update admin role (super_admin only).
    
    Path parameter:
    - admin_id: ID of admin to update
    
    Request body:
    {
        "role": "super_admin|moderator|approver|viewer"
    }
    
    Returns:
    {
        "status": "ok",
        "success": true,
        "message": "Role updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'role' not in data:
            return jsonify({'error': 'role required'}), 400
        
        new_role = data.get('role', '').strip()
        
        # Update role
        service = get_admin_user_service()
        success, message = service.update_role(
            admin_id,
            new_role,
            request.admin_username
        )
        
        if success:
            logger.info(f"Admin role updated by {request.admin_username}: {admin_id} -> {new_role}")
            return jsonify({
                'status': 'ok',
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error updating admin role: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update role'}), 500


@admin_management_bp.route('/admin/<admin_id>/deactivate', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_token
@require_admin_role('super_admin')
def deactivate_admin_account(admin_id):
    """
    Deactivate admin account (super_admin only).
    
    Path parameter:
    - admin_id: ID of admin to deactivate
    
    Returns:
    {
        "status": "ok",
        "success": true,
        "message": "Admin deactivated successfully"
    }
    """
    try:
        # Prevent self-deactivation
        if admin_id == request.admin_id:
            return jsonify({
                'error': 'Cannot deactivate your own account'
            }), 400
        
        # Deactivate
        service = get_admin_user_service()
        success, message = service.deactivate_admin(
            admin_id,
            request.admin_username
        )
        
        if success:
            logger.info(f"Admin deactivated by {request.admin_username}: {admin_id}")
            return jsonify({
                'status': 'ok',
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error deactivating admin: {e}", exc_info=True)
        return jsonify({'error': 'Failed to deactivate admin'}), 500


# ============================================================================
# PROTECTED: AUDIT LOG ENDPOINTS
# ============================================================================

@admin_management_bp.route('/audit-log', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_token
@require_permission('audit_log')
def get_audit_log():
    """
    Get audit log (requires audit_log permission).
    
    Query parameters:
    - limit: Max results (default 100, max 500)
    - admin_id: Filter by admin (optional)
    
    Returns:
    {
        "status": "ok",
        "audit_log": [...],
        "count": 42
    }
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        admin_filter = request.args.get('admin_id', '').strip() or None
        
        service = get_admin_user_service()
        logs = service.get_audit_log(limit=limit, admin_id=admin_filter)
        
        return jsonify({
            'status': 'ok',
            'audit_log': logs,
            'count': len(logs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting audit log: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get audit log'}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@admin_management_bp.route('/health', methods=['GET'])
@limiter.limit("60/minute")
def admin_management_health():
    """
    Health check endpoint (no auth required).
    
    Returns:
    {
        "status": "ok",
        "service": "admin-management-api",
        "timestamp": "2026-03-16T...Z"
    }
    """
    return jsonify({
        'status': 'ok',
        'service': 'admin-management-api',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

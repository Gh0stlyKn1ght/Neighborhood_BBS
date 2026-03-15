"""
Access Control Routes - PHASE 3

REST API endpoints for user registration, approval workflows, and access control management.

Endpoints:
  Public:
    - POST /api/access/register - Register new user
    - POST /api/access/verify-token - Verify access token
    - GET  /api/access/mode - Get current access mode
    
  Admin (X-Admin-Password required):
    - GET  /api/access/approvals - Get pending approvals
    - POST /api/access/approve - Approve user
    - POST /api/access/reject - Reject user
    - GET  /api/access/users - Get registered users
    - POST /api/access/whitelist/add - Add IP to whitelist
    - DELETE /api/access/whitelist/:ip - Remove IP from whitelist
    - GET  /api/access/whitelist - Get whitelisted IPs
    - GET  /api/access/stats - Get access control statistics

Author: AI Assistant
Date: 2025
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging

from setup_config import SetupConfig
from services.access_control_service import access_control_service

logger = logging.getLogger(__name__)

# Create blueprint
access_bp = Blueprint('access', __name__, url_prefix='/api/access')

# Rate limiting decorator
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def require_admin_password(f):
    """Decorator to require admin password authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.headers.get('X-Admin-Password')
        
        if not admin_password:
            return jsonify({'error': 'Missing admin password'}), 401
        
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Invalid admin password'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


# Public endpoints

@access_bp.route('/mode', methods=['GET'])
@limiter.limit("60/minute")
def get_access_mode():
    """Get current access control mode"""
    try:
        mode = access_control_service.get_access_mode()
        return jsonify({
            'success': True,
            'mode': mode
        }), 200
    except Exception as e:
        logger.error(f"Error getting access mode: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/register', methods=['POST'])
@limiter.limit("5/minute")
def register_user():
    """Register new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        reason = data.get('reason', '').strip()
        
        if not all([username, email, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Check if approval is required
        access_mode = access_control_service.get_access_mode()
        requires_approval = access_mode == AccessControlService.MODE_APPROVAL
        
        ip_address = request.remote_addr
        device_info = request.headers.get('User-Agent', '')
        
        success, message = access_control_service.register_user(
            username=username,
            email=email,
            password=password,
            requires_approval=requires_approval,
            ip_address=ip_address,
            device_info=device_info,
            reason=reason
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'requires_approval': requires_approval
            }), 201
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/verify-token', methods=['POST'])
@limiter.limit("10/minute")
def verify_token():
    """Verify access token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        token = data.get('token', '').strip()
        token_type = data.get('token_type', access_control_service.TOKEN_EMAIL_VERIFICATION)
        
        if not token:
            return jsonify({'success': False, 'error': 'Missing token'}), 400
        
        is_valid, username = access_control_service.verify_access_token(token, token_type)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': 'Token verified',
                'username': username
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 400
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Admin endpoints

@access_bp.route('/approvals', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_pending_approvals():
    """Get all pending approval requests"""
    try:
        approvals = access_control_service.get_pending_approvals()
        return jsonify({
            'success': True,
            'approvals': approvals,
            'count': len(approvals)
        }), 200
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/approve', methods=['POST'])
@require_admin_password
@limiter.limit("20/minute")
def approve_user():
    """Approve pending user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'error': 'Missing username'}), 400
        
        success, message = access_control_service.approve_user(
            username=username,
            approved_by='admin'
        )
        
        return jsonify({
            'success': success,
            'message': message
        }), (200 if success else 400)
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/reject', methods=['POST'])
@require_admin_password
@limiter.limit("20/minute")
def reject_user():
    """Reject pending user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        username = data.get('username', '').strip()
        rejection_reason = data.get('rejection_reason', '').strip()
        
        if not username:
            return jsonify({'success': False, 'error': 'Missing username'}), 400
        
        success, message = access_control_service.reject_user(
            username=username,
            rejection_reason=rejection_reason,
            rejected_by='admin'
        )
        
        return jsonify({
            'success': success,
            'message': message
        }), (200 if success else 400)
    except Exception as e:
        logger.error(f"Error rejecting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/users', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_registered_users():
    """Get list of registered users"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Clamp limits for security
        limit = min(limit, 100)
        offset = max(offset, 0)
        
        conn = access_control_service.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, is_active, requires_approval, approved_at, created_at
            FROM user_registrations
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        users = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM user_registrations')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users),
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error(f"Error getting registered users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/whitelist/add', methods=['POST'])
@require_admin_password
@limiter.limit("10/minute")
def add_to_whitelist():
    """Add IP address to whitelist"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        ip_address = data.get('ip_address', '').strip()
        description = data.get('description', '').strip()
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'Missing IP address'}), 400
        
        success, message = access_control_service.add_ip_to_whitelist(
            ip_address=ip_address,
            description=description,
            added_by='admin'
        )
        
        return jsonify({
            'success': success,
            'message': message
        }), (201 if success else 400)
    except Exception as e:
        logger.error(f"Error adding IP to whitelist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/whitelist/<ip_address>', methods=['DELETE'])
@require_admin_password
@limiter.limit("10/minute")
def remove_from_whitelist(ip_address):
    """Remove IP address from whitelist"""
    try:
        ip_address = ip_address.strip()
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'Missing IP address'}), 400
        
        success, message = access_control_service.remove_ip_from_whitelist(ip_address)
        
        return jsonify({
            'success': success,
            'message': message
        }), (200 if success else 400)
    except Exception as e:
        logger.error(f"Error removing IP from whitelist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/whitelist', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_whitelisted_ips():
    """Get all whitelisted IPs"""
    try:
        ips = access_control_service.get_whitelisted_ips(active_only=True)
        return jsonify({
            'success': True,
            'ips': ips,
            'count': len(ips)
        }), 200
    except Exception as e:
        logger.error(f"Error getting whitelisted IPs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@access_bp.route('/stats', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_access_statistics():
    """Get access control statistics"""
    try:
        stats = access_control_service.get_access_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting access stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Import at the end to avoid circular dependency
from services.access_control_service import AccessControlService

"""
Authentication Routes - Passcode and session management
Handles login flow, passcode validation, and session creation
Week 8 Implementation
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from server import limiter
from session_manager import SessionManager
from services.passcode_access_service import get_passcode_service
from services.approval_access_service import get_approval_service
from admin_config import AdminConfig
from setup_config import SetupConfig
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize services
passcode_service = get_passcode_service()
approval_service = get_approval_service()


# Admin authentication decorator
def require_admin_password(f):
    """Decorator to require admin password authentication.
    Checks X-Admin-Password header and verifies against stored admin password hash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.headers.get('X-Admin-Password')
        
        if not admin_password:
            logger.warning(f"Admin endpoint called without password: {request.path}")
            return jsonify({
                'status': 'error',
                'error': 'Admin authentication required'
            }), 401
        
        if not SetupConfig.verify_admin_password(admin_password):
            logger.warning(f"Admin endpoint called with invalid password: {request.path}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid credentials'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


@auth_bp.route('/access-info', methods=['GET'])
@limiter.limit("60/minute")
def get_access_info():
    """
    Get current access configuration (public information).
    
    Returns:
    - access_mode: 'open', 'passcode', or 'approved'
    - requires_passcode: Boolean if passcode is required
    - requires_approval: Boolean if approval is required
    - community_name: Community name (if set)
    
    Design:
    - Public endpoint (no auth required)
    - Helps client decide whether to show passcode prompt
    - Does NOT expose the passcode itself
    """
    try:
        access_mode = AdminConfig.get_access_control()
        
        return jsonify({
            'status': 'ok',
            'access_mode': access_mode,
            'requires_passcode': access_mode == 'passcode',
            'requires_approval': access_mode == 'approved',
            'join_message': 'Enter passcode to join' if access_mode == 'passcode' else 'Join chat'
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting access info: {e}")
        return jsonify({'error': 'Failed to get access info'}), 500


@auth_bp.route('/validate-passcode', methods=['POST'])
@limiter.limit("10/minute")
def validate_passcode():
    """
    Validate passcode and create session.
    
    Request body:
    {
        "passcode": "user_provided_passcode",
        "nickname": "user_chosen_nickname"
    }
    
    Returns:
    - session_id: UUID for this session
    - nickname: Confirmed nickname
    - connected_at: Session start time
    - expires_at: Session expiration time
    
    Design:
    - Step 1: Check if passcode is required
    - Step 2: Validate provided passcode against hash
    - Step 3: If valid, create session with nickname
    - Step 4: Return session_id for use in WebSocket
    - Rate limited to prevent brute force
    - No plaintext passcode in logs/storage
    
    Flow:
    1. Client checks access_mode via GET /access-info
    2. If requires_passcode:
       - Client shows passcode prompt
       - Client submits passcode + nickname via this endpoint
    3. Server validates passcode and creates session
    4. Client receives session_id
    5. Client connects to WebSocket with session_id
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        
        # Get inputs
        provided_passcode = data.get('passcode', '').strip()
        nickname = data.get('nickname', '').strip()
        
        # Validate inputs
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        if len(nickname) < 2 or len(nickname) > 50:
            return jsonify({'error': 'nickname must be 2-50 characters'}), 400
        
        # Check if passcode is required
        if not passcode_service.is_passcode_required():
            return jsonify({'error': 'passcode not required in this mode'}), 400
        
        # Validate passcode
        if not provided_passcode:
            return jsonify({'error': 'passcode required'}), 400
        
        is_valid, error_msg = passcode_service.validate_passcode(provided_passcode)
        
        if not is_valid:
            return jsonify({
                'status': 'unauthorized',
                'error': error_msg or 'Invalid passcode'
            }), 401
        
        # Create session with validated passcode
        session_data = SessionManager.create_session(nickname)

        if not session_data:
            return jsonify({'error': 'Failed to create session'}), 500

        if session_data.get('error') == 'nickname_taken':
            return jsonify({'error': session_data['message']}), 409
        
        logger.info(f"Session created via passcode auth: {session_data['session_id']} for {nickname}")
        
        return jsonify({
            'status': 'ok',
            'session_id': session_data['session_id'],
            'nickname': session_data['nickname'],
            'connected_at': session_data['connected_at'],
            'expires_at': session_data['expires_at'],
            'message': 'Passcode validated. Session created. Connect to WebSocket with session_id.'
        }), 200
    
    except Exception as e:
        logger.error(f"Error validating passcode: {e}", exc_info=True)
        return jsonify({'error': 'System error during authentication'}), 500


@auth_bp.route('/open-join', methods=['POST'])
@limiter.limit("30/minute")
def open_join():
    """
    Create session for open-access mode (no passcode required).
    
    Request body:
    {
        "nickname": "user_chosen_nickname"
    }
    
    Returns:
    - session_id: UUID for this session
    - nickname: Confirmed nickname
    - connected_at: Session start time
    - expires_at: Session expiration time
    
    Design:
    - Only available in 'open' access mode
    - No authentication required
    - Direct session creation
    - Used when access_mode is 'open'
    """
    try:
        # Check if open access is allowed
        access_mode = AdminConfig.get_access_control()
        if access_mode != 'open':
            return jsonify({'error': 'Open access not enabled in this mode'}), 403
        
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        nickname = data.get('nickname', '').strip()
        
        # Validate nickname
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        if len(nickname) < 2 or len(nickname) > 50:
            return jsonify({'error': 'nickname must be 2-50 characters'}), 400
        
        # Create session directly (no auth)
        session_data = SessionManager.create_session(nickname)

        if not session_data:
            return jsonify({'error': 'Failed to create session'}), 500

        if session_data.get('error') == 'nickname_taken':
            return jsonify({'error': session_data['message']}), 409
        
        logger.info(f"Session created via open join: {session_data['session_id']} for {nickname}")
        
        return jsonify({
            'status': 'ok',
            'session_id': session_data['session_id'],
            'nickname': session_data['nickname'],
            'connected_at': session_data['connected_at'],
            'expires_at': session_data['expires_at'],
            'message': 'Session created. Connect to WebSocket with session_id.'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in open join: {e}")
        return jsonify({'error': 'Failed to create session'}), 500


# Admin endpoints

@auth_bp.route('/admin/passcode-status', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def admin_get_passcode_status():
    """
    Get passcode configuration status (admin only).
    
    Returns:
    - is_required: Boolean if passcode mode is active
    - has_passcode: Boolean if passcode is set
    - access_mode: Current mode (open/passcode/approved)
    - last_changed: When passcode was last reset
    - status: 'active' or 'inactive'
    
    Design:
    - Returns status only (not the passcode itself)
    - Admin can check if passcode is configured
    - Shows when it was last changed
    - Verifies system is in passcode mode
    """
    try:
        status = passcode_service.get_passcode_status()
        
        return jsonify({
            'status': 'ok',
            'passcode_config': status
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting passcode status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500


@auth_bp.route('/admin/reset-passcode', methods=['POST'])
@require_admin_password
@limiter.limit("5/minute")
def admin_reset_passcode():
    """
    Reset/rotate passcode (admin action).
    
    Request body:
    {
        "new_passcode": "new_community_passcode",
        "disconnect_users": true  # Optional, default true
    }
    
    Returns:
    - success: Boolean if reset successful
    - message: Status message
    - Note: All existing users will be disconnected if disconnect_users=true
    
    Design:
    - Admin can rotate passcode anytime
    - New passcode takes effect immediately
    - Can optionally disconnect all existing users (force re-auth with new passcode)
    - Audit logged in admin_audit_log table
    - Uses PBKDF2 for secure hashing
    
    Example Flow:
    1. Admin detects someone shared old passcode with outsiders
    2. Admin calls this endpoint with new passcode
    3. All sessions invalidated (users must re-authenticate)
    4. Old passcode no longer works
    5. Users rejoin with new passcode
    
    Security:
    - Requires admin authentication (in production)
    - Rate limited to 5/minute to prevent accidental rotation
    - New passcode must be 4-50 characters
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400

        new_passcode = data.get('new_passcode', '').strip()
        disconnect_users = data.get('disconnect_users', True)
        
        # Validate new passcode
        if not new_passcode:
            return jsonify({'error': 'new_passcode required'}), 400
        
        if len(new_passcode) < 4:
            return jsonify({'error': 'passcode must be at least 4 characters'}), 400
        
        if len(new_passcode) > 50:
            return jsonify({'error': 'passcode must be at most 50 characters'}), 400
        
        # Reset passcode
        success, message = passcode_service.reset_passcode(
            new_passcode=new_passcode,
            admin_username='admin',  # In production, get from auth context
            disconnect_existing_sessions=disconnect_users
        )
        
        if success:
            logger.info(f"Passcode reset by admin (disconnect_users={disconnect_users})")
            return jsonify({
                'status': 'ok',
                'success': True,
                'message': message,
                'users_disconnected': disconnect_users
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error resetting passcode: {e}", exc_info=True)
        return jsonify({'error': 'System error during passcode reset'}), 500


# Approval-based access endpoints (Week 9)

@auth_bp.route('/request-approval', methods=['POST'])
@limiter.limit("10/minute")
def request_approval():
    """
    Submit approval request to join (user action).
    
    Request body:
    {
        "nickname": "requested_nickname",
        "request_reason": "Optional message to admin (e.g., neighbor info)"
    }
    
    Returns:
    - status: 'ok' if submitted
    - message: Status message with next steps
    
    Design:
    - Only available in 'approved' access mode
    - User submits nickname + optional reason
    - Request stored with pending status
    - Admin reviews and approves/rejects
    - User can check status via /approval-status endpoint
    """
    try:
        # Check if approval mode is enabled
        if not approval_service.is_approval_required():
            return jsonify({'error': 'Approval not required in this mode'}), 400
        
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        nickname = data.get('nickname', '').strip()
        request_reason = data.get('request_reason', '').strip()
        
        # Validate inputs
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        if len(nickname) < 2 or len(nickname) > 50:
            return jsonify({'error': 'nickname must be 2-50 characters'}), 400
        
        # Submit request
        success, message = approval_service.request_approval(nickname, request_reason)
        
        if success:
            logger.info(f"Approval request submitted for: {nickname}")
            return jsonify({
                'status': 'ok',
                'success': True,
                'message': message,
                'next_step': 'Check status with GET /api/auth/approval-status/{nickname}'
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'error': message
            }), 409
    
    except Exception as e:
        logger.error(f"Error in request_approval: {e}")
        return jsonify({'error': 'System error during request submission'}), 500


@auth_bp.route('/approval-status/<nickname>', methods=['GET'])
@limiter.limit("30/minute")
def check_approval_status(nickname):
    """
    Check if user is approved to join (user action).
    
    Path param: nickname
    
    Returns:
    - status: 'approved', 'pending', 'rejected', 'not_requested'
    - message: Human-readable status message
    - can_join: Boolean if user can join (only true if approved)
    
    Design:
    - Public endpoint (no auth)
    - User checks if their request was approved
    - Returns status and next steps
    - If approved, user gets session via /validate-approval-session endpoint
    """
    try:
        status, message = approval_service.check_approval_status(nickname)
        
        return jsonify({
            'status': 'ok',
            'approval_status': status,
            'message': message,
            'can_join': status == 'approved',
            'next_step': 'POST /api/auth/create-session to join' if status == 'approved' else 'Wait for admin review'
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking approval status: {e}")
        return jsonify({'error': 'Failed to check status'}), 500


@auth_bp.route('/create-approved-session', methods=['POST'])
@limiter.limit("30/minute")
def create_approved_session():
    """
    Create session for approved user (user action).
    
    Request body:
    {
        "nickname": "approved_nickname"
    }
    
    Returns:
    - session_id: UUID for this session
    - nickname: Confirmed nickname
    - message: Success message
    
    Design:
    - Only available after user is approved
    - Verify approval status first
    - Create session with approved nickname
    - User connects to WebSocket with session_id
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        nickname = data.get('nickname', '').strip()
        
        # Validate nickname
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        # Check if user is approved
        status, message = approval_service.check_approval_status(nickname)
        
        if status != 'approved':
            return jsonify({
                'error': f'Not approved to join (status: {status})',
                'message': message
            }), 403
        
        # Create session
        session_data = SessionManager.create_session(nickname)
        
        if not session_data:
            return jsonify({'error': 'Failed to create session'}), 500
        
        logger.info(f"Session created for approved user: {nickname}")
        
        return jsonify({
            'status': 'ok',
            'session_id': session_data['session_id'],
            'nickname': session_data['nickname'],
            'connected_at': session_data['connected_at'],
            'expires_at': session_data['expires_at'],
            'message': 'Approved! Session created. Connect to WebSocket with session_id.'
        }), 200
    
    except Exception as e:
        logger.error(f"Error creating approved session: {e}")
        return jsonify({'error': 'System error creating session'}), 500


# Admin approval management endpoints

@auth_bp.route('/admin/pending-requests', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_password
def admin_get_pending_requests():
    """
    Get pending approval requests (admin only).
    
    Requires: X-Admin-Password header with valid admin password
    
    Returns:
    - List of pending requests:
      - id, nickname, request_reason
      - created_at, days_pending
    
    Design:
    - Admin dashboard view of pending requests
    - Shows who's waiting and how long
    - Sorted by oldest first (FIFO)
    - Rate limited to 30/minute
    """
    try:
        
        requests = approval_service.get_pending_requests()
        
        return jsonify({
            'status': 'ok',
            'pending_requests': requests,
            'count': len(requests)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        return jsonify({'error': 'Failed to get pending requests'}), 500


@auth_bp.route('/admin/approve-user', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_password
def admin_approve_user():
    """
    Approve a user (admin action).
    
    Requires: X-Admin-Password header with valid admin password
    
    Request body:
    {
        "nickname": "nickname_to_approve"
    }
    
    Returns:
    - success: Boolean
    - message: Status message
    
    Design:
    - Find pending request
    - Update status to 'approved'
    - Record admin and timestamp
    - User can now join
    - Rate limited to 10/minute
    """
    try:
        
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        nickname = data.get('nickname', '').strip()
        
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        success, message = approval_service.approve_user(
            nickname,
            admin_username='admin'  # In production, get from auth
        )
        
        if success:
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
        logger.error(f"Error approving user: {e}")
        return jsonify({'error': 'System error during approval'}), 500


@auth_bp.route('/admin/reject-user', methods=['POST'])
@limiter.limit("10/minute")
@require_admin_password
def admin_reject_user():
    """
    Reject a user's approval request (admin action).
    
    Requires: X-Admin-Password header with valid admin password
    
    Request body:
    {
        "nickname": "nickname_to_reject",
        "reason": "Optional rejection reason"
    }
    
    Returns:
    - success: Boolean
    - message: Status message
    
    Design:
    - Find pending request
    - Update status to 'rejected'
    - User can request again later
    - Record reason for audit
    - Rate limited to 10/minute
    """
    try:
        
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        nickname = data.get('nickname', '').strip()
        reason = data.get('reason', '').strip()
        
        if not nickname:
            return jsonify({'error': 'nickname required'}), 400
        
        success, message = approval_service.reject_user(
            nickname,
            rejection_reason=reason,
            admin_username='admin'  # In production, get from auth
        )
        
        if success:
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
        logger.error(f"Error rejecting user: {e}")
        return jsonify({'error': 'System error during rejection'}), 500


@auth_bp.route('/admin/approval-history', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_password
def admin_get_approval_history():
    """
    Get approval history (approved and rejected users).
    
    Requires: X-Admin-Password header with valid admin password
    
    Returns:
    - List of approved/rejected users:
      - nickname, status, approved_by, approved_at
    
    Design:
    - Audit trail of approvals/rejections
    - Sorted by newest first
    - Shows who approved/rejected
    - Rate limited to 30/minute
    """
    try:
        
        history = approval_service.get_approval_history()
        
        return jsonify({
            'status': 'ok',
            'approval_history': history,
            'count': len(history)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting approval history: {e}")
        return jsonify({'error': 'Failed to get approval history'}), 500


@auth_bp.route('/admin/approval-stats', methods=['GET'])
@limiter.limit("30/minute")
@require_admin_password
def admin_get_approval_stats():
    """
    Get approval system statistics (admin dashboard).
    
    Requires: X-Admin-Password header with valid admin password
    
    Returns:
    - pending_count: Number waiting for approval
    - approved_count: Total approved users
    - rejected_count: Total rejected
    - oldest_pending_hours: How long oldest request waiting
    
    Design:
    - Aggregated statistics only
    - Shows system health
    - Helps admin prioritize work
    - Rate limited to 30/minute
    """
    try:
        # Admin authentication verified by decorator
        
        stats = approval_service.get_approval_statistics()
        
        return jsonify({
            'status': 'ok',
            'approval_statistics': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting approval stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


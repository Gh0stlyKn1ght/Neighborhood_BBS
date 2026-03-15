"""
User routes - Anonymous session management
Handles joining, changing nickname, session info
"""

from flask import Blueprint, jsonify, request, session
from session_manager import SessionManager
from mode_helper import ModeHelper
from admin_config import AdminConfig
from server import limiter
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/features', methods=['GET'])
@limiter.limit("60/minute")
def get_feature_flags():
    """
    Get enabled features for this BBS instance
    Returns mode-specific feature flags
    """
    try:
        flags = ModeHelper.get_feature_flags()
        return jsonify(flags), 200
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        return jsonify({'error': 'Failed to get features'}), 500


@user_bp.route('/join', methods=['POST'])
def join_community():
    """
    Join community as anonymous user
    Creates new session with chosen nickname
    
    Body: {nickname: "alice"}
    Returns: {session_id, nickname, connected_at, message}
    """
    try:
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        
        # Validate nickname
        if not nickname:
            return jsonify({'error': 'Nickname is required'}), 400
        
        if len(nickname) < 2:
            return jsonify({'error': 'Nickname must be at least 2 characters'}), 400
        
        if len(nickname) > 30:
            return jsonify({'error': 'Nickname must be 30 characters or less'}), 400
        
        # Check if only alphanumeric and common symbols
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', nickname):
            return jsonify({'error': 'Nickname can only contain letters, numbers, dashes, underscores, and spaces'}), 400
        
        # Create session
        session_data = SessionManager.create_session(nickname)
        if not session_data:
            return jsonify({'error': 'Failed to create session'}), 500
        
        # Store session ID in Flask session for tracking
        session['session_id'] = session_data['session_id']
        
        return jsonify({
            'session_id': session_data['session_id'],
            'nickname': session_data['nickname'],
            'connected_at': session_data['connected_at'],
            'message': f'Welcome to Neighborhood BBS, {nickname}!'
        }), 201
    
    except Exception as e:
        logger.error(f"Error joining community: {e}")
        return jsonify({'error': 'Failed to join community'}), 500


@user_bp.route('/info', methods=['GET'])
def get_session_info():
    """
    Get current user's session information
    
    Returns: {session_id, nickname, connected_at, expires_at, online_users}
    """
    try:
        session_id = session.get('session_id') or request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Update activity
        SessionManager.update_activity(session_id)
        
        # Get connected users
        connected = SessionManager.get_connected_users()
        active_count = SessionManager.get_active_sessions()
        
        return jsonify({
            'session_id': session_data['session_id'],
            'nickname': session_data['nickname'],
            'connected_at': session_data['connected_at'],
            'expires_at': session_data['expires_at'],
            'online_users': connected,
            'online_count': len(connected),
            'active_sessions': active_count
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({'error': 'Failed to get session info'}), 500


@user_bp.route('/change-nickname', methods=['POST'])
def change_nickname():
    """
    Change nickname mid-session
    
    Body: {session_id, new_nickname}
    Returns: {session_id, nickname, message}
    """
    try:
        session_id = session.get('session_id') or request.get_json().get('session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        data = request.get_json()
        new_nickname = data.get('new_nickname', '').strip()
        
        # Validate new nickname
        if not new_nickname:
            return jsonify({'error': 'New nickname is required'}), 400
        
        if len(new_nickname) < 2 or len(new_nickname) > 30:
            return jsonify({'error': 'Nickname must be 2-30 characters'}), 400
        
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', new_nickname):
            return jsonify({'error': 'Invalid characters in nickname'}), 400
        
        # Get current session
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Update nickname
        old_nickname = session_data['nickname']
        success = SessionManager.update_nickname(session_id, new_nickname)
        
        if not success:
            return jsonify({'error': 'Failed to update nickname'}), 500
        
        logger.info(f"User changed nickname from {old_nickname} to {new_nickname}")
        
        return jsonify({
            'session_id': session_id,
            'nickname': new_nickname,
            'previous_nickname': old_nickname,
            'message': f'Nickname changed to {new_nickname}'
        }), 200
    
    except Exception as e:
        logger.error(f"Error changing nickname: {e}")
        return jsonify({'error': 'Failed to change nickname'}), 500


@user_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """
    Disconnect user session
    
    Body: {session_id}
    Returns: {message}
    """
    try:
        session_id = session.get('session_id') or request.get_json().get('session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session already expired'}), 404
        
        # Close session
        SessionManager.close_session(session_id)
        
        # Clear Flask session
        session.pop('session_id', None)
        
        return jsonify({
            'message': f'Goodbye, {session_data["nickname"]}!'
        }), 200
    
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        return jsonify({'error': 'Failed to disconnect'}), 500


@user_bp.route('/online-users', methods=['GET'])
def get_online_users():
    """
    Get list of currently online users
    
    Returns: {users: [nicknames], count: number}
    """
    try:
        users = SessionManager.get_connected_users()
        return jsonify({
            'users': users,
            'count': len(users)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting online users: {e}")
        return jsonify({'error': 'Failed to get online users'}), 500


@user_bp.route('/stats', methods=['GET'])
def get_user_stats():
    """
    Get user session statistics (admin available)
    
    Returns: {active_sessions, total_sessions, sessions_today, avg_duration_minutes}
    """
    try:
        stats = SessionManager.get_session_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500


@user_bp.route('/validate-session', methods=['GET'])
def validate_session():
    """
    Validate if session is still active
    
    Query: session_id
    Returns: {valid: boolean}
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'valid': False}), 200
        
        session_data = SessionManager.get_session(session_id)
        is_valid = session_data is not None
        
        if is_valid:
            SessionManager.update_activity(session_id)
        
        return jsonify({'valid': is_valid}), 200
    
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return jsonify({'valid': False}), 200


@user_bp.route('/block', methods=['POST'])
def block_user():
    """
    Block a user (prevent seeing their messages)
    
    Body: {session_id, blocked_nickname, reason}
    Returns: {status: ok, blocked_users: [...]}
    """
    try:
        session_id = request.args.get('session_id') or request.get_json().get('session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        data = request.get_json()
        blocked_nickname = data.get('blocked_nickname', '').strip()
        reason = data.get('reason', '').strip() or None
        
        # Validate
        if not blocked_nickname:
            return jsonify({'error': 'Blocked nickname is required'}), 400
        
        # Get current session to verify it exists
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Block the user
        if not SessionManager.block_user(session_id, blocked_nickname, reason):
            return jsonify({'error': 'Failed to block user'}), 500
        
        # Return updated block list
        blocked_list = SessionManager.get_blocked_users(session_id)
        
        return jsonify({
            'status': 'ok',
            'blocked_users': blocked_list,
            'message': f'{blocked_nickname} has been blocked'
        }), 200
    
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        return jsonify({'error': 'Failed to block user'}), 500


@user_bp.route('/unblock', methods=['POST'])
def unblock_user():
    """
    Unblock a previously blocked user
    
    Body: {session_id, blocked_nickname}
    Returns: {status: ok, blocked_users: [...]}
    """
    try:
        session_id = request.args.get('session_id') or request.get_json().get('session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        data = request.get_json()
        blocked_nickname = data.get('blocked_nickname', '').strip()
        
        # Validate
        if not blocked_nickname:
            return jsonify({'error': 'Blocked nickname is required'}), 400
        
        # Get current session to verify it exists
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Unblock the user
        if not SessionManager.unblock_user(session_id, blocked_nickname):
            return jsonify({'error': 'Failed to unblock user'}), 500
        
        # Return updated block list
        blocked_list = SessionManager.get_blocked_users(session_id)
        
        return jsonify({
            'status': 'ok',
            'blocked_users': blocked_list,
            'message': f'{blocked_nickname} has been unblocked'
        }), 200
    
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        return jsonify({'error': 'Failed to unblock user'}), 500


@user_bp.route('/blocked-list', methods=['GET'])
def get_blocked_list():
    """
    Get list of blocked users for this session
    
    Query: session_id
    Returns: {blocked_users: [...]}
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Get current session to verify it exists
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Get blocked list
        blocked_list = SessionManager.get_blocked_users(session_id)
        
        return jsonify({
            'blocked_users': blocked_list,
            'count': len(blocked_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting blocked list: {e}")
        return jsonify({'error': 'Failed to get blocked list'}), 500

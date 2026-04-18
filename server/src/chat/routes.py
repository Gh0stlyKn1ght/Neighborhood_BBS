"""
Chat module - Real-time messaging with WebSocket and privacy support
Supports both anonymous sessions and authenticated users
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, rooms as socketio_rooms, disconnect
from server import socketio, limiter
from session_manager import SessionManager
from privacy_handler import PrivacyModeHandler
from mode_helper import ModeHelper
from moderation_service import ModerationService
from services.message_persistence_service import get_message_persistence_service
from services.moderation_integration import ModerationIntegrationService
from services.device_ban_service import get_device_ban_service
from models import ChatRoom, Database, User, Message
from utils.auth_utils import require_user_auth, TokenUtils
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Initialize services
privacy_handler = PrivacyModeHandler(ModeHelper.get_privacy_mode())
persistence_service = get_message_persistence_service()
moderation_integration = ModerationIntegrationService()
device_ban_service = get_device_ban_service()

# Track session_id to socket_id mapping for disconnect cleanup
_session_socket_mapping = {}


@chat_bp.route('/rooms', methods=['GET'])
@limiter.limit("60/minute")
def get_rooms():
    """Get list of available chat rooms"""
    try:
        rooms = ChatRoom.get_all()
        return jsonify({
            'rooms': [
                {
                    'id': r['id'],
                    'name': r['name'],
                    'description': r['description']
                }
                for r in rooms
            ]
        }), 200
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@limiter.limit("60/minute")
def get_room_messages(room_id):
    """
    Get message history for a room
    Respects privacy mode settings
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Clamp limit
        limit = min(limit, 100)
        offset = max(offset, 0)
        
        # Get messages from privacy handler
        messages = privacy_handler.get_message_history(
            room_id=room_id,
            limit=100
        )
        
        # Paginate
        paginated = messages[offset:offset+limit]
        
        return jsonify({
            'messages': paginated,
            'total': len(messages),
            'offset': offset,
            'limit': limit,
            'privacy_mode': privacy_handler.privacy_mode
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting room messages: {e}")
        return jsonify({'error': 'Failed to get messages'}), 500


@chat_bp.route('/rooms/<int:room_id>/users', methods=['GET'])
@limiter.limit("60/minute")
def get_room_users(room_id):
    """Get list of currently online users"""
    try:
        user_list = SessionManager.get_connected_users()
        
        return jsonify({
            'users': user_list,
            'count': len(user_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting room users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500


@chat_bp.route('/send-message', methods=['POST'])
@limiter.limit("30/minute")
def send_message():
    """
    Send a message to a room
    WebSocket is preferred but REST endpoint available
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        room_id = data.get('room_id', 1)
        text = data.get('text', '').strip()
        
        # Validate
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        if not text:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Message too long (max 5000 chars)'}), 400
        
        # Validate session — renamed to user_session to avoid shadowing Flask's session
        user_session = SessionManager.get_session(session_id)
        if not user_session:
            return jsonify({'error': 'Session invalid or expired'}), 401
        
        nickname = user_session['nickname']
        
        # Save message
        message = privacy_handler.save_message(
            session_id=session_id,
            nickname=nickname,
            text=text,
            room_id=room_id
        )
        
        if not message:
            return jsonify({'error': 'Failed to save message'}), 500
        
        # Update activity
        SessionManager.update_activity(session_id)
        
        return jsonify({
            'message_id': message.get('id'),
            'timestamp': message.get('timestamp'),
            'nickname': nickname
        }), 201
    
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


# ==================== AUTHENTICATED USER MESSAGING ====================

@chat_bp.route('/send-message-auth', methods=['POST'])
@require_user_auth
@limiter.limit("60/minute")
def send_message_auth():
    """
    Send a message as authenticated user
    Messages are associated with user account (not anonymous session)
    
    Body: {room_id, text}
    Returns: {message_id, user_id, username, timestamp}
    """
    try:
        data = request.get_json()
        room_id = data.get('room_id', 1)
        text = data.get('text', '').strip()
        
        # Validate
        if not text:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Message too long (max 5000 chars)'}), 400
        
        # Get user data
        user_data = User.get_by_id(request.user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Save message with user_id
        conn = Database().get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT INTO messages 
               (room_id, author, content, nickname)
               VALUES (?, ?, ?, ?)''',
            (room_id, user_data['username'], text, user_data['username'])
        )
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        # Broadcast via WebSocket if available
        socketio.emit('new_message', {
            'message_id': message_id,
            'room_id': room_id,
            'author': user_data['username'],
            'user_id': request.user_id,
            'text': text,
            'timestamp': datetime.utcnow().isoformat(),
            'is_authenticated': True
        }, room=f'room_{room_id}')
        
        logger.info(f"Authenticated user {user_data['username']} sent message to room {room_id}")
        
        return jsonify({
            'message_id': message_id,
            'user_id': request.user_id,
            'username': user_data['username'],
            'room_id': room_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 201
    
    except Exception as e:
        logger.error(f"Error sending authenticated message: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


@chat_bp.route('/rooms/<int:room_id>/messages-auth', methods=['GET'])
@require_user_auth
@limiter.limit("60/minute")
def get_room_messages_auth(room_id):
    """
    Get message history for an authenticated user
    Includes author information and user associations
    
    Returns: {messages: [{id, author, user_id, text, created_at}], total, offset, limit}
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Clamp limit
        limit = min(limit, 100)
        offset = max(offset, 0)
        
        # Get messages from database
        conn = Database().get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, author, content, created_at 
               FROM messages 
               WHERE room_id = ? 
               ORDER BY created_at DESC 
               LIMIT ? OFFSET ?''',
            (room_id, limit, offset)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'author': row[1],
                'text': row[2],
                'created_at': row[3]
            })
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM messages WHERE room_id = ?', (room_id,))
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'messages': messages,
            'total': total,
            'offset': offset,
            'limit': limit,
            'room_id': room_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting authenticated room messages: {e}")
        return jsonify({'error': 'Failed to get messages'}), 500


@chat_bp.route('/user/<username>/profile', methods=['GET'])
@limiter.limit("60/minute")
def get_user_public_profile(username):
    """
    Get public profile information for a user
    Shows basic info visible in chat (read-only, no auth required)
    
    Returns: {user_id, username, created_at, message_count}
    """
    try:
        user_data = User.get_by_username(username)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get message count for this user
        conn = Database().get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM messages WHERE author = ?',
            (username,)
        )
        message_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'user_id': user_data['id'],
            'username': user_data['username'],
            'created_at': user_data['created_at'],
            'message_count': message_count,
            'is_active': user_data['is_active']
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get user profile'}), 500


@chat_bp.route('/privacy-info', methods=['GET'])
@limiter.limit("60/minute")
def get_privacy_info():
    """
    Get information about message privacy mode and storage
    
    Returns:
    - privacy_mode: Full description of current mode
    - message_retention: How long messages are kept
    - storage_location: Where messages are stored
    - statistics: Message count and cleanup info
    """
    try:
        stats = persistence_service.get_statistics()
        
        mode = persistence_service.get_privacy_mode()
        
        if mode == 'full_privacy':
            privacy_description = {
                'mode': 'FULL_PRIVACY',
                'description': 'Maximum privacy: messages stored in RAM only',
                'message_retention': 'Session-based (deleted on disconnect)',
                'storage_location': 'In-memory only (not persisted)',
                'tracking': 'None - no session linking to messages',
                'use_case': 'Communities prioritizing privacy over history'
            }
        
        elif mode == 'hybrid':
            privacy_description = {
                'mode': 'HYBRID',
                'description': 'Balanced: messages persist for 7 days then auto-delete',
                'message_retention': '7 days (then automatic deletion)',
                'storage_location': 'Persistent database',
                'tracking': 'No user IDs - only nickname + timestamp',
                'use_case': 'Communities needing some history but prefer privacy'
            }
        
        elif mode == 'persistent':
            privacy_description = {
                'mode': 'PERSISTENT',
                'description': 'All messages saved permanently (requires privacy agreement)',
                'message_retention': 'Permanent',
                'storage_location': 'Persistent database',
                'tracking': 'Full message history available',
                'use_case': 'Q&A, support, or documentation communities'
            }
        
        else:
            privacy_description = {'error': 'Unknown privacy mode'}
        
        return jsonify({
            'privacy_info': privacy_description,
            'statistics': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting privacy info: {e}")
        return jsonify({'error': 'Failed to get privacy info'}), 500


@chat_bp.route('/messages/statistics', methods=['GET'])
@limiter.limit("30/minute")
def get_message_statistics():
    """
    Get message storage statistics
    
    Query params:
    - room_id: Optional room ID to filter by
    
    Returns message count and retention info based on privacy mode
    """
    try:
        room_id = request.args.get('room_id', type=int)
        
        stats = persistence_service.get_statistics()
        mode = persistence_service.get_privacy_mode()
        
        # Add mode-specific stats
        message_count = persistence_service.get_message_count(room_id)
        
        return jsonify({
            'privacy_mode': mode,
            'message_count': message_count,
            'statistics': stats,
            'room_filter': room_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting message statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@chat_bp.route('/moderation/session-status', methods=['GET'])
@limiter.limit("60/minute")
def get_session_moderation_status():
    """
    Get moderation status for a session (privacy-aware violations only)
    
    Query params:
    - session_id: Required session ID to check
    
    Returns:
    - is_muted: Whether session is currently muted/blocked
    - muted_until: When mute expires
    - violations_in_window: Number of violations in current tracking window
    - warnings_remaining: How many more violations before auto-mute
    - can_speak: Whether user can send messages
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        # Validate session exists
        session = SessionManager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session invalid or expired'}), 401
        
        # Get moderation status for session
        status = ModerationIntegrationService.get_session_status(session_id)
        
        return jsonify({
            'status': 'ok',
            'moderation_status': status,
            'privacy_note': 'Status is session-based only (not cross-session tracking)'
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting session moderation status: {e}")
        return jsonify({'error': 'Failed to get moderation status'}), 500


@chat_bp.route('/moderation/statistics', methods=['GET'])
@limiter.limit("30/minute")
def get_moderation_statistics():
    """
    Get aggregate moderation statistics (privacy-aware aggregates only)
    
    Returns:
    - active_sessions_tracked: Sessions with active violations tracked
    - muted_sessions: Number of currently muted sessions
    - enabled_rules: Number of active content filtering rules
    - unresolved_violations: Total unresolved violation reports
    - privacy_mode: Confirmation of privacy-aware session tracking
    """
    try:
        stats = ModerationIntegrationService.get_statistics()
        
        return jsonify({
            'status': 'ok',
            'moderation_statistics': stats,
            'disclaimer': 'All statistics are aggregated and session-based (no user tracking)'
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting moderation statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


# Device-based escalation endpoints (Week 7)

@chat_bp.route('/admin/device-bans', methods=['GET'])
@limiter.limit("30/minute")
def get_device_bans():
    """
    Get list of active device bans (admin only).
    
    Returns:
    - List of banned devices with:
      - device_id: Hash-based device identifier
      - device_type: Type of device (browser, phone, etc)
      - ip_address: IP address of banned device
      - ban_reason: Reason for ban
      - banned_by: Admin who performed ban
      - banned_at: Timestamp of ban
      - expires_at: When ban expires (null = permanent)
    
    Privacy Note:
    - MAC addresses hashed (never exposed)
    - No user/nickname linked to bans
    - Device-level escalation only
    """
    try:
        # Verify admin access (in production, check auth header)
        bans = device_ban_service.get_active_bans()
        
        return jsonify({
            'status': 'ok',
            'active_bans': bans,
            'count': len(bans),
            'note': 'Device-level escalation bans (second-to-last resort after session muting)'
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting device bans: {e}")
        return jsonify({'error': 'Failed to get device bans'}), 500


@chat_bp.route('/admin/ban-device', methods=['POST'])
@limiter.limit("10/minute")
def ban_device_admin():
    """
    Ban a device (admin escalation action).
    
    Request body:
    {
        "device_id": "hash123...",
        "ban_reason": "Repeated abuse after session muting",
        "expire_hours": 48,  # Optional: null = permanent
        "device_type": "browser"  # Optional
    }
    
    Returns:
    - success: true if device banned
    - device_id: The device that was banned
    - message: Status message
    
    Design:
    - Device-level ban (escalation above session muting)
    - Requires admin approval (would include auth check in production)
    - Can be temporary (auto-expires) or permanent
    - No user/nickname tracking (privacy-first)
    - Hard stop for banned devices (they cannot reconnect)
    """
    try:
        data = request.get_json()
        device_id = data.get('device_id', '').strip()
        ban_reason = data.get('ban_reason', 'Admin ban').strip()
        expire_hours = data.get('expire_hours')
        device_type = data.get('device_type', 'unknown').strip()
        
        # Validate
        if not device_id:
            return jsonify({'error': 'device_id required'}), 400
        
        if not ban_reason:
            return jsonify({'error': 'ban_reason required'}), 400
        
        # Perform ban
        success = device_ban_service.ban_device(
            device_id=device_id,
            device_type=device_type,
            ban_reason=ban_reason,
            banned_by='admin',  # In production, get from auth context
            expire_hours=expire_hours
        )
        
        if success:
            return jsonify({
                'status': 'ok',
                'success': True,
                'device_id': device_id,
                'message': f'Device banned: {ban_reason}',
                'expires': expire_hours is not None,
                'expire_hours': expire_hours
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Device already banned or creation failed'
            }), 409
    
    except Exception as e:
        logger.error(f"Error banning device: {e}")
        return jsonify({'error': 'Failed to ban device'}), 500


@chat_bp.route('/admin/unban-device', methods=['POST'])
@limiter.limit("10/minute")
def unban_device_admin():
    """
    Unban a device (admin second-chance action).
    
    Request body:
    {
        "device_id": "hash123..."
    }
    
    Returns:
    - success: true if device unbanned
    - device_id: The device that was unbanned
    - message: Status message
    
    Design:
    - Remove active ban for device
    - Allows device to reconnect
    - Should require admin approval (auth check in production)
    - No audit trail required (already logged in ban creation)
    """
    try:
        data = request.get_json()
        device_id = data.get('device_id', '').strip()
        
        # Validate
        if not device_id:
            return jsonify({'error': 'device_id required'}), 400
        
        # Perform unban
        success = device_ban_service.unban_device(
            device_id=device_id,
            unbanned_by='admin'  # In production, get from auth context
        )
        
        if success:
            return jsonify({
                'status': 'ok',
                'success': True,
                'device_id': device_id,
                'message': 'Device unbanned (second chance granted)'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Device not found or already unbanned'
            }), 404
    
    except Exception as e:
        logger.error(f"Error unbanning device: {e}")
        return jsonify({'error': 'Failed to unban device'}), 500


# WebSocket events for real-time chat

@socketio.on('join_room')
def on_join_room(data):
    """WebSocket: Join a chat room"""
    try:
        session_id = data.get('session_id')
        room_id = data.get('room_id', 1)
        
        # Validate session
        session = SessionManager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session invalid'})
            return
        
        nickname = session['nickname']
        room_name = f"room_{room_id}"
        
        # Track session to socket mapping for disconnect cleanup
        from flask_socketio import request as socketio_request
        _session_socket_mapping[socketio_request.sid] = session_id
        
        # Join SocketIO room
        join_room(room_name)
        
        # Broadcast join notification
        message = {
            'type': 'user_joined',
            'nickname': nickname,
            'timestamp': datetime.now().isoformat(),
            'online_count': SessionManager.get_active_sessions()
        }
        
        emit('user_joined', message, room=room_name)
        logger.info(f"{nickname} joined room {room_id}")
    
    except Exception as e:
        logger.error(f"Error in join_room: {e}")
        emit('error', {'message': str(e)})


@socketio.on('message')
def on_message(data):
    """WebSocket: Send a message to room with privacy-aware moderation checks"""
    try:
        session_id = data.get('session_id')
        room_id = data.get('room_id', 1)
        text = data.get('text', '').strip()
        
        if not text:
            return
        
        if len(text) > 5000:
            emit('error', {'message': 'Message too long'})
            return
        
        # Validate session
        session = SessionManager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session expired'})
            return
        
        nickname = session['nickname']
        room_name = f"room_{room_id}"
        
        # PHASE 2: Check if user (by nickname) is suspended
        # NOTE: For FULL_PRIVACY mode, this only applies to current session
        if ModerationService.is_user_suspended(nickname):
            emit('error', {'message': 'Your account is suspended and cannot send messages'})
            logger.warning(f"Suspended user {nickname} attempted to send message")
            return
        
        # WEEK 6: Privacy-aware moderation check (session-based, not user-based)
        # This checks violations per session to avoid tracking across sessions
        moderation_result = ModerationIntegrationService.check_message_for_violations(
            message_text=text,
            session_id=session_id,
            nickname=nickname
        )
        
        # Handle moderation result
        if not moderation_result['passed']:
            # Moderation check failed - message blocked
            emit('error', {
                'message': moderation_result['reason'],
                'severity': moderation_result['severity'],
                'violations': len(moderation_result['violations'])
            })
            logger.warning(f"Session {session_id} ({nickname}): Message blocked - {moderation_result['reason']}")
            
            # Also check with global nickname suspension (cross-session moderation)
            violation_details = f"Triggered {len(moderation_result['violations'])} rule(s)"
            ModerationService.report_violation(
                nickname=nickname,
                violation_type=ModerationService.VIOLATION_CUSTOM,
                description=violation_details,
                reported_by='system',
                evidence=text
            )
            
            return
        
        elif moderation_result['action'] == 'warn':
            # Message passed but flagged - warn user but allow
            emit('warning', {
                'message': moderation_result['reason'],
                'violations': len(moderation_result['violations'])
            })
            logger.info(f"Session {session_id} ({nickname}): Message warned - {len(moderation_result['violations'])} rules triggered")
        
        # Save message using privacy handler
        message = privacy_handler.save_message(
            session_id=session_id,
            nickname=nickname,
            text=text,
            room_id=room_id
        )
        
        # Update activity
        SessionManager.update_activity(session_id)
        
        # Broadcast message
        chat_message = {
            'nickname': nickname,
            'text': moderation_result['filtered_message'],
            'timestamp': datetime.now().isoformat(),
            'room_id': room_id,
            'moderation_flagged': len(moderation_result['violations']) > 0
        }
        
        emit('message', chat_message, room=room_name)
        logger.debug(f"{nickname} (session {session_id}) sent message to room {room_id}")
    
    except Exception as e:
        logger.error(f"Error in message: {e}")
        emit('error', {'message': str(e)})


@socketio.on('change_nickname')
def on_change_nickname(data):
    """WebSocket: Change nickname"""
    try:
        session_id = data.get('session_id')
        new_nickname = data.get('new_nickname', '').strip()
        
        if not new_nickname or len(new_nickname) < 2 or len(new_nickname) > 30:
            emit('error', {'message': 'Nickname must be 2-30 characters'})
            return
        
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', new_nickname):
            emit('error', {'message': 'Invalid characters in nickname'})
            return
        
        # Validate session
        session = SessionManager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session expired'})
            return
        
        old_nickname = session['nickname']
        
        # Update nickname
        result = SessionManager.update_nickname(session_id, new_nickname)
        if result.get('error') == 'nickname_taken':
            emit('error', {'message': 'That nickname is already in use'})
            return
        if result.get('error') == 'session_not_found':
            emit('error', {'message': 'Session expired'})
            return
        if not result.get('ok'):
            emit('error', {'message': 'Failed to change nickname'})
            return
        
        # Broadcast change
        change_event = {
            'type': 'nickname_changed',
            'old_nickname': old_nickname,
            'new_nickname': new_nickname,
            'timestamp': datetime.now().isoformat()
        }
        
        emit('nickname_changed', change_event, broadcast=True, skip_sid=True)
        logger.info(f"User changed nickname from {old_nickname} to {new_nickname}")
    
    except Exception as e:
        logger.error(f"Error in change_nickname: {e}")
        emit('error', {'message': str(e)})


@socketio.on('leave_room')
def on_leave_room(data):
    """WebSocket: Leave a chat room"""
    try:
        session_id = data.get('session_id')
        room_id = data.get('room_id', 1)
        
        # Validate session
        session = SessionManager.get_session(session_id)
        if not session:
            return
        
        nickname = session['nickname']
        room_name = f"room_{room_id}"
        
        # Leave SocketIO room
        leave_room(room_name)
        
        # Broadcast leave notification
        message = {
            'type': 'user_left',
            'nickname': nickname,
            'timestamp': datetime.now().isoformat(),
            'online_count': SessionManager.get_active_sessions()
        }
        
        emit('user_left', message, room=room_name, skip_sid=True)
        logger.info(f"{nickname} left room {room_id}")
    
    except Exception as e:
        logger.error(f"Error in leave_room: {e}")


@socketio.on('disconnect')
def on_disconnect():
    """WebSocket: User disconnected - clean up messages and moderation tracking"""
    try:
        from flask_socketio import request as socketio_request
        
        socket_id = socketio_request.sid
        session_id = _session_socket_mapping.pop(socket_id, None)
        
        if session_id:
            # Clean up messages for this session (full privacy mode)
            persistence_service.on_user_disconnect(session_id)
            
            # Clean up moderation data for this session (privacy-aware cleanup)
            # Removes session-based violation tracking when session ends
            ModerationIntegrationService.cleanup_expired_sessions([session_id])
            
            logger.info(f"User disconnected: cleaned up session {session_id} (messages, moderation tracking)")
        else:
            logger.debug("User disconnected (no session mapping)")
    
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")


@socketio.on('connect')
def on_connect():
    """
    WebSocket: User connected
    
    Device-based escalation check (Week 7):
    1. Extract device information (IP, User-Agent, MAC if available)
    2. Check if device is banned
    3. Reject connection for banned devices (hard stop)
    4. Allow connection and track device_id for future bans
    """
    try:
        # Check device ban status before allowing connection
        device_allowed, ban_reason, device_info = device_ban_service.check_device_allowed()
        
        if not device_allowed:
            logger.warning(f"Rejecting banned device connection: {ban_reason} | {device_info}")
            emit('error', {
                'message': ban_reason or 'Device banned',
                'type': 'device_ban',
                'timestamp': datetime.now().isoformat()
            })
            # Disconnect immediately (hard stop for banned devices)
            disconnect()
            return
        
        # Store device_id for this session (use as session key for future bans)
        device_id = device_info.get('device_id')
        if device_id:
            # Store in session context for later reference  
            # This allows admin to ban by device_id if needed in future
            from flask_socketio import session as socketio_session
            socketio_session['device_id'] = device_id
            socketio_session['device_info'] = {
                'ip': device_info.get('ip_address'),
                'has_mac': device_info.get('mac_hashed', False)
            }
        
        logger.debug(f"User connected to WebSocket | Device: {device_info.get('device_id')} | Ban Status: {device_info.get('ban_status')}")
        
    except Exception as e:
        logger.error(f"Error in connect handler: {e}", exc_info=True)
        # Fail open - allow connection on error
        pass

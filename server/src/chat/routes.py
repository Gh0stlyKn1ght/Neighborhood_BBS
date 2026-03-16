"""
Chat module - Real-time messaging with WebSocket and privacy support
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, rooms as socketio_rooms
from server import socketio, limiter
from session_manager import SessionManager
from privacy_handler import PrivacyModeHandler
from mode_helper import ModeHelper
from moderation_service import ModerationService
from services.message_persistence_service import get_message_persistence_service
from models import ChatRoom, Database
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Initialize services
privacy_handler = PrivacyModeHandler(ModeHelper.get_privacy_mode())
persistence_service = get_message_persistence_service()

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
        return jsonify({'error': str(e)}), 500


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
        
        # Validate session
        session = SessionManager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session invalid or expired'}), 401
        
        nickname = session['nickname']
        
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
    """WebSocket: Send a message to room with moderation checks"""
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
        
        # PHASE 2: Check if user is suspended
        if ModerationService.is_user_suspended(nickname):
            emit('error', {'message': 'Your account is suspended and cannot send messages'})
            logger.warning(f"Suspended user {nickname} attempted to send message")
            return
        
        # PHASE 2: Check message content for moderation violations
        moderation_check = ModerationService.check_message_content(text)
        
        if moderation_check['violated']:
            # Report violation
            violation_details = f"Triggered {len(moderation_check['rules_triggered'])} rule(s): {', '.join([r['rule_name'] for r in moderation_check['rules_triggered']])}"
            ModerationService.report_violation(
                nickname=nickname,
                violation_type=ModerationService.VIOLATION_CUSTOM,
                description=violation_details,
                reported_by='system',
                evidence=text
            )
            
            # Determine action based on severity
            max_severity = moderation_check['severity']
            
            if max_severity == ModerationService.SEVERITY_CRITICAL:
                # Suspend user immediately
                ModerationService.suspend_user(nickname, 'temporary', f'Auto-suspended for {max_severity} violation', 'system', 24)
                emit('error', {'message': 'Your message violates community standards. Your account has been suspended.'})
                logger.critical(f"AUTO-SUSPEND: {nickname} for critical violation")
                return
            
            elif max_severity == ModerationService.SEVERITY_HIGH:
                # Warn user strongly, don't send message
                emit('warning', {
                    'message': 'Your message violates community standards and was not sent.',
                    'severity': 'high',
                    'rules_violated': len(moderation_check['rules_triggered'])
                })
                logger.warning(f"Message blocked for {nickname}: high severity violation")
                return
            
            elif max_severity in [ModerationService.SEVERITY_MEDIUM, ModerationService.SEVERITY_LOW]:
                # Warn but allow message with flag
                emit('warning', {
                    'message': 'Your message contains content flagged for review',
                    'severity': max_severity,
                    'rules_violated': len(moderation_check['rules_triggered'])
                })
                logger.info(f"Message from {nickname} flagged for {max_severity} violation")
        
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
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'room_id': room_id,
            'moderation_flagged': moderation_check['violated']
        }
        
        emit('message', chat_message, room=room_name)
        logger.debug(f"{nickname} sent message to room {room_id}")
    
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
        success = SessionManager.update_nickname(session_id, new_nickname)
        if not success:
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
    """WebSocket: User disconnected - clean up messages in full privacy mode"""
    try:
        from flask_socketio import request as socketio_request
        
        socket_id = socketio_request.sid
        session_id = _session_socket_mapping.pop(socket_id, None)
        
        if session_id:
            # Clean up messages for this session (full privacy mode)
            persistence_service.on_user_disconnect(session_id)
            logger.info(f"User disconnected: cleaned up session {session_id}")
        else:
            logger.debug("User disconnected (no session mapping)")
    
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")


@socketio.on('connect')
def on_connect():
    """WebSocket: User connected"""
    try:
        logger.debug("User connected to WebSocket")
    except Exception as e:
        logger.error(f"Error in connect: {e}")

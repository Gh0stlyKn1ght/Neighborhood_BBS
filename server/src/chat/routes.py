"""
Chat module - Real-time messaging with WebSocket and privacy support
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, rooms as socketio_rooms
from server import socketio, limiter
from session_manager import SessionManager
from privacy_handler import PrivacyModeHandler
from mode_helper import ModeHelper
from models import ChatRoom, Database
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Initialize privacy handler based on mode
privacy_handler = PrivacyModeHandler(ModeHelper.get_privacy_mode())


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
    """WebSocket: Send a message to room"""
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
            'room_id': room_id
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
    """WebSocket: User disconnected"""
    try:
        logger.debug("User disconnected from WebSocket")
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")


@socketio.on('connect')
def on_connect():
    """WebSocket: User connected"""
    try:
        logger.debug("User connected to WebSocket")
    except Exception as e:
        logger.error(f"Error in connect: {e}")

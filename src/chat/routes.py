"""
Chat module - Real-time messaging for neighborhoods
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import logging
from models import ChatRoom, Message

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/rooms', methods=['GET'])
def get_rooms():
    """Get list of active chat rooms"""
    try:
        rooms = ChatRoom.get_all()
        return jsonify({'rooms': rooms}), 200
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/rooms', methods=['POST'])
def create_room():
    """Create a new chat room"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Room name required'}), 400
        
        room_id = ChatRoom.create(name, description)
        if room_id:
            return jsonify({'status': 'ok', 'room_id': room_id}), 201
        else:
            return jsonify({'error': 'Room already exists'}), 409
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/history/<int:room_id>', methods=['GET'])
def get_chat_history(room_id):
    """Get chat history for a room"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        messages = Message.get_by_room(room_id, limit=limit, offset=offset)
        return jsonify({'messages': messages}), 200
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/send', methods=['POST'])
def send_message():
    """Send a message to a room"""
    try:
        data = request.get_json()
        room_id = data.get('room_id')
        author = data.get('author', 'Anonymous')
        content = data.get('content')
        
        if not all([room_id, content]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(content) > 1000:
            return jsonify({'error': 'Message too long'}), 400
        
        message_id = Message.create(room_id, author, content)
        
        return jsonify({
            'status': 'ok',
            'message_id': message_id,
            'timestamp': datetime.now().isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': str(e)}), 500

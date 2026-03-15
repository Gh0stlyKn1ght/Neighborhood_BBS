"""
Board module - Community notice board for neighborhoods
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from models import Post

logger = logging.getLogger(__name__)

board_bp = Blueprint('board', __name__, url_prefix='/api/board')


@board_bp.route('/posts', methods=['GET'])
def get_posts():
    """Get all board posts"""
    try:
        limit = request.args.get('limit', 30, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        posts = Post.get_all(limit=limit, offset=offset)
        return jsonify({'posts': posts}), 200
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({'error': str(e)}), 500


@board_bp.route('/posts', methods=['POST'])
def create_post():
    """Create a new board post"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        author = data.get('author', 'Anonymous')
        category = data.get('category', 'general')
        
        if not all([title, content]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(title) > 200 or len(content) > 5000:
            return jsonify({'error': 'Content too long'}), 400
        
        post_id = Post.create(title, content, author, category)
        return jsonify({'status': 'ok', 'post_id': post_id}), 201
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({'error': str(e)}), 500


@board_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post"""
    try:
        post = Post.get_by_id(post_id)
        if post:
            return jsonify({'post': post}), 200
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        return jsonify({'error': str(e)}), 500


@board_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post"""
    try:
        Post.delete(post_id)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({'error': str(e)}), 500


@board_bp.route('/posts/<int:post_id>/replies', methods=['POST'])
def add_reply(post_id):
    """Add a reply to a post"""
    try:
        data = request.get_json()
        author = data.get('author', 'Anonymous')
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Reply content required'}), 400
        
        if len(content) > 2000:
            return jsonify({'error': 'Reply too long'}), 400
        
        reply_id = Post.add_reply(post_id, author, content)
        return jsonify({'status': 'ok', 'reply_id': reply_id}), 201
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        return jsonify({'error': str(e)}), 500

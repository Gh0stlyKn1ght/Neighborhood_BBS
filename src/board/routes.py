"""
Board module - Community notice board for neighborhoods
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from models import Post
from server import limiter
from utils.helpers import sanitize_input

# Allowed post categories
ALLOWED_CATEGORIES = {'general', 'announcements', 'events', 'help', 'marketplace', 'lost-and-found'}

logger = logging.getLogger(__name__)

board_bp = Blueprint('board', __name__, url_prefix='/api/board')


@board_bp.route('/posts', methods=['GET'])
def get_posts():
    """Get all board posts"""
    try:
        limit = request.args.get('limit', 30, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Enforce limits
        limit = min(limit, 100)
        offset = max(offset, 0)

        posts = Post.get_all(limit=limit, offset=offset)
        return jsonify({'posts': posts}), 200
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({'error': str(e)}), 500


@board_bp.route('/posts', methods=['POST'])
@limiter.limit("20/minute")
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

        # Sanitize inputs
        title = sanitize_input(title, max_length=200)
        content = sanitize_input(content, max_length=5000)
        author = sanitize_input(author, max_length=100)

        if not title.strip() or not content.strip():
            return jsonify({'error': 'Title and content cannot be empty'}), 400

        # Validate category
        if category not in ALLOWED_CATEGORIES:
            category = 'general'

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
@limiter.limit("30/minute")
def add_reply(post_id):
    """Add a reply to a post"""
    try:
        # Check if post exists
        post = Post.get_by_id(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        data = request.get_json()
        author = data.get('author', 'Anonymous')
        content = data.get('content')

        if not content:
            return jsonify({'error': 'Reply content required'}), 400

        # Sanitize inputs
        author = sanitize_input(author, max_length=100)
        content = sanitize_input(content, max_length=2000)

        if not content.strip():
            return jsonify({'error': 'Reply cannot be empty'}), 400

        reply_id = Post.add_reply(post_id, author, content)
        return jsonify({'status': 'ok', 'reply_id': reply_id}), 201
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        return jsonify({'error': str(e)}), 500

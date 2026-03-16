"""
Bulletins routes - Admin announcements and notices
REST API for creating, reading, updating, deleting bulletins
Broadcasts happen via WebSocket events
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from bulletins.service import BullletinService
from bulletins.websocket_events import (
    broadcast_bulletin_created,
    broadcast_bulletin_updated,
    broadcast_bulletin_deleted,
    broadcast_bulletin_pinned
)
from server import limiter
import logging

logger = logging.getLogger(__name__)

bulletins_bp = Blueprint('bulletins', __name__, url_prefix='/api/bulletins')
bulletin_service = BullletinService()


# ============================================================================
# PUBLIC ROUTES (read-only, accessible to all users)
# ============================================================================

@bulletins_bp.route('', methods=['GET'])
@limiter.limit("30/minute")
def list_bulletins():
    """
    List all active bulletins
    Returns bulletins ordered by: pinned (first), then newest first
    
    Query params:
    - include_expired: bool (default false)
    
    Returns: {bulletins: [{id, title, content, category, is_pinned, ...}]}
    """
    try:
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'
        bulletins = bulletin_service.list_bulletins(active_only=True, include_expired=include_expired)
        
        return jsonify({
            'count': len(bulletins),
            'bulletins': bulletins
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing bulletins: {e}")
        return jsonify({'error': 'Failed to list bulletins'}), 500


@bulletins_bp.route('/<int:bulletin_id>', methods=['GET'])
@limiter.limit("60/minute")
def get_bulletin(bulletin_id):
    """
    Get single bulletin by ID
    
    Returns: {id, title, content, category, is_pinned, created_by, created_at, updated_at, expires_at}
    """
    try:
        bulletin = bulletin_service.get_bulletin(bulletin_id)
        
        if 'error' in bulletin:
            return jsonify(bulletin), bulletin.get('status', 400)
        
        return jsonify(bulletin), 200
    
    except Exception as e:
        logger.error(f"Error getting bulletin {bulletin_id}: {e}")
        return jsonify({'error': 'Failed to get bulletin'}), 500


# ============================================================================
# ADMIN ROUTES (write operations, requires admin authentication)
# ============================================================================

@bulletins_bp.route('', methods=['POST'])
@limiter.limit("10/minute")
def create_bulletin():
    """
    Create new bulletin (admin only)
    
    Body: {
        title: string (required),
        content: string (required),
        category: string ({general, maintenance, important, announcement} default: general),
        is_pinned: bool (default: false),
        expires_at: ISO timestamp (optional, for temporary notices)
    }
    
    Returns: Created bulletin dict with id
    """
    try:
        # TODO: Add admin auth check
        # if not is_admin_authenticated():
        #     return jsonify({'error': 'Admin authentication required'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return jsonify({'error': 'Title and content are required'}), 400
        
        if len(title) < 3 or len(title) > 200:
            return jsonify({'error': 'Title must be 3-200 characters'}), 400
        
        if len(content) < 1 or len(content) > 5000:
            return jsonify({'error': 'Content must be 1-5000 characters'}), 400
        
        # Get optional fields
        category = data.get('category', 'general')
        is_pinned = data.get('is_pinned', False)
        expires_at = data.get('expires_at')
        created_by = data.get('created_by', 'admin')  # TODO: Get from session/auth
        
        # Validate category
        valid_categories = {'general', 'maintenance', 'important', 'announcement'}
        if category not in valid_categories:
            category = 'general'
        
        # Validate expires_at if provided
        if expires_at:
            try:
                expire_dt = datetime.fromisoformat(expires_at)
                if expire_dt <= datetime.utcnow():
                    return jsonify({'error': 'Expiration time must be in the future'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid expires_at format (use ISO format)'}), 400
        
        # Create bulletin
        bulletin = bulletin_service.create_bulletin(
            title=title,
            content=content,
            created_by=created_by,
            category=category,
            is_pinned=is_pinned,
            expires_at=expires_at
        )
        
        if 'error' in bulletin:
            return jsonify(bulletin), bulletin.get('status', 400)
        
        logger.info(f"Bulletin created: {bulletin['id']}")
        
        # Broadcast to all connected clients via WebSocket
        broadcast_bulletin_created(bulletin)
        
        return jsonify(bulletin), 201
    
    except Exception as e:
        logger.error(f"Error creating bulletin: {e}")
        return jsonify({'error': 'Failed to create bulletin'}), 500


@bulletins_bp.route('/<int:bulletin_id>', methods=['PUT'])
@limiter.limit("10/minute")
def update_bulletin(bulletin_id):
    """
    Update bulletin (admin only)
    
    Body: {
        title: string (optional),
        content: string (optional),
        category: string (optional),
        is_pinned: bool (optional),
        expires_at: ISO timestamp (optional),
        is_active: bool (optional)
    }
    
    Returns: Updated bulletin dict
    """
    try:
        # TODO: Add admin auth check
        
        data = request.get_json()
        
        # Validate that at least one field is provided
        update_fields = {k: v for k, v in data.items() 
                        if k in {'title', 'content', 'category', 'is_pinned', 'expires_at', 'is_active'}}
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Validate title if provided
        if 'title' in update_fields:
            title = update_fields['title'].strip()
            if len(title) < 3 or len(title) > 200:
                return jsonify({'error': 'Title must be 3-200 characters'}), 400
        
        # Validate content if provided
        if 'content' in update_fields:
            content = update_fields['content'].strip()
            if len(content) < 1 or len(content) > 5000:
                return jsonify({'error': 'Content must be 1-5000 characters'}), 400
        
        # Validate category if provided
        if 'category' in update_fields:
            valid_categories = {'general', 'maintenance', 'important', 'announcement'}
            if update_fields['category'] not in valid_categories:
                return jsonify({'error': f'Invalid category. Must be one of {valid_categories}'}), 400
        
        # Update bulletin
        bulletin = bulletin_service.update_bulletin(bulletin_id, **update_fields)
        
        if 'error' in bulletin:
            return jsonify(bulletin), bulletin.get('status', 400)
        
        logger.info(f"Bulletin {bulletin_id} updated")
        
        # Broadcast to all connected clients via WebSocket
        broadcast_bulletin_updated(bulletin)
        
        return jsonify(bulletin), 200
    
    except Exception as e:
        logger.error(f"Error updating bulletin {bulletin_id}: {e}")
        return jsonify({'error': 'Failed to update bulletin'}), 500


@bulletins_bp.route('/<int:bulletin_id>', methods=['DELETE'])
@limiter.limit("10/minute")
def delete_bulletin(bulletin_id):
    """
    Delete bulletin (admin only, soft delete - marks as inactive)
    
    Returns: {success: true, message: "Bulletin deleted"}
    """
    try:
        # TODO: Add admin auth check
        
        result = bulletin_service.delete_bulletin(bulletin_id)
        
        if 'error' in result:
            return jsonify(result), result.get('status', 400)
        
        logger.info(f"Bulletin {bulletin_id} deleted")
        
        # Broadcast to all connected clients via WebSocket
        broadcast_bulletin_deleted(bulletin_id)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error deleting bulletin {bulletin_id}: {e}")
        return jsonify({'error': 'Failed to delete bulletin'}), 500


@bulletins_bp.route('/<int:bulletin_id>/pin', methods=['POST'])
@limiter.limit("10/minute")
def pin_bulletin(bulletin_id):
    """
    Pin bulletin to top (admin only)
    
    Returns: Updated bulletin dict
    """
    try:
        # TODO: Add admin auth check
        
        bulletin = bulletin_service.pin_bulletin(bulletin_id)
        
        if 'error' in bulletin:
            return jsonify(bulletin), bulletin.get('status', 400)
        
        # Broadcast to all connected clients via WebSocket
        broadcast_bulletin_pinned(bulletin)
        
        return jsonify(bulletin), 200
    
    except Exception as e:
        logger.error(f"Error pinning bulletin {bulletin_id}: {e}")
        return jsonify({'error': 'Failed to pin bulletin'}), 500


@bulletins_bp.route('/<int:bulletin_id>/unpin', methods=['POST'])
@limiter.limit("10/minute")
def unpin_bulletin(bulletin_id):
    """
    Unpin bulletin from top (admin only)
    
    Returns: Updated bulletin dict
    """
    try:
        # TODO: Add admin auth check
        
        bulletin = bulletin_service.unpin_bulletin(bulletin_id)
        
        if 'error' in bulletin:
            return jsonify(bulletin), bulletin.get('status', 400)
        
        # Broadcast to all connected clients via WebSocket
        broadcast_bulletin_pinned(bulletin)
        
        return jsonify(bulletin), 200
    
    except Exception as e:
        logger.error(f"Error unpinning bulletin {bulletin_id}: {e}")
        return jsonify({'error': 'Failed to unpin bulletin'}), 500

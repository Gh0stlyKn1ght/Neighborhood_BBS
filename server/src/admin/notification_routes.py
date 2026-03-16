"""
Admin Notifications API Routes
REST endpoints for managing admin notifications

Phase 4 Week 14
"""

from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from datetime import datetime
from typing import Tuple, Dict, Any
import logging

from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Import auth decorators and helpers from admin management
from admin_management.decorators import require_admin_token, check_admin_role

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/admin-management/notifications')

# Rate limiter (will be injected if available)
limiter = None


def set_limiter(limiter_instance):
    """Set the rate limiter instance"""
    global limiter
    limiter = limiter_instance


def get_notification_service() -> NotificationService:
    """Get NotificationService instance"""
    if not hasattr(current_app, 'notification_service'):
        current_app.notification_service = NotificationService()
        current_app.notification_service.init_notifications_table()
    return current_app.notification_service


# ============================================================================
# RETRIEVAL ENDPOINTS
# ============================================================================

@notifications_bp.route('', methods=['GET'])
@require_admin_token
def get_notifications():
    """
    Get paginated notifications for authenticated admin
    
    Query Parameters:
        - limit: Number of notifications to return (1-500, default 50)
        - offset: Pagination offset (default 0)
        - unread: If true, only return unread notifications
    
    Returns:
        200: List of notifications with metadata
        400: Invalid parameters
        401: Unauthorized
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        
        # Validation
        if limit < 1 or limit > 500:
            return jsonify({'status': 'error', 'message': 'Limit must be between 1 and 500'}), 400
        if offset < 0:
            return jsonify({'status': 'error', 'message': 'Offset must be non-negative'}), 400
        
        admin_id = request.admin_id  # Set by require_admin_token decorator
        service = get_notification_service()
        
        notifications = service.get_notifications(
            admin_id=admin_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        return jsonify({
            'status': 'ok',
            'data': notifications,
            'limit': limit,
            'offset': offset,
            'count': len(notifications)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch notifications'}), 500


@notifications_bp.route('/unread', methods=['GET'])
@require_admin_token
def get_unread_count():
    """
    Get count of unread notifications for authenticated admin
    
    Returns:
        200: Unread count and total stats
        401: Unauthorized
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        unread_count = service.get_unread_count(admin_id)
        stats = service.get_notification_stats(admin_id)
        
        return jsonify({
            'status': 'ok',
            'data': {
                'unread': unread_count,
                'stats': stats
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get unread count'}), 500


@notifications_bp.route('/<notification_id>', methods=['GET'])
@require_admin_token
def get_notification(notification_id: str):
    """
    Get a specific notification
    
    Path Parameters:
        - notification_id: The notification ID
    
    Returns:
        200: Notification details
        404: Notification not found
        401: Unauthorized (not owner of notification)
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        notification = service.get_notification(notification_id, admin_id)
        
        if not notification:
            return jsonify({'status': 'error', 'message': 'Notification not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'data': notification
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching notification: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch notification'}), 500


@notifications_bp.route('/stats', methods=['GET'])
@require_admin_token
def get_stats():
    """
    Get notification statistics for authenticated admin
    
    Returns:
        200: Notification statistics (total, read, unread, by type)
        401: Unauthorized
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        stats = service.get_notification_stats(admin_id)
        type_summary = service.get_notification_types_summary(admin_id)
        
        return jsonify({
            'status': 'ok',
            'data': {
                'stats': stats,
                'by_type': type_summary
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get statistics'}), 500


# ============================================================================
# MODIFICATION ENDPOINTS
# ============================================================================

@notifications_bp.route('/<notification_id>/read', methods=['POST'])
@require_admin_token
def mark_as_read(notification_id: str):
    """
    Mark a notification as read
    
    Path Parameters:
        - notification_id: The notification ID
    
    Returns:
        200: Successfully marked as read
        404: Notification not found
        401: Unauthorized
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        success = service.mark_as_read(notification_id, admin_id)
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Notification not found or already read'}), 404
        
        return jsonify({
            'status': 'ok',
            'message': 'Notification marked as read'
        }), 200
    
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to mark as read'}), 500


@notifications_bp.route('/read-all', methods=['POST'])
@require_admin_token
def mark_all_as_read():
    """
    Mark all notifications as read for authenticated admin
    
    Returns:
        200: Number of notifications marked as read
        401: Unauthorized
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        count = service.mark_all_as_read(admin_id)
        
        return jsonify({
            'status': 'ok',
            'message': 'All notifications marked as read',
            'count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error marking all as read: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to mark all as read'}), 500


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@require_admin_token
def delete_notification(notification_id: str):
    """
    Delete a notification
    
    Path Parameters:
        - notification_id: The notification ID
    
    Returns:
        200: Notification deleted
        404: Notification not found
        401: Unauthorized
    """
    try:
        admin_id = request.admin_id
        service = get_notification_service()
        
        success = service.delete_notification(notification_id, admin_id)
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Notification not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'message': 'Notification deleted'
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to delete notification'}), 500


@notifications_bp.route('/clear-old', methods=['POST'])
@require_admin_token
@check_admin_role(['super_admin', 'moderator'])
def clear_old_notifications():
    """
    Clear notifications older than specified days
    Only available to super_admin and moderator roles
    
    JSON Body:
        - days: Number of days to keep (default 7)
    
    Returns:
        200: Number of notifications cleared
        400: Invalid parameters
        403: Insufficient permissions
        401: Unauthorized
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        if not isinstance(days, int) or days < 1 or days > 365:
            return jsonify({'status': 'error', 'message': 'Days must be between 1 and 365'}), 400
        
        service = get_notification_service()
        count = service.clear_old_notifications(days)
        
        return jsonify({
            'status': 'ok',
            'message': f'Cleared notifications older than {days} days',
            'count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error clearing old notifications: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to clear notifications'}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@notifications_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check notification service health
    
    Returns:
        200: Service is healthy
        503: Service is unhealthy
    """
    try:
        service = get_notification_service()
        # Try a simple query
        service.get_notification_stats()
        
        return jsonify({
            'status': 'ok',
            'service': 'notifications',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'service': 'notifications',
            'message': 'Service unhealthy'
        }), 503


# ============================================================================
# BULK OPERATIONS (for admins)
# ============================================================================

@notifications_bp.route('/batch-read', methods=['POST'])
@require_admin_token
def batch_mark_read():
    """
    Mark multiple notifications as read in one request
    
    JSON Body:
        - notification_ids: Array of notification IDs
    
    Returns:
        200: Number successfully marked as read
        400: Invalid parameters
        401: Unauthorized
    """
    try:
        data = request.get_json() or {}
        notification_ids = data.get('notification_ids', [])
        
        if not isinstance(notification_ids, list) or not notification_ids:
            return jsonify({'status': 'error', 'message': 'notification_ids must be non-empty array'}), 400
        
        if len(notification_ids) > 100:
            return jsonify({'status': 'error', 'message': 'Cannot mark more than 100 notifications at once'}), 400
        
        admin_id = request.admin_id
        service = get_notification_service()
        
        count = 0
        for notif_id in notification_ids:
            if service.mark_as_read(notif_id, admin_id):
                count += 1
        
        return jsonify({
            'status': 'ok',
            'message': f'Marked {count} notifications as read',
            'count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error in batch mark read: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to process batch operation'}), 500


@notifications_bp.route('/batch-delete', methods=['POST'])
@require_admin_token
def batch_delete():
    """
    Delete multiple notifications in one request
    
    JSON Body:
        - notification_ids: Array of notification IDs
    
    Returns:
        200: Number successfully deleted
        400: Invalid parameters
        401: Unauthorized
    """
    try:
        data = request.get_json() or {}
        notification_ids = data.get('notification_ids', [])
        
        if not isinstance(notification_ids, list) or not notification_ids:
            return jsonify({'status': 'error', 'message': 'notification_ids must be non-empty array'}), 400
        
        if len(notification_ids) > 100:
            return jsonify({'status': 'error', 'message': 'Cannot delete more than 100 notifications at once'}), 400
        
        admin_id = request.admin_id
        service = get_notification_service()
        
        count = 0
        for notif_id in notification_ids:
            if service.delete_notification(notif_id, admin_id):
                count += 1
        
        return jsonify({
            'status': 'ok',
            'message': f'Deleted {count} notifications',
            'count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error in batch delete: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to process batch operation'}), 500

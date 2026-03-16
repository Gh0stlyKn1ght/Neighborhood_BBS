"""
Analytics Routes - PHASE 4 Week 13

REST API endpoints for admin dashboard analytics:
- Admin management statistics (count, activity, roles)
- Moderation statistics (violations, suspensions, device bans)
- Access control statistics (registrations, approvals)
- Session statistics (active sessions, duration, peak times)
- Content statistics (messages, posts, replies)
- Historical data for charts

All endpoints require Bearer token authentication
Previously used privacy-first aggregate metrics (Week 12) at /api/admin/analytics
New: Admin-specific analytics at /api/admin-management/analytics with token auth

Author: AI Assistant
Date: 2026
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from server import limiter
from services.analytics_service import AnalyticsService
from admin.admin_management import require_admin_token

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/admin-management/analytics')


# Initialize analytics service
def get_analytics_service():
    """Get analytics service instance"""
    return AnalyticsService()


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@analytics_bp.route('/dashboard', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_dashboard_summary():
    """
    Get comprehensive dashboard summary with all statistics.
    
    Query parameters (optional):
        - days: Number of days for activity stats (default: 7)
    
    Returns:
    {
        "status": "ok",
        "data": {
            "admins": {...},
            "admin_activity": {...},
            "moderation": {...},
            "access_control": {...},
            "sessions": {...},
            "content": {...},
            "generated_at": "2026-03-16T..."
        }
    }
    """
    try:
        service = get_analytics_service()
        data = service.get_dashboard_summary()
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to generate dashboard summary'
        }), 500


@analytics_bp.route('/admins', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_admin_stats():
    """
    Get admin statistics: count, role distribution, and activity.
    
    Query parameters (optional):
        - days: Activity period in days (default: 7)
    
    Returns:
    {
        "status": "ok",
        "data": {
            "count": {
                "total": int,
                "active": int,
                "inactive": int,
                "by_role": {...}
            },
            "activity": {
                "period_days": int,
                "total_actions": int,
                "by_admin": {...},
                "by_action": {...},
                "top_admins": [...]
            }
        }
    }
    """
    try:
        service = get_analytics_service()
        days = request.args.get('days', 7, type=int)
        
        data = {
            'count': service.get_admin_count(),
            'activity': service.get_admin_activity(days=days)
        }
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get admin statistics'
        }), 500


@analytics_bp.route('/moderation', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_moderation_stats():
    """
    Get moderation statistics: violations, suspensions, device bans.
    
    Query parameters (optional):
        - days: Period in days (default: 7)
    
    Returns:
    {
        "status": "ok",
        "data": {
            "period_days": int,
            "total_violations": int,
            "violations_by_type": {...},
            "resolved": int,
            "unresolved": int,
            "suspensions_active": int,
            "device_bans_active": int,
            "bans_new": int
        }
    }
    """
    try:
        service = get_analytics_service()
        days = request.args.get('days', 7, type=int)
        
        data = service.get_moderation_stats(days=days)
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting moderation stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get moderation statistics'
        }), 500


@analytics_bp.route('/access', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_access_control_stats():
    """
    Get access control statistics: registrations, approvals.
    
    Returns:
    {
        "status": "ok",
        "data": {
            "user_registrations": int,
            "pending_approvals": int,
            "approved_total": int,
            "rejected": int,
            "approval_rate": float,
            "pending_by_days": {...}
        }
    }
    """
    try:
        service = get_analytics_service()
        data = service.get_access_stats()
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting access stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get access control statistics'
        }), 500


@analytics_bp.route('/sessions', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_session_stats():
    """
    Get session statistics: active sessions, session duration, peak times.
    
    Returns:
    {
        "status": "ok",
        "data": {
            "active_sessions": int,
            "total_sessions_24h": int,
            "total_sessions_7d": int,
            "avg_session_duration_minutes": float,
            "most_active_time": "HH:MM"
        }
    }
    """
    try:
        service = get_analytics_service()
        data = service.get_session_stats()
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get session statistics'
        }), 500


@analytics_bp.route('/content', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_content_stats():
    """
    Get content creation statistics: messages, posts, replies.
    
    Query parameters (optional):
        - days: Period in days (default: 7)
    
    Returns:
    {
        "status": "ok",
        "data": {
            "period_days": int,
            "messages": int,
            "posts": int,
            "replies": int,
            "total_content": int,
            "messages_per_day": float,
            "posts_per_day": float
        }
    }
    """
    try:
        service = get_analytics_service()
        days = request.args.get('days', 7, type=int)
        
        data = service.get_content_stats(days=days)
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting content stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get content statistics'
        }), 500


@analytics_bp.route('/history', methods=['GET'])
@require_admin_token
@limiter.limit("30/minute")
def get_historical_data():
    """
    Get historical data for charts.
    
    Query parameters (required):
        - metric: 'messages', 'violations', 'sessions', 'admin_actions'
    
    Query parameters (optional):
        - days: Period in days (default: 30)
    
    Returns:
    {
        "status": "ok",
        "data": {
            "metric": str,
            "period_days": int,
            "data": [
                {"date": "YYYY-MM-DD", "value": int},
                ...
            ]
        }
    }
    """
    try:
        service = get_analytics_service()
        
        metric = request.args.get('metric')
        if not metric:
            return jsonify({
                'status': 'error',
                'error': 'Missing required parameter: metric',
                'allowed_metrics': ['messages', 'violations', 'sessions', 'admin_actions']
            }), 400
        
        if metric not in ['messages', 'violations', 'sessions', 'admin_actions']:
            return jsonify({
                'status': 'error',
                'error': f'Unknown metric: {metric}',
                'allowed_metrics': ['messages', 'violations', 'sessions', 'admin_actions']
            }), 400
        
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'status': 'error',
                'error': 'Days must be between 1 and 365'
            }), 400
        
        data = service.get_historical_data(metric=metric, days=days)
        
        return jsonify({
            'status': 'ok',
            'data': data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to get historical data'
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@analytics_bp.route('/health', methods=['GET'])
@limiter.limit("60/minute")
def analytics_health():
    """Health check for analytics service (no auth required)"""
    try:
        service = get_analytics_service()
        # Try a simple query to ensure database is accessible
        admin_count = service.get_admin_count()
        
        return jsonify({
            'status': 'ok',
            'service': 'analytics'
        }), 200
    
    except Exception as e:
        logger.error(f"Analytics health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Analytics service unavailable'
        }), 500

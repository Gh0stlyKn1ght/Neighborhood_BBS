"""
Analytics Routes - PHASE 4 Week 12

REST API endpoints for dashboard analytics:
- System health metrics
- Community statistics
- Message and filtering analytics
- Trend analysis

All endpoints require X-Admin-Password header
Rate-limited per endpoint

Author: AI Assistant
Date: 2026
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import os

from services.analytics_service import analytics_service
from rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/admin/analytics')


def require_admin_auth(f):
    """Decorator to check admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.headers.get('X-Admin-Password')
        
        if not admin_password:
            return jsonify({'error': 'Missing admin password'}), 401
        
        # Compare with environment variable
        expected_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if admin_password != expected_password:
            return jsonify({'error': 'Invalid admin password'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@analytics_bp.route('/health', methods=['GET'])
@rate_limiter.limit("60 per minute")
@require_admin_auth
def get_system_health():
    """
    Get system health metrics
    
    Returns:
    - Connected users count (real-time)
    - Messages sent today
    - Average message length
    - Top filtered patterns
    - Moderation statistics
    """
    try:
        health = analytics_service.get_system_health()
        
        return jsonify({
            'success': True,
            'health': health
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/dashboard', methods=['GET'])
@rate_limiter.limit("60 per minute")
@require_admin_auth
def get_dashboard():
    """
    Get comprehensive dashboard data
    
    Includes:
    - Current metrics summary
    - Top filtered patterns
    - Hourly message distribution
    - 7-day user trend
    - Moderation statistics
    """
    try:
        dashboard_data = analytics_service.get_dashboard_data()
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/users/connected', methods=['GET'])
@rate_limiter.limit("60 per minute")
@require_admin_auth
def get_connected_users():
    """Get current number of connected users"""
    try:
        count = analytics_service.get_connected_users_count()
        
        return jsonify({
            'success': True,
            'connected_users': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting connected users: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/messages/today', methods=['GET'])
@rate_limiter.limit("60 per minute")
@require_admin_auth
def get_messages_today():
    """Get total messages sent today (aggregate only)"""
    try:
        count = analytics_service.get_messages_today_count()
        avg_length = analytics_service.get_average_message_length()
        
        return jsonify({
            'success': True,
            'messages_today': count,
            'average_length': avg_length
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting messages today: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/messages/distribution', methods=['GET'])
@rate_limiter.limit("30 per minute")
@require_admin_auth
def get_message_distribution():
    """Get message distribution by hour for today"""
    try:
        hourly = analytics_service.get_messages_by_hour_today()
        
        return jsonify({
            'success': True,
            'hourly_distribution': hourly
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting message distribution: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/patterns/top', methods=['GET'])
@rate_limiter.limit("30 per minute")
@require_admin_auth
def get_top_patterns():
    """
    Get most frequently filtered patterns
    
    Query params:
    - limit: Number of patterns to return (default 10, max 50)
    """
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        patterns = analytics_service.get_most_filtered_patterns(limit)
        
        return jsonify({
            'success': True,
            'patterns': patterns,
            'limit': limit
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting top patterns: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/moderation/stats', methods=['GET'])
@rate_limiter.limit("30 per minute")
@require_admin_auth
def get_moderation_stats():
    """
    Get moderation statistics
    
    Returns:
    - Violations today (aggregate)
    - Breakdown by severity
    - Number of users affected (aggregate)
    """
    try:
        stats = analytics_service.get_moderation_stats()
        
        return jsonify({
            'success': True,
            'moderation': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting moderation stats: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/trends/users', methods=['GET'])
@rate_limiter.limit("30 per minute")
@require_admin_auth
def get_user_trends():
    """
    Get active user trend over last N days
    
    Query params:
    - days: Number of days to include (default 7, max 30)
    """
    try:
        days = min(int(request.args.get('days', 7)), 30)
        trend = analytics_service.get_active_users_trend(days)
        
        return jsonify({
            'success': True,
            'trend': trend,
            'period_days': days
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user trends: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/report', methods=['GET'])
@rate_limiter.limit("20 per minute")
@require_admin_auth
def get_analytics_report():
    """
    Generate detailed analytics report
    
    Query params:
    - range: 'today', 'week', or 'month' (default 'today')
    """
    try:
        time_range = request.args.get('range', 'today')
        
        # Validate range
        if time_range not in ['today', 'week', 'month']:
            time_range = 'today'
        
        report = analytics_service.get_analytics_report(time_range)
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/info', methods=['GET'])
@rate_limiter.limit("60 per minute")
@require_admin_auth
def get_analytics_info():
    """Get information about analytics system"""
    return jsonify({
        'success': True,
        'analytics_system': {
            'version': '1.0',
            'purpose': 'Community health metrics (privacy-first)',
            'philosophy': 'Aggregate metrics only - NO individual user tracking',
            'metrics': [
                'connected_users',
                'messages_today',
                'average_message_length',
                'most_filtered_patterns',
                'user_activity_trends',
                'moderation_statistics'
            ],
            'forbidden': [
                'individual_user_tracking',
                'device_ids',
                'personal_user_data',
                'per_user_message_counts',
                'user_identities'
            ],
            'endpoints': [
                'GET /api/admin/analytics/health',
                'GET /api/admin/analytics/dashboard',
                'GET /api/admin/analytics/users/connected',
                'GET /api/admin/analytics/messages/today',
                'GET /api/admin/analytics/messages/distribution',
                'GET /api/admin/analytics/patterns/top',
                'GET /api/admin/analytics/moderation/stats',
                'GET /api/admin/analytics/trends/users',
                'GET /api/admin/analytics/report',
                'GET /api/admin/analytics/info'
            ]
        }
    }), 200

"""
Audit Log Routes - PHASE 4 Week 11

REST API endpoints for admin audit log access:
- List recent audit logs
- Filter by admin, category, or user
- Export for compliance
- View statistics
- Search audit logs

All endpoints require X-Admin-Password header

Author: AI Assistant
Date: 2026
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import logging

from services.audit_log_service import audit_log_service, AuditLogService   
from server import limiter

logger = logging.getLogger(__name__)

# Create blueprint
audit_bp = Blueprint('audit', __name__, url_prefix='/api/admin/audit')


def require_admin_auth(f):
    """Decorator to check admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.headers.get('X-Admin-Password')
        
        if not admin_password:
            return jsonify({'error': 'Missing admin password'}), 401
        
        # Note: In production, hash this and compare with stored hash
        # For now, comparing to environment variable
        import os
        expected_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if admin_password != expected_password:
            return jsonify({'error': 'Invalid admin password'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@audit_bp.route('/logs', methods=['GET'])
@limiter.limit("30 per minute")
@require_admin_auth
def get_audit_logs():
    """
    Get recent admin audit logs
    
    Query params:
    - limit: Number of logs (default 50, max 500)
    - offset: Pagination offset (default 0)
    - category: Filter by action category
    - admin_user: Filter by admin user
    - target_user: Filter by target user
    - status: Filter by status (success, failed, partial)
    """
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        admin_user = request.args.get('admin_user')
        target_user = request.args.get('target_user')
        status_filter = request.args.get('status')
        
        # Start with recent actions
        logs = audit_log_service.get_recent_actions(limit, offset)
        
        # Apply filters
        if logs:
            if category:
                logs = [l for l in logs if l['action_category'] == category]
            if admin_user:
                logs = [l for l in logs if l['admin_user'] == admin_user]
            if target_user:
                logs = [l for l in logs if l['target_user'] == target_user]
            if status_filter:
                logs = [l for l in logs if l['status'] == status_filter]
        
        # Get total count
        total_count = audit_log_service.get_action_count(category)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/logs/search', methods=['GET'])
@limiter.limit("20 per minute")
@require_admin_auth
def search_audit_logs():
    """
    Search audit logs by various criteria
    
    Query params:
    - q: Search query (searches action, target_user, details)
    - category: Action category
    - admin_user: Admin who performed action
    - start_date: ISO format date (YYYY-MM-DD)
    - end_date: ISO format date (YYYY-MM-DD)
    - status: success, failed, partial
    """
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category')
        admin_user = request.args.get('admin_user')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status_filter = request.args.get('status')
        
        filters = {}
        if category:
            filters['category'] = category
        if admin_user:
            filters['admin_user'] = admin_user
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if status_filter:
            filters['status'] = status_filter
        
        # Get filtered logs
        logs = audit_log_service.export_audit_log(filters)
        
        # Search in logs
        if query:
            search_lower = query.lower()
            logs = [
                l for l in logs if
                search_lower in str(l.get('action', '')).lower() or
                search_lower in str(l.get('target_user', '')).lower() or
                search_lower in str(l.get('details', '')).lower() or
                search_lower in str(l.get('notes', '')).lower()
            ]
        
        return jsonify({
            'success': True,
            'results': logs,
            'count': len(logs),
            'query': query
        }), 200
    
    except Exception as e:
        logger.error(f"Error searching audit logs: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/logs/category/<category>', methods=['GET'])
@limiter.limit("30 per minute")
@require_admin_auth
def get_logs_by_category(category):
    """Get audit logs filtered by action category"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        
        # Validate category
        valid_categories = [
            AuditLogService.CATEGORY_USER_BAN,
            AuditLogService.CATEGORY_TIMEOUT,
            AuditLogService.CATEGORY_DEVICE_BAN,
            AuditLogService.CATEGORY_CONTENT,
            AuditLogService.CATEGORY_BULLETIN,
            AuditLogService.CATEGORY_CONFIG,
            AuditLogService.CATEGORY_ADMIN,
            AuditLogService.CATEGORY_ACCESS,
            AuditLogService.CATEGORY_OTHER
        ]
        
        if category not in valid_categories:
            return jsonify({'error': 'Invalid category'}), 400
        
        logs = audit_log_service.get_actions_by_category(category, limit)
        
        return jsonify({
            'success': True,
            'category': category,
            'logs': logs,
            'count': len(logs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting logs by category: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/logs/admin/<admin_user>', methods=['GET'])
@limiter.limit("30 per minute")
@require_admin_auth
def get_logs_by_admin(admin_user):
    """Get audit logs for a specific admin"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        logs = audit_log_service.get_actions_by_admin(admin_user, limit)
        
        return jsonify({
            'success': True,
            'admin_user': admin_user,
            'logs': logs,
            'count': len(logs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting logs by admin: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/logs/user/<target_user>', methods=['GET'])
@limiter.limit("30 per minute")
@require_admin_auth
def get_logs_by_target(target_user):
    """Get audit logs for actions targeting a specific user"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        logs = audit_log_service.get_actions_by_target(target_user, limit)
        
        return jsonify({
            'success': True,
            'target_user': target_user,
            'logs': logs,
            'count': len(logs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting logs by target: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/logs/export', methods=['GET'])
@limiter.limit("5 per minute")
@require_admin_auth
def export_audit_logs():
    """
    Export audit logs for compliance/legal/transparency purposes
    
    Query params (all optional):
    - category: Action category
    - admin_user: Admin user
    - target_user: Target user
    - status: Status filter
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    """
    try:
        filters = {}
        
        # Build filters from query params
        category = request.args.get('category')
        if category:
            filters['category'] = category
        
        admin_user = request.args.get('admin_user')
        if admin_user:
            filters['admin_user'] = admin_user
        
        target_user = request.args.get('target_user')
        if target_user:
            filters['target_user'] = target_user
        
        status_filter = request.args.get('status')
        if status_filter:
            filters['status'] = status_filter
        
        start_date = request.args.get('start_date')
        if start_date:
            filters['start_date'] = start_date
        
        end_date = request.args.get('end_date')
        if end_date:
            filters['end_date'] = end_date
        
        logs = audit_log_service.export_audit_log(filters)
        
        # Create response with JSON data
        response_data = {
            'export_timestamp': datetime.now().isoformat(),
            'filters': filters,
            'total_records': len(logs),
            'records': logs
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
@require_admin_auth
def get_audit_stats():
    """Get audit log statistics and summary"""
    try:
        summary = audit_log_service.get_audit_summary()
        
        return jsonify({
            'success': True,
            'stats': summary
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting audit stats: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/report', methods=['GET'])
@limiter.limit("10 per minute")
@require_admin_auth
def get_audit_report():
    """Get detailed audit report"""
    try:
        admin_user = request.args.get('admin_user')
        
        report = audit_log_service.get_audit_report(admin_user)
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting audit report: {e}")
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/info', methods=['GET'])
@limiter.limit("60 per minute")
@require_admin_auth
def get_audit_info():
    """Get information about audit log system"""
    return jsonify({
        'success': True,
        'audit_log_system': {
            'version': '1.0',
            'purpose': 'Permanent admin action accountability',
            'retention': 'Permanent (never deleted)',
            'categories': [
                'USER_BAN',
                'TIMEOUT',
                'DEVICE_BAN',
                'CONTENT',
                'BULLETIN',
                'CONFIG',
                'ADMIN',
                'ACCESS_CONTROL',
                'OTHER'
            ],
            'endpoints': [
                'GET /api/admin/audit/logs',
                'GET /api/admin/audit/logs/search',
                'GET /api/admin/audit/logs/category/<category>',
                'GET /api/admin/audit/logs/admin/<admin_user>',
                'GET /api/admin/audit/logs/user/<target_user>',
                'GET /api/admin/audit/logs/export',
                'GET /api/admin/audit/stats',
                'GET /api/admin/audit/report'
            ]
        }
    }), 200

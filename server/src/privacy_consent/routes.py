"""
Privacy Consent Routes - PHASE 4 Week 10

REST API endpoints for privacy bulletins and consent management.

Endpoints:
  Public:
    - GET  /api/privacy-consent/bulletin - Get active privacy bulletin
    - POST /api/privacy-consent/acknowledge - Record user consent
    - GET  /api/privacy-consent/has-consented - Check if session consented
    
  Admin (X-Admin-Password required):
    - POST /api/privacy-consent/bulletin - Create/update bulletin
    - GET  /api/privacy-consent/bulletins - Get bulletin history
    - GET  /api/privacy-consent/stats - Get consent statistics
    - POST /api/privacy-consent/cleanup - Cleanup old records
    - GET  /api/privacy-consent/summary - Export consent summary

Author: AI Assistant
Date: 2026
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging

from setup_config import SetupConfig
from services.privacy_consent_service import privacy_consent_service

logger = logging.getLogger(__name__)

# Create blueprint
privacy_consent_bp = Blueprint('privacy_consent', __name__, url_prefix='/api/privacy-consent')

# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def require_admin_password(f):
    """Decorator to require admin password"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.headers.get('X-Admin-Password')
        
        if not admin_password:
            return jsonify({'error': 'Missing admin password'}), 401
        
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Invalid admin password'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


# Public endpoints

@privacy_consent_bp.route('/bulletin', methods=['GET'])
@limiter.limit("60/minute")
def get_privacy_bulletin():
    """Get active privacy bulletin"""
    try:
        bulletin = privacy_consent_service.get_active_bulletin()
        
        if not bulletin:
            return jsonify({
                'success': False,
                'error': 'No active privacy bulletin'
            }), 404
        
        return jsonify({
            'success': True,
            'bulletin': bulletin
        }), 200
    except Exception as e:
        logger.error(f"Error getting bulletin: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/acknowledge', methods=['POST'])
@limiter.limit("10/minute")
def acknowledge_consent():
    """Record user privacy consent acknowledgment"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        session_id = data.get('session_id', '').strip()
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Missing session_id'}), 400
        
        # Get user info
        ip_address = request.remote_addr
        device_info = request.headers.get('User-Agent', '')
        
        # Record consent
        success, message = privacy_consent_service.record_consent(
            session_id=session_id,
            ip_address=ip_address,
            device_info=device_info
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logger.error(f"Error acknowledging consent: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/has-consented', methods=['GET'])
@limiter.limit("30/minute")
def check_consent():
    """Check if session has consented to privacy terms"""
    try:
        session_id = request.args.get('session_id', '').strip()
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Missing session_id'}), 400
        
        has_consented = privacy_consent_service.has_consented(session_id)
        
        return jsonify({
            'success': True,
            'has_consented': has_consented
        }), 200
    except Exception as e:
        logger.error(f"Error checking consent: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Admin endpoints

@privacy_consent_bp.route('/bulletin', methods=['POST'])
@require_admin_password
@limiter.limit("5/minute")
def create_bulletin():
    """Create or update privacy bulletin"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return jsonify({
                'success': False,
                'error': 'Missing title or content'
            }), 400
        
        # Create bulletin
        success, message = privacy_consent_service.create_bulletin(
            title=title,
            content=content,
            created_by='admin'
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logger.error(f"Error creating bulletin: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/bulletins', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_bulletin_history():
    """Get privacy bulletin history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Max 50
        
        bulletins = privacy_consent_service.get_bulletin_history(limit=limit)
        
        return jsonify({
            'success': True,
            'bulletins': bulletins,
            'count': len(bulletins)
        }), 200
    except Exception as e:
        logger.error(f"Error getting bulletin history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/stats', methods=['GET'])
@require_admin_password
@limiter.limit("30/minute")
def get_consent_stats():
    """Get privacy consent statistics"""
    try:
        stats = privacy_consent_service.get_consent_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/summary', methods=['GET'])
@require_admin_password
@limiter.limit("10/minute")
def get_consent_summary():
    """Export consent summary for transparency reports"""
    try:
        summary = privacy_consent_service.export_consent_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
    except Exception as e:
        logger.error(f"Error exporting summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@privacy_consent_bp.route('/cleanup', methods=['POST'])
@require_admin_password
@limiter.limit("5/minute")
def cleanup_old_records():
    """Clean up old consent records"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 90)
        
        if not isinstance(days_old, int) or days_old < 1:
            return jsonify({
                'success': False,
                'error': 'Invalid days_old value'
            }), 400
        
        count = privacy_consent_service.cleanup_old_consents(days_old=days_old)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {count} old consent records',
            'records_deleted': count
        }), 200
    except Exception as e:
        logger.error(f"Error cleaning up records: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

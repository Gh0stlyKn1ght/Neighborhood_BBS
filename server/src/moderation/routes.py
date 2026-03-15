"""
Moderation API Routes - PHASE 2
Admin endpoints for content filtering, violation tracking, and user management
"""

from flask import Blueprint, request, jsonify
from setup_config import SetupConfig
from moderation_service import ModerationService
from server import limiter
import logging

logger = logging.getLogger(__name__)

moderation_bp = Blueprint('moderation', __name__, url_prefix='/api/moderation')


# ============================================================================
# MODERATION RULES
# ============================================================================

@moderation_bp.route('/rules', methods=['GET'])
@limiter.limit("30/minute")
def get_moderation_rules():
    """Get all moderation rules"""
    try:
        from models import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM moderation_rules ORDER BY updated_at DESC')
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'rules': rules,
            'count': len(rules)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        return jsonify({'error': 'Failed to get rules'}), 500


@moderation_bp.route('/rules', methods=['POST'])
@limiter.limit("10/minute")
def add_moderation_rule():
    """
    Add a new moderation rule
    
    Requires admin authentication
    Body: {rule_name, rule_type, pattern, action, severity}
    """
    try:
        # Check admin password (simple auth for MVP)
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            logger.warning(f"Unauthorized moderation rule addition attempt")
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        rule_name = data.get('rule_name', '').strip()
        rule_type = data.get('rule_type', '').strip()
        pattern = data.get('pattern', '').strip()
        action = data.get('action', ModerationService.ACTION_WARN).strip()
        severity = data.get('severity', ModerationService.SEVERITY_MEDIUM).strip()
        
        # Validate
        if not rule_name or not rule_type or not pattern:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if rule_type not in ['keyword', 'pattern', 'ratio']:
            return jsonify({'error': 'Invalid rule_type'}), 400
        
        if action not in ['warn', 'mute', 'suspend', 'ban']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Add rule
        if not ModerationService.add_moderation_rule(rule_name, rule_type, pattern, action, severity, 'admin'):
            return jsonify({'error': 'Failed to add rule'}), 500
        
        logger.info(f"Moderation rule added: {rule_name}")
        
        return jsonify({
            'status': 'ok',
            'message': f'Rule "{rule_name}" created',
            'rule': {
                'rule_name': rule_name,
                'rule_type': rule_type,
                'pattern': pattern,
                'action': action,
                'severity': severity
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding rule: {e}")
        return jsonify({'error': 'Failed to add rule'}), 500


# ============================================================================
# VIOLATION REPORTING
# ============================================================================

@moderation_bp.route('/violations/report', methods=['POST'])
@limiter.limit("30/minute")
def report_violation():
    """
    Report a user violation
    
    Body: {nickname, violation_type, description, evidence}
    """
    try:
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        violation_type = data.get('violation_type', '').strip()
        description = data.get('description', '').strip()
        evidence = data.get('evidence', '').strip() or None
        
        # Validate
        if not nickname or not violation_type or not description:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Report violation
        if not ModerationService.report_violation(nickname, violation_type, description, 'user', evidence):
            return jsonify({'error': 'Failed to report violation'}), 500
        
        return jsonify({
            'status': 'ok',
            'message': f'Violation reported for {nickname}',
            'violation_type': violation_type
        }), 201
    
    except Exception as e:
        logger.error(f"Error reporting violation: {e}")
        return jsonify({'error': 'Failed to report violation'}), 500


@moderation_bp.route('/violations/<nickname>', methods=['GET'])
@limiter.limit("30/minute")
def get_user_violations(nickname):
    """Get all violations for a user"""
    try:
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        violations = ModerationService.get_user_violations(nickname)
        
        return jsonify({
            'status': 'ok',
            'nickname': nickname,
            'violations': violations,
            'count': len(violations),
            'severity_levels': {
                'critical': sum(1 for v in violations if v['severity'] == 'critical'),
                'high': sum(1 for v in violations if v['severity'] == 'high'),
                'medium': sum(1 for v in violations if v['severity'] == 'medium'),
                'low': sum(1 for v in violations if v['severity'] == 'low'),
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        return jsonify({'error': 'Failed to get violations'}), 500


# ============================================================================
# CONTENT CHECKING
# ============================================================================

@moderation_bp.route('/check-message', methods=['POST'])
@limiter.limit("60/minute")
def check_message():
    """
    Check if a message violates moderation rules
    
    Body: {message}
    Returns: {violated: bool, rules_triggered: [...], severity: 'low'/'medium'/'high'/'critical'}
    """
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        result = ModerationService.check_message_content(message)
        
        return jsonify({
            'status': 'ok',
            'violated': result['violated'],
            'rules_triggered': result['rules_triggered'],
            'severity': result['severity'],
            'message_length': len(message)
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking message: {e}")
        return jsonify({'error': 'Failed to check message'}), 500


# ============================================================================
# USER SUSPENSIONS
# ============================================================================

@moderation_bp.route('/suspend', methods=['POST'])
@limiter.limit("10/minute")
def suspend_user():
    """
    Suspend a user (temporary or permanent)
    
    Requires admin authentication
    Body: {nickname, suspension_type, reason, duration_hours}
    """
    try:
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        suspension_type = data.get('suspension_type', 'temporary').strip()
        reason = data.get('reason', 'Policy violation').strip()
        duration_hours = data.get('duration_hours', 24)
        
        # Validate
        if not nickname:
            return jsonify({'error': 'Nickname required'}), 400
        
        if suspension_type not in ['temporary', 'permanent']:
            return jsonify({'error': 'Invalid suspension_type'}), 400
        
        # Suspend user
        if not ModerationService.suspend_user(nickname, suspension_type, reason, 'admin', duration_hours):
            return jsonify({'error': 'Failed to suspend user'}), 500
        
        logger.warning(f"User suspended: {nickname} ({suspension_type})")
        
        return jsonify({
            'status': 'ok',
            'message': f'{nickname} has been suspended',
            'suspension_type': suspension_type,
            'reason': reason
        }), 201
    
    except Exception as e:
        logger.error(f"Error suspending user: {e}")
        return jsonify({'error': 'Failed to suspend user'}), 500


@moderation_bp.route('/unsuspend/<nickname>', methods=['POST'])
@limiter.limit("10/minute")
def unsuspend_user(nickname):
    """
    Remove suspension from user
    
    Requires admin authentication
    """
    try:
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Unsuspend user
        if not ModerationService.unsuspend_user(nickname, 'admin'):
            return jsonify({'error': 'Failed to unsuspend user'}), 500
        
        logger.info(f"User unsuspended: {nickname}")
        
        return jsonify({
            'status': 'ok',
            'message': f'{nickname} has been unsuspended'
        }), 200
    
    except Exception as e:
        logger.error(f"Error unsuspending user: {e}")
        return jsonify({'error': 'Failed to unsuspend user'}), 500


@moderation_bp.route('/suspensions/<nickname>', methods=['GET'])
@limiter.limit("30/minute")
def check_suspension(nickname):
    """Check if user is suspended"""
    try:
        is_suspended = ModerationService.is_user_suspended(nickname)
        
        if is_suspended:
            from models import Database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_suspensions
                WHERE nickname = ? AND is_active = 1
                LIMIT 1
            ''', (nickname,))
            
            suspension = dict(cursor.fetchone()) if cursor.fetchone() else None
            conn.close()
            
            return jsonify({
                'status': 'ok',
                'suspended': True,
                'suspension': suspension
            }), 200
        else:
            return jsonify({
                'status': 'ok',
                'suspended': False
            }), 200
    
    except Exception as e:
        logger.error(f"Error checking suspension: {e}")
        return jsonify({'error': 'Failed to check suspension'}), 500


# ============================================================================
# MODERATION LOGS
# ============================================================================

@moderation_bp.route('/logs', methods=['GET'])
@limiter.limit("30/minute")
def get_moderation_logs():
    """
    Get moderation action logs (admin only)
    
    Query params: limit (default 100), action_type (optional filter)
    """
    try:
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        limit = request.args.get('limit', 100, type=int)
        action_type = request.args.get('action_type', None)
        
        logs = ModerationService.get_moderation_logs(limit, action_type)
        
        return jsonify({
            'status': 'ok',
            'logs': logs,
            'count': len(logs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': 'Failed to get logs'}), 500


@moderation_bp.route('/stats', methods=['GET'])
@limiter.limit("30/minute")
def get_moderation_stats():
    """Get moderation statistics (admin only)"""
    try:
        # Check admin password
        admin_password = request.headers.get('X-Admin-Password')
        if not SetupConfig.verify_admin_password(admin_password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        from models import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) as total FROM violations WHERE resolved = 0')
        unresolved_violations = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM user_suspensions WHERE is_active = 1')
        active_suspensions = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM moderation_logs')
        total_actions = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT severity, COUNT(*) as count FROM violations
            WHERE resolved = 0
            GROUP BY severity
        ''')
        violations_by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'stats': {
                'unresolved_violations': unresolved_violations,
                'active_suspensions': active_suspensions,
                'total_actions': total_actions,
                'violations_by_severity': violations_by_severity
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

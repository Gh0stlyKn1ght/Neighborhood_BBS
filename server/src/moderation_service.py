"""
Moderation Service - PHASE 2
Handles content filtering, violation tracking, and user suspensions
"""

import re
from datetime import datetime, timedelta
from models import Database
from session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class ModerationService:
    """Core moderation system for handling violations and suspensions"""
    
    # Violation severity levels
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    
    # Violation types
    VIOLATION_SPAM = 'spam'
    VIOLATION_HARASSMENT = 'harassment'
    VIOLATION_HATE_SPEECH = 'hate_speech'
    VIOLATION_PROFANITY = 'profanity'
    VIOLATION_IMPERSONATION = 'impersonation'
    VIOLATION_COMMERCIAL = 'commercial_spam'
    VIOLATION_CUSTOM = 'custom'
    
    # Moderation rule types
    RULE_TYPE_KEYWORD = 'keyword'
    RULE_TYPE_PATTERN = 'pattern'
    RULE_TYPE_RATIO = 'ratio'
    
    # Moderation actions
    ACTION_WARN = 'warn'
    ACTION_MUTE = 'mute'
    ACTION_SUSPEND = 'suspend'
    ACTION_BAN = 'ban'
    
    @staticmethod
    def add_moderation_rule(rule_name, rule_type, pattern, action=ACTION_WARN, severity=SEVERITY_MEDIUM, created_by='system'):
        """
        Add a new content filtering rule
        
        Args:
            rule_name: Unique name for this rule
            rule_type: 'keyword', 'pattern', 'ratio'
            pattern: String or regex pattern to match
            action: 'warn', 'mute', 'suspend', 'ban'
            severity: 'low', 'medium', 'high', 'critical'
            created_by: Admin who created this rule
            
        Returns:
            bool: True if successful
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO moderation_rules
                (rule_name, rule_type, pattern, action, severity, created_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule_name, rule_type, pattern, action, severity, created_by, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added moderation rule: {rule_name} ({rule_type})")
            return True
        
        except Exception as e:
            logger.error(f"Error adding moderation rule: {e}")
            return False
    
    @staticmethod
    def check_message_content(message_text):
        """
        Check if message violates any moderation rules
        
        Returns:
            dict: {violated: True/False, rules_triggered: [...], severity: 'low'/'medium'/'high'/'critical'}
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get all enabled rules
            cursor.execute('SELECT * FROM moderation_rules WHERE enabled = 1')
            rules = cursor.fetchall()
            conn.close()
            
            triggered_rules = []
            max_severity = None
            severity_order = {None: 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            
            for rule in rules:
                matches = False
                
                if rule['rule_type'] == ModerationService.RULE_TYPE_KEYWORD:
                    # Simple keyword matching (case-insensitive)
                    if rule['pattern'].lower() in message_text.lower():
                        matches = True
                
                elif rule['rule_type'] == ModerationService.RULE_TYPE_PATTERN:
                    # Regex pattern matching
                    try:
                        if re.search(rule['pattern'], message_text, re.IGNORECASE):
                            matches = True
                    except re.error:
                        logger.warning(f"Invalid regex in rule {rule['rule_name']}: {rule['pattern']}")
                
                elif rule['rule_type'] == ModerationService.RULE_TYPE_RATIO:
                    # Character ratio checks (e.g., caps, numbers, special chars)
                    if rule['pattern'] == 'caps_ratio':
                        caps = sum(1 for c in message_text if c.isupper())
                        if len(message_text) > 0 and caps / len(message_text) > 0.7:
                            matches = True
                
                if matches:
                    triggered_rules.append({
                        'rule_name': rule['rule_name'],
                        'action': rule['action'],
                        'severity': rule['severity']
                    })
                    
                    # Update max severity
                    if severity_order.get(rule['severity'], 0) > severity_order.get(max_severity, 0):
                        max_severity = rule['severity']
            
            return {
                'violated': len(triggered_rules) > 0,
                'rules_triggered': triggered_rules,
                'severity': max_severity or ModerationService.SEVERITY_LOW
            }
        
        except Exception as e:
            logger.error(f"Error checking message content: {e}")
            return {'violated': False, 'rules_triggered': [], 'severity': ModerationService.SEVERITY_LOW}
    
    @staticmethod
    def report_violation(nickname, violation_type, description, reported_by='system', evidence=None):
        """
        Report a user violation
        
        Args:
            nickname: User being reported
            violation_type: Type of violation
            description: Description of violation
            reported_by: Who reported it (admin, system, or user nickname)
            evidence: Optional evidence text/message
            
        Returns:
            bool: True if reported
        """
        try:
            # Determine severity based on violation type
            severity_map = {
                ModerationService.VIOLATION_SPAM: ModerationService.SEVERITY_MEDIUM,
                ModerationService.VIOLATION_HARASSMENT: ModerationService.SEVERITY_HIGH,
                ModerationService.VIOLATION_HATE_SPEECH: ModerationService.SEVERITY_CRITICAL,
                ModerationService.VIOLATION_PROFANITY: ModerationService.SEVERITY_LOW,
                ModerationService.VIOLATION_IMPERSONATION: ModerationService.SEVERITY_HIGH,
                ModerationService.VIOLATION_COMMERCIAL: ModerationService.SEVERITY_MEDIUM,
            }
            
            severity = severity_map.get(violation_type, ModerationService.SEVERITY_MEDIUM)
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO violations
                (nickname, violation_type, severity, description, evidence, reported_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nickname, violation_type, severity, description, evidence, reported_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Violation reported: {nickname} - {violation_type} ({severity})")
            
            # Log moderation action
            ModerationService.log_action(
                action_type='violation_reported',
                target_nickname=nickname,
                action_reason=description,
                taken_by=reported_by,
                action_details={'violation_type': violation_type, 'severity': severity}
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error reporting violation: {e}")
            return False
    
    @staticmethod
    def get_user_violations(nickname, resolved_only=False):
        """Get all violations for a user"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if resolved_only:
                cursor.execute('''
                    SELECT * FROM violations
                    WHERE nickname = ? AND resolved = 1
                    ORDER BY created_at DESC
                ''', (nickname,))
            else:
                cursor.execute('''
                    SELECT * FROM violations
                    WHERE nickname = ?
                    ORDER BY created_at DESC
                ''', (nickname,))
            
            violations = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return violations
        
        except Exception as e:
            logger.error(f"Error getting violations: {e}")
            return []
    
    @staticmethod
    def suspend_user(nickname, suspension_type='temporary', reason='Policy violation', suspended_by='admin', duration_hours=24):
        """
        Suspend a user (temporary or permanent)
        
        Args:
            nickname: User to suspend
            suspension_type: 'temporary' or 'permanent'
            reason: Reason for suspension
            suspended_by: Admin suspending
            duration_hours: Hours until suspension expires (only for temporary)
            
        Returns:
            bool: True if suspended
        """
        try:
            expires_at = None
            if suspension_type == 'temporary':
                expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_suspensions
                (nickname, suspension_type, reason, suspended_by, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (nickname, suspension_type, reason, suspended_by, expires_at))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"User suspended: {nickname} ({suspension_type}) by {suspended_by}")
            
            # Log action
            ModerationService.log_action(
                action_type='user_suspended',
                target_nickname=nickname,
                action_reason=reason,
                taken_by=suspended_by,
                action_details={'suspension_type': suspension_type, 'expires_at': str(expires_at)}
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error suspending user: {e}")
            return False
    
    @staticmethod
    def is_user_suspended(nickname):
        """
        Check if user is currently suspended
        
        Returns:
            bool: True if suspended
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_suspensions
                WHERE nickname = ? AND is_active = 1
                AND (suspension_type = 'permanent' OR expires_at IS NULL OR expires_at > ?)
            ''', (nickname, datetime.now()))
            
            suspension = cursor.fetchone()
            conn.close()
            
            return suspension is not None
        
        except Exception as e:
            logger.error(f"Error checking suspension: {e}")
            return False
    
    @staticmethod
    def unsuspend_user(nickname, unsuspended_by='admin'):
        """Remove suspension from user"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_suspensions
                SET is_active = 0
                WHERE nickname = ?
            ''', (nickname,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User unsuspended: {nickname} by {unsuspended_by}")
            
            ModerationService.log_action(
                action_type='user_unsuspended',
                target_nickname=nickname,
                taken_by=unsuspended_by
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error unsuspending user: {e}")
            return False
    
    @staticmethod
    def log_action(action_type, target_nickname=None, action_reason=None, taken_by='system', action_details=None, result='success'):
        """
        Log a moderation action for audit trail
        
        Args:
            action_type: Type of action taken
            target_nickname: User affected
            action_reason: Why action was taken
            taken_by: Admin/system that took action
            action_details: Additional JSON details
            result: 'success' or 'failed'
        """
        try:
            import json
            details_json = json.dumps(action_details) if action_details else None
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO moderation_logs
                (action_type, target_nickname, action_reason, action_details, taken_by, result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (action_type, target_nickname, action_reason, details_json, taken_by, result))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Moderation log: {action_type} on {target_nickname} by {taken_by}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    @staticmethod
    def get_moderation_logs(limit=100, action_type=None):
        """Get recent moderation logs"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if action_type:
                cursor.execute('''
                    SELECT * FROM moderation_logs
                    WHERE action_type = ?
                    ORDER BY taken_at DESC
                    LIMIT ?
                ''', (action_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM moderation_logs
                    ORDER BY taken_at DESC
                    LIMIT ?
                ''', (limit,))
            
            logs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return logs
        
        except Exception as e:
            logger.error(f"Error getting moderation logs: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_suspensions():
        """
        Clean up expired temporary suspensions
        Run this periodically (e.g., hourly)
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_suspensions
                SET is_active = 0
                WHERE is_active = 1
                AND suspension_type = 'temporary'
                AND expires_at IS NOT NULL
                AND expires_at <= ?
            ''', (datetime.now(),))
            
            updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if updated > 0:
                logger.info(f"Cleaned up {updated} expired suspensions")
            
            return updated
        
        except Exception as e:
            logger.error(f"Error cleaning up suspensions: {e}")
            return 0

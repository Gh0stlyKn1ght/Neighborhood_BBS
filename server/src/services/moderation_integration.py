"""
Moderation Integration Service - Privacy-Aware Content Filtering (PHASE 1 Week 6)
Integrates ModerationService with message persistence while preserving privacy

Key Feature: Violations are tracked WITHOUT identifying users across sessions
- Session-based violation counters (not user-based)
- Auto-muting only for current session
- Violations expire when user disconnects (full privacy mode)
- No persistent user linking
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
from moderation_service import ModerationService

logger = logging.getLogger(__name__)


class ModerationIntegrationService:
    """Privacy-aware moderation integration for message filtering and violation tracking"""
    
    # Session-based violation tracking (key: session_id, value: [violation_count, timestamp])
    _session_violations = defaultdict(lambda: {'count': 0, 'last_violation': None, 'muted_until': None})
    _violation_lock = Lock()
    
    # Configuration
    VIOLATION_THRESHOLD = 5  # Violations before auto-mute
    VIOLATION_WINDOW = 10  # Minutes to track violations in
    MUTE_DURATION = 60  # Minutes to mute after threshold
    
    @staticmethod
    def check_message_for_violations(message_text, session_id, nickname=None):
        """
        Check a message against moderation rules WITHOUT identifying the user
        
        Args:
            message_text: Message to check
            session_id: Session making the request (NOT stored as user ID)
            nickname: Current session nickname (can be changed, not identifying)
            
        Returns:
            dict: {
                'passed': bool,
                'violations': [...],  # Rules triggered
                'severity': 'low'/'medium'/'high'/'critical',
                'action': 'allow'/'warn'/'block',
                'reason': 'string',
                'filtered_message': 'string or None'  # If moderated
            }
        """
        try:
            # Check if session is muted
            muted_status = ModerationIntegrationService._check_session_muted(session_id)
            if muted_status['is_muted']:
                logger.debug(f"Session {session_id} muted until {muted_status['muted_until']}")
                return {
                    'passed': False,
                    'violations': [{'reason': 'session_muted'}],
                    'severity': 'high',
                    'action': 'block',
                    'reason': f"Session muted until {muted_status['muted_until'].strftime('%H:%M:%S')}",
                    'filtered_message': None
                }
            
            # Check message content against moderation rules
            check_result = ModerationService.check_message_content(message_text)
            
            if check_result['violated']:
                # Session has triggered moderation rules
                ModerationIntegrationService._record_session_violation(session_id, check_result)
                
                # Check if violation threshold exceeded
                violation_count = ModerationIntegrationService._get_session_violation_count(session_id)
                
                logger.warning(
                    f"Session {session_id} violation triggered: "
                    f"{len(check_result['rules_triggered'])} rules, "
                    f"total violations: {violation_count}/{ModerationIntegrationService.VIOLATION_THRESHOLD}"
                )
                
                # Determine if we should auto-mute
                if violation_count >= ModerationIntegrationService.VIOLATION_THRESHOLD:
                    ModerationIntegrationService._mute_session(session_id, 'violation_threshold')
                    return {
                        'passed': False,
                        'violations': check_result['rules_triggered'],
                        'severity': check_result['severity'],
                        'action': 'block',
                        'reason': f"Violation threshold exceeded ({violation_count}). Session muted for {ModerationIntegrationService.MUTE_DURATION} minutes.",
                        'filtered_message': None
                    }
                
                # Below threshold - let through but warn
                return {
                    'passed': True,
                    'violations': check_result['rules_triggered'],
                    'severity': check_result['severity'],
                    'action': 'warn',
                    'reason': f"Message flagged ({len(check_result['rules_triggered'])} rules matched). Warnings: {violation_count}/{ModerationIntegrationService.VIOLATION_THRESHOLD}",
                    'filtered_message': message_text
                }
            
            # Message passed all checks
            return {
                'passed': True,
                'violations': [],
                'severity': 'low',
                'action': 'allow',
                'reason': 'Message approved',
                'filtered_message': message_text
            }
        
        except Exception as e:
            logger.error(f"Error checking message violations: {e}")
            # Err on side of allowing message
            return {
                'passed': True,
                'violations': [],
                'severity': 'low',
                'action': 'allow',
                'reason': 'Check error (allowed)',
                'filtered_message': message_text
            }
    
    @staticmethod
    def _record_session_violation(session_id, check_result):
        """Record a violation for a session (not a user)"""
        with ModerationIntegrationService._violation_lock:
            session_data = ModerationIntegrationService._session_violations[session_id]
            
            # Clean up old violations outside window
            if session_data['last_violation']:
                age = datetime.now() - session_data['last_violation']
                if age > timedelta(minutes=ModerationIntegrationService.VIOLATION_WINDOW):
                    session_data['count'] = 0
            
            # Increment violation count
            session_data['count'] += 1
            session_data['last_violation'] = datetime.now()
            
            logger.debug(
                f"Session {session_id} violation recorded: "
                f"count={session_data['count']}, "
                f"rules={len(check_result['rules_triggered'])}"
            )
    
    @staticmethod
    def _get_session_violation_count(session_id):
        """Get current violation count for a session"""
        with ModerationIntegrationService._violation_lock:
            session_data = ModerationIntegrationService._session_violations[session_id]
            
            # Clean up old violations
            if session_data['last_violation']:
                age = datetime.now() - session_data['last_violation']
                if age > timedelta(minutes=ModerationIntegrationService.VIOLATION_WINDOW):
                    session_data['count'] = 0
            
            return session_data['count']
    
    @staticmethod
    def _check_session_muted(session_id):
        """Check if a session is currently muted"""
        with ModerationIntegrationService._violation_lock:
            session_data = ModerationIntegrationService._session_violations[session_id]
            
            if session_data['muted_until'] is None:
                return {'is_muted': False, 'muted_until': None}
            
            if datetime.now() > session_data['muted_until']:
                # Mute period expired
                session_data['muted_until'] = None
                logger.info(f"Session {session_id} mute period expired")
                return {'is_muted': False, 'muted_until': None}
            
            return {'is_muted': True, 'muted_until': session_data['muted_until']}
    
    @staticmethod
    def _mute_session(session_id, reason):
        """Mute a session for violating rules (privacy-aware - no user tracking)"""
        with ModerationIntegrationService._violation_lock:
            muted_until = datetime.now() + timedelta(minutes=ModerationIntegrationService.MUTE_DURATION)
            ModerationIntegrationService._session_violations[session_id]['muted_until'] = muted_until
            
            logger.warning(f"Session {session_id} muted until {muted_until.strftime('%H:%M:%S')} - reason: {reason}")
    
    @staticmethod
    def get_session_status(session_id):
        """Get current moderation status for a session"""
        with ModerationIntegrationService._violation_lock:
            session_data = ModerationIntegrationService._session_violations[session_id]
            
            # Check if muted
            muted_status = ModerationIntegrationService._check_session_muted(session_id)
            
            # Clean up old violations
            violation_count = ModerationIntegrationService._get_session_violation_count(session_id)
            
            return {
                'session_id': session_id,
                'is_muted': muted_status['is_muted'],
                'muted_until': muted_status['muted_until'].isoformat() if muted_status['muted_until'] else None,
                'violations_in_window': violation_count,
                'threshold': ModerationIntegrationService.VIOLATION_THRESHOLD,
                'can_speak': not muted_status['is_muted'],
                'warnings_remaining': max(0, ModerationIntegrationService.VIOLATION_THRESHOLD - violation_count)
            }
    
    @staticmethod
    def unmute_session(session_id, reason='admin_override'):
        """Unmute a session (admin action or explicit override)"""
        try:
            with ModerationIntegrationService._violation_lock:
                ModerationIntegrationService._session_violations[session_id]['muted_until'] = None
                ModerationIntegrationService._session_violations[session_id]['count'] = 0
            
            logger.info(f"Session {session_id} unmuted - reason: {reason}")
            
            # Log action for audit trail (NO user identification)
            ModerationService.log_action(
                action_type='session_unmuted',
                target_nickname=None,  # NOT storing which user/nickname
                action_reason=reason,
                taken_by='system',
                action_details={'session_id': session_id}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error unmuting session: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_sessions(expired_session_ids):
        """
        Clean up mute/violation data for disconnected sessions
        Called when user disconnects to free memory (privacy-aware cleanup)
        
        Args:
            expired_session_ids: List of session IDs that have disconnected
        """
        try:
            with ModerationIntegrationService._violation_lock:
                for session_id in expired_session_ids:
                    if session_id in ModerationIntegrationService._session_violations:
                        del ModerationIntegrationService._session_violations[session_id]
                        logger.debug(f"Cleaned up moderation data for session {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session moderation data: {e}")
    
    @staticmethod
    def get_statistics():
        """Get moderation statistics (privacy-aware aggregates only)"""
        try:
            with ModerationIntegrationService._violation_lock:
                active_sessions = len(ModerationIntegrationService._session_violations)
                muted_sessions = sum(
                    1 for s in ModerationIntegrationService._session_violations.values()
                    if s.get('muted_until') and datetime.now() <= s['muted_until']
                )
                total_violations = sum(
                    s.get('count', 0) for s in ModerationIntegrationService._session_violations.values()
                )
            
            # Get global rule stats
            from models import Database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM moderation_rules WHERE enabled = 1')
            enabled_rules = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM violations')
            total_violations_logged = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM violations WHERE resolved = 0')
            unresolved_violations = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'active_sessions_tracked': active_sessions,
                'muted_sessions': muted_sessions,
                'violations_in_current_window': total_violations,
                'enabled_rules': enabled_rules,
                'total_violations_logged': total_violations_logged,
                'unresolved_violations': unresolved_violations,
                'privacy_mode': 'session-based (no user tracking)'
            }
        
        except Exception as e:
            logger.error(f"Error getting moderation statistics: {e}")
            return {'error': str(e)}


def get_moderation_integration_service():
    """Factory function for singleton access"""
    return ModerationIntegrationService

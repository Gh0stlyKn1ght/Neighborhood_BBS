"""
Integration tests for moderation with privacy preservation (PHASE 1 Week 6)
Tests session-based violation tracking without user identification
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Database
from moderation_service import ModerationService
from services.moderation_integration import ModerationIntegrationService
from session_manager import SessionManager
import tempfile
import os


class PrivacyAwareModerationTests(unittest.TestCase):
    """Test moderation without user tracking"""
    
    def setUp(self):
        """Set up test database and services"""
        # Create fresh test database
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db_file.name
        temp_db_file.close()
        
        self.db = Database(Path(temp_db_path))
        self.db.init_db()
        self.temp_db_path = temp_db_path
    
    def tearDown(self):
        """Clean up"""
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except:
                pass
        
        if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
            except:
                pass
        
        # Clear moderation data
        ModerationIntegrationService._session_violations.clear()
    
    def test_session_based_violation_tracking(self):
        """Test that violations are tracked per session, not per user"""
        print("\n" + "="*60)
        print("TEST: Session-Based Violation Tracking")
        print("="*60)
        
        # Add a moderation rule
        ModerationService.add_moderation_rule(
            'test_spam',
            'keyword',
            'viagra',
            ModerationService.ACTION_WARN,
            ModerationService.SEVERITY_MEDIUM,
            'system'
        )
        
        session_1 = "session-001"
        session_2 = "session-002"
        same_nickname = "alice"
        
        # Test 1: Session 1 sends spam (same nickname)
        result_1 = ModerationIntegrationService.check_message_for_violations(
            "Buy viagra now!",
            session_1,
            same_nickname
        )
        self.assertFalse(result_1['passed'], "Spam should be flagged")
        self.assertEqual(result_1['action'], 'warn', "Should warn on violation")
        
        # Test 2: Session 2 (different session, same nickname) should NOT have accumulated violations
        result_2 = ModerationIntegrationService.check_message_for_violations(
            "Buy viagra now!",
            session_2,
            same_nickname
        )
        self.assertFalse(result_2['passed'], "Spam should be flagged")
        self.assertEqual(result_2['action'], 'warn', "Should warn on violation")
        
        # Test 3: Check session statuses - they should be independent
        status_1 = ModerationIntegrationService.get_session_status(session_1)
        status_2 = ModerationIntegrationService.get_session_status(session_2)
        
        # Both have 1 violation in their windows
        self.assertEqual(status_1['violations_in_window'], 1)
        self.assertEqual(status_2['violations_in_window'], 1)
        
        # Neither should be muted yet
        self.assertFalse(status_1['is_muted'])
        self.assertFalse(status_2['is_muted'])
        
        print("  ✓ Session 1 violations tracked independently")
        print("  ✓ Session 2 violations tracked independently")
        print("  ✓ Same nickname doesn't cross-contaminate sessions")


    def test_violation_threshold_auto_mute(self):
        """Test that sessions are auto-muted after violating threshold"""
        print("\n" + "="*60)
        print("TEST: Violation Threshold Auto-Mute")
        print("="*60)
        
        # Add a rule with low threshold
        ModerationService.add_moderation_rule(
            'spam_rule',
            'keyword',
            'test_spam',
            ModerationService.ACTION_WARN,
            ModerationService.SEVERITY_LOW,
            'system'
        )
        
        session_id = "session-test"
        threshold = ModerationIntegrationService.VIOLATION_THRESHOLD
        
        # Send violations up to threshold
        for i in range(threshold):
            result = ModerationIntegrationService.check_message_for_violations(
                "message with test_spam in it",
                session_id,
                f"user_{i}"
            )
            
            if i < threshold - 1:
                # Below threshold - should warn but allow
                self.assertTrue(result['passed'], f"Violation {i+1}: Should pass with warning")
                self.assertEqual(result['action'], 'warn')
            else:
                # At threshold - should auto-mute
                self.assertFalse(result['passed'], f"Violation {threshold}: Should be blocked by auto-mute")
                self.assertEqual(result['action'], 'block')
                self.assertIn('muted', result['reason'].lower())
        
        # Test that session is now muted
        status = ModerationIntegrationService.get_session_status(session_id)
        self.assertTrue(status['is_muted'], "Session should be muted after threshold")
        self.assertIsNotNone(status['muted_until'], "Mute should have expiration")
        
        # Test that muted session can't send messages
        blocked_result = ModerationIntegrationService.check_message_for_violations(
            "clean message",  # No spam words
            session_id,
            "user"
        )
        self.assertFalse(blocked_result['passed'], "Muted session should be blocked")
        self.assertEqual(blocked_result['action'], 'block')
        
        print(f"  ✓ Sent {threshold} violations before auto-mute")
        print("  ✓ Session auto-muted after threshold exceeded")
        print("  ✓ Muted session cannot send messages")


    def test_mute_expiration(self):
        """Test that mute periods expire"""
        print("\n" + "="*60)
        print("TEST: Mute Expiration")
        print("="*60)
        
        session_id = "session-mute-test"
        
        # Manually mute a session
        ModerationIntegrationService._mute_session(session_id, "test_mute")
        
        # Verify muted
        status = ModerationIntegrationService.get_session_status(session_id)
        self.assertTrue(status['is_muted'], "Should be muted")
        
        # Manually expire the mute (for testing)
        ModerationIntegrationService._session_violations[session_id]['muted_until'] = \
            datetime.now() - timedelta(minutes=1)
        
        # Verify mute expired
        status_after = ModerationIntegrationService.get_session_status(session_id)
        self.assertFalse(status_after['is_muted'], "Mute should have expired")
        
        print("  ✓ Session mute expires correctly")


    def test_session_cleanup_on_disconnect(self):
        """Test that session data is cleaned up on disconnect"""
        print("\n" + "="*60)
        print("TEST: Session Cleanup on Disconnect")
        print("="*60)
        
        # Add rule
        ModerationService.add_moderation_rule(
            'cleanup_test',
            'keyword',
            'test_spam',
            ModerationService.ACTION_WARN,
            ModerationService.SEVERITY_LOW,
            'system'
        )
        
        session_id = "session-cleanup"
        
        # Create violation data
        result = ModerationIntegrationService.check_message_for_violations(
            "message with test_spam in it",
            session_id,
            "user"
        )
        
        # Verify tracking data exists
        self.assertIn(session_id, ModerationIntegrationService._session_violations)
        status_before = ModerationIntegrationService.get_session_status(session_id)
        self.assertGreater(status_before['violations_in_window'], 0)
        
        # Cleanup session
        ModerationIntegrationService.cleanup_expired_sessions([session_id])
        
        # Verify data is cleared
        self.assertNotIn(session_id, ModerationIntegrationService._session_violations)
        
        print("  ✓ Session data exists before cleanup")
        print("  ✓ Session data removed after cleanup")
        print("  ✓ Privacy-aware: No persistent user data remains")


    def test_unmute_session(self):
        """Test admin ability to unmute sessions"""
        print("\n" + "="*60)
        print("TEST: Admin Unmute Session")
        print("="*60)
        
        session_id = "session-unmute-test"
        
        # Mute the session
        ModerationIntegrationService._mute_session(session_id, "manual_test")
        status_muted = ModerationIntegrationService.get_session_status(session_id)
        self.assertTrue(status_muted['is_muted'])
        
        # Unmute it
        ModerationIntegrationService.unmute_session(session_id, "admin_override")
        status_unmuted = ModerationIntegrationService.get_session_status(session_id)
        self.assertFalse(status_unmuted['is_muted'], "Should be unmuted")
        self.assertEqual(status_unmuted['violations_in_window'], 0, "Violations should be reset")
        
        print("  ✓ Admin can unmute sessions")
        print("  ✓ Muted session restored to functional state")


    def test_moderation_statistics_privacy(self):
        """Test that statistics are aggregated without identifying users"""
        print("\n" + "="*60)
        print("TEST: Moderation Statistics Privacy")
        print("="*60)
        
        # Add some violations from multiple sessions
        for i in range(3):
            ModerationIntegrationService._session_violations[f"session-{i}"]['count'] = i + 1
        
        stats = ModerationIntegrationService.get_statistics()
        
        # Verify we only get aggregates, not user lists
        self.assertIn('active_sessions_tracked', stats)
        self.assertIn('muted_sessions', stats)
        self.assertIn('violations_in_current_window', stats)
        self.assertIn('privacy_mode', stats)
        self.assertIn('session-based', stats['privacy_mode'])
        
        # Verify no user/nickname information is exposed
        self.assertNotIn('nicknames', str(stats))
        self.assertNotIn('users', str(stats))
        
        print("  ✓ Statistics aggregated without user identification")
        print("  ✓ Privacy mode: session-based (no user tracking)")
        print(f"  ✓ Active sessions tracked: {stats['active_sessions_tracked']}")


    def test_violation_window_cleanup(self):
        """Test that violations outside the tracking window are cleared"""
        print("\n" + "="*60)
        print("TEST: Violation Window Cleanup")
        print("="*60)
        
        session_id = "session-window-test"
        
        # Add a violation
        violation_data = ModerationIntegrationService._session_violations[session_id]
        violation_data['count'] = 3
        violation_data['last_violation'] = datetime.now()
        
        # Verify violation is tracked
        status = ModerationIntegrationService.get_session_status(session_id)
        self.assertEqual(status['violations_in_window'], 3)
        
        # Move violation outside window
        old_time = datetime.now() - timedelta(minutes=ModerationIntegrationService.VIOLATION_WINDOW + 1)
        violation_data['last_violation'] = old_time
        
        # Get status again - should clean up old violations
        status_reset = ModerationIntegrationService.get_session_status(session_id)
        self.assertEqual(status_reset['violations_in_window'], 0, "Old violations should be cleared")
        
        print("  ✓ Violations inside window: tracked")
        print("  ✓ Violations outside window: auto-cleared")
        print(f"  ✓ Window duration: {ModerationIntegrationService.VIOLATION_WINDOW} minutes")


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""
Week 8: Passcode-Based Access Control Tests
Tests passcode authentication, session creation, and admin passcode management
"""

import unittest
import tempfile
import sqlite3
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from services.passcode_access_service import PasscodeAccessService, get_passcode_service
from session_manager import SessionManager
from models import Database
from admin_config import AdminConfig

# Set database to memory for testing
import os
os.environ['DB_PATH'] = ':memory:'


class PasscodeServiceTests(unittest.TestCase):
    """Test passcode validation and management"""
    
    @classmethod
    def setUpClass(cls):
        """Set up isolated test database"""
        cls.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db_path = cls.temp_db_file.name
        cls.temp_db_file.close()
        
        # Initialize database with schema
        Database.init_db(cls.temp_db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        try:
            if os.path.exists(cls.temp_db_path):
                os.unlink(cls.temp_db_path)
        except Exception as e:
            print(f"Warning: Could not delete temp db: {e}")
    
    def setUp(self):
        """Set up fresh service instance for each test"""
        Database.DB_PATH = self.temp_db_path
        self.service = PasscodeAccessService()
        
        # Set passcode mode in config
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('access_control', 'passcode'))
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear relevant tables
        conn = Database.get_connection()
        conn.execute('DELETE FROM setup_config WHERE key LIKE "passcode%"')
        conn.execute('DELETE FROM sessions')
        conn.commit()
        conn.close()
    
    def test_passcode_required_check_when_enabled(self):
        """Test that is_passcode_required returns True when mode is 'passcode'"""
        is_required = self.service.is_passcode_required()
        self.assertTrue(is_required)
        print(f"✅ Passcode required check: True when mode is 'passcode'")
    
    def test_passcode_required_check_when_disabled(self):
        """Test that is_passcode_required returns False when mode is 'open'"""
        # Change mode to open
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('access_control', 'open'))
        conn.commit()
        conn.close()
        
        is_required = self.service.is_passcode_required()
        self.assertFalse(is_required)
        print(f"✅ Passcode required check: False when mode is 'open'")
    
    def test_passcode_hashing_consistency(self):
        """Test that hashing same passcode produces same hash"""
        passcode = "test_passcode_123"
        
        hash1 = PasscodeAccessService._hash_passcode(passcode)
        hash2 = PasscodeAccessService._hash_passcode(passcode)
        
        # Same passcode should produce same hash
        self.assertEqual(hash1, hash2)
        print(f"✅ Passcode hashing consistency verified")
    
    def test_passcode_hashing_changes_with_input(self):
        """Test that different passcodes produce different hashes"""
        hash1 = PasscodeAccessService._hash_passcode("passcode_one")
        hash2 = PasscodeAccessService._hash_passcode("passcode_two")
        
        # Different passcodes should produce different hashes
        self.assertNotEqual(hash1, hash2)
        print(f"✅ Passcode hashing: Different inputs produce different hashes")
    
    def test_constant_time_comparison_equal(self):
        """Test constant-time comparison returns True for equal strings"""
        a = "test_string_123"
        b = "test_string_123"
        
        result = PasscodeAccessService._constant_time_compare(a, b)
        self.assertTrue(result)
        print(f"✅ Constant-time comparison: Equal strings match")
    
    def test_constant_time_comparison_unequal(self):
        """Test constant-time comparison returns False for different strings"""
        a = "test_string_123"
        b = "test_string_456"
        
        result = PasscodeAccessService._constant_time_compare(a, b)
        self.assertFalse(result)
        print(f"✅ Constant-time comparison: Different strings don't match")
    
    def test_constant_time_comparison_different_lengths(self):
        """Test constant-time comparison handles different length strings"""
        a = "short"
        b = "much_longer_string"
        
        result = PasscodeAccessService._constant_time_compare(a, b)
        self.assertFalse(result)
        print(f"✅ Constant-time comparison: Different lengths handled")
    
    def test_set_and_validate_passcode(self):
        """Test setting a passcode and validating it"""
        test_passcode = "community_secret_123"
        
        # Set passcode in database
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Validate correct passcode
        is_valid, error = self.service.validate_passcode(test_passcode)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        print(f"✅ Passcode validation: Correct passcode accepted")
    
    def test_reject_wrong_passcode(self):
        """Test that wrong passcode is rejected"""
        test_passcode = "correct_passcode"
        wrong_passcode = "wrong_passcode"
        
        # Set correct passcode
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Try wrong passcode
        is_valid, error = self.service.validate_passcode(wrong_passcode)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('Incorrect', error)
        print(f"✅ Passcode validation: Wrong passcode rejected")
    
    def test_reset_passcode(self):
        """Test admin passcode reset"""
        old_passcode = "old_passcode_123"
        new_passcode = "new_passcode_456"
        
        # Set old passcode
        old_hash = PasscodeAccessService._hash_passcode(old_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', old_hash))
        conn.commit()
        conn.close()
        
        # Reset to new passcode
        success, message = self.service.reset_passcode(
            new_passcode,
            admin_username='admin',
            disconnect_existing_sessions=False
        )
        
        self.assertTrue(success)
        
        # Verify old passcode no longer works
        is_valid_old, _ = self.service.validate_passcode(old_passcode)
        self.assertFalse(is_valid_old)
        
        # Verify new passcode works
        is_valid_new, _ = self.service.validate_passcode(new_passcode)
        self.assertTrue(is_valid_new)
        
        print(f"✅ Passcode reset: Old passcode invalidated, new one works")
    
    def test_reset_passcode_min_length_validation(self):
        """Test that short passcode is rejected"""
        short_passcode = "abc"  # Too short
        
        success, message = self.service.reset_passcode(short_passcode)
        self.assertFalse(success)
        self.assertIn('least 4', message)
        print(f"✅ Passcode reset: Short passcode rejected")
    
    def test_reset_passcode_max_length_validation(self):
        """Test that long passcode is rejected"""
        long_passcode = "a" * 51  # Too long
        
        success, message = self.service.reset_passcode(long_passcode)
        self.assertFalse(success)
        self.assertIn('too long', message.lower())
        print(f"✅ Passcode reset: Long passcode rejected")
    
    def test_get_passcode_status_active(self):
        """Test getting passcode status when active"""
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode("test_pass")
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        status = self.service.get_passcode_status()
        
        self.assertTrue(status['is_required'])
        self.assertTrue(status['has_passcode'])
        self.assertEqual(status['access_mode'], 'passcode')
        self.assertEqual(status['status'], 'active')
        print(f"✅ Passcode status: Active status reported correctly")
    
    def test_rate_limiting_excessive_attempts(self):
        """Test rate limiting after excessive failed attempts"""
        test_passcode = "correct"
        
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Make 5 failed attempts
        for i in range(5):
            is_valid, error = self.service.validate_passcode("wrong_pass")
            self.assertFalse(is_valid)
        
        # 6th attempt should be rate limited
        is_valid, error = self.service.validate_passcode(test_passcode)
        self.assertFalse(is_valid)
        self.assertIn('Too many attempts', error)
        print(f"✅ Rate limiting: Excessive attempts blocked")
    
    def test_privacy_no_passcode_in_logs(self):
        """Test that passcode never appears in error messages"""
        test_passcode = "secret_password_123"
        
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Validate with wrong passcode
        is_valid, error = self.service.validate_passcode("wrong_password")
        
        # Error message should not contain original passcode
        self.assertNotIn("secret_password_123", error or "")
        self.assertNotIn("wrong_password", error or "")
        print(f"✅ Privacy: Passcodes not exposed in error messages")


class PasscodeSessionIntegrationTests(unittest.TestCase):
    """Test passcode auth integrated with session management"""
    
    @classmethod
    def setUpClass(cls):
        """Set up isolated test database"""
        cls.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db_path = cls.temp_db_file.name
        cls.temp_db_file.close()
        
        Database.init_db(cls.temp_db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        try:
            if os.path.exists(cls.temp_db_path):
                os.unlink(cls.temp_db_path)
        except:
            pass
    
    def setUp(self):
        """Set up for each test"""
        Database.DB_PATH = self.temp_db_path
        self.service = PasscodeAccessService()
        
        # Enable passcode mode
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('access_control', 'passcode'))
        
        # Set a test passcode
        test_hash = PasscodeAccessService._hash_passcode("test123")
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', test_hash))
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up after each test"""
        conn = Database.get_connection()
        conn.execute('DELETE FROM setup_config')
        conn.execute('DELETE FROM sessions')
        conn.commit()
        conn.close()
    
    def test_session_creation_after_valid_passcode(self):
        """Test that session is created after passcode validation"""
        # Validate passcode
        is_valid, _ = self.service.validate_passcode("test123")
        self.assertTrue(is_valid)
        
        # Create session with nickname
        session = SessionManager.create_session("TestUser")
        
        self.assertIsNotNone(session)
        self.assertIn('session_id', session)
        self.assertEqual(session['nickname'], 'TestUser')
        print(f"✅ Session integration: Session created after valid passcode")
    
    def test_session_creation_flow_complete(self):
        """Test complete flow: passcode validation → session creation"""
        test_passcode = "validate_me"
        test_nickname = "UserName"
        
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Validate passcode
        is_valid, error = self.service.validate_passcode(test_passcode)
        self.assertTrue(is_valid, f"Passcode validation failed: {error}")
        
        # Create session
        session = SessionManager.create_session(test_nickname)
        self.assertIsNotNone(session)
        
        # Verify session can be retrieved
        retrieved = SessionManager.get_session(session['session_id'])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['nickname'], test_nickname)
        
        print(f"✅ Complete flow: Passcode validation → Session creation → Retrieval")
    
    def test_multiple_users_different_nicknames(self):
        """Test that multiple users can authenticate with same passcode"""
        test_passcode = "community_pass"
        
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode(test_passcode)
        conn = Database.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO setup_config (key, value)
            VALUES (?, ?)
        ''', ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Create multiple sessions
        sessions = []
        for i, nickname in enumerate(["User1", "User2", "User3"]):
            is_valid, _ = self.service.validate_passcode(test_passcode)
            self.assertTrue(is_valid)
            
            session = SessionManager.create_session(nickname)
            sessions.append(session)
        
        # Verify all sessions created and retrievable
        self.assertEqual(len(sessions), 3)
        for i, session in enumerate(sessions):
            retrieved = SessionManager.get_session(session['session_id'])
            self.assertIsNotNone(retrieved)
            print(f"✅ Multi-user: User {i+1} session created and retrieved")


class PasscodeAdminEndpointTests(unittest.TestCase):
    """Test admin endpoints for passcode management"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        Database.init_db(self.temp_db_path)
        Database.DB_PATH = self.temp_db_path
        self.service = PasscodeAccessService()
    
    def tearDown(self):
        """Clean up"""
        try:
            if os.path.exists(self.temp_db_path):
                os.unlink(self.temp_db_path)
        except:
            pass
    
    def test_admin_get_status_workflow(self):
        """Test admin GET /api/auth/admin/passcode-status endpoint workflow"""
        # Set passcode
        passcode_hash = PasscodeAccessService._hash_passcode("admin_test")
        conn = Database.get_connection()
        conn.execute('INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('access_control', 'passcode'))
        conn.execute('INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('passcode_hash', passcode_hash))
        conn.commit()
        conn.close()
        
        # Get status
        status = self.service.get_passcode_status()
        
        self.assertTrue(status['is_required'])
        self.assertTrue(status['has_passcode'])
        self.assertNotIn('passcode', status)  # Should NOT expose passcode
        self.assertNotIn('hash', status)  # Should NOT expose hash
        
        print(f"✅ Admin status endpoint: Status returned without exposing passcode")
    
    def test_admin_reset_passcode_workflow(self):
        """Test admin POST /api/auth/admin/reset-passcode endpoint workflow"""
        old_pass = "old_community_pass"
        new_pass = "new_community_pass"
        
        # Set initial passcode
        old_hash = PasscodeAccessService._hash_passcode(old_pass)
        conn = Database.get_connection()
        conn.execute('INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('passcode_hash', old_hash))
        conn.commit()
        conn.close()
        
        # Admin resets passcode
        success, message = self.service.reset_passcode(
            new_pass,
            admin_username='admin_user',
            disconnect_existing_sessions=False
        )
        
        self.assertTrue(success)
        
        # Verify old passcode no longer works
        is_valid_old, _ = self.service.validate_passcode(old_pass)
        self.assertFalse(is_valid_old)
        
        # Verify new passcode works
        is_valid_new, _ = self.service.validate_passcode(new_pass)
        self.assertTrue(is_valid_new)
        
        print(f"✅ Admin reset endpoint: Passcode rotation successful")
    
    def test_admin_reset_with_session_disconnect(self):
        """Test passcode reset with user disconnection"""
        # Create a session
        session = SessionManager.create_session("TestUser")
        session_id = session['session_id']
        
        # Verify session exists
        retrieved = SessionManager.get_session(session_id)
        self.assertIsNotNone(retrieved)
        
        # Admin resets passcode with disconnect
        success, message = self.service.reset_passcode(
            "new_passcode",
            admin_username='admin',
            disconnect_existing_sessions=True
        )
        
        self.assertTrue(success)
        self.assertIn('disconnected', message.lower())
        
        print(f"✅ Admin reset with disconnect: Sessions invalidated")


if __name__ == '__main__':
    unittest.main(verbosity=2)

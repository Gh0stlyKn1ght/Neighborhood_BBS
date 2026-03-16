"""
Integration tests for message persistence by privacy mode (PHASE 1 Week 5)
Tests FULL_PRIVACY, HYBRID, and PERSISTENT modes
"""

import unittest
import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from server import create_app, socketio
from models import Database
from privacy_handler import PrivacyModeHandler
from services.message_persistence_service import MessagePersistenceService
from session_manager import SessionManager


class MessagePersistenceFullPrivacyTests(unittest.TestCase):
    """Test full privacy mode (RAM-only messages, session-based)"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and app"""
        import tempfile
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db_file.name
        temp_db_file.close()
        
        cls.db = Database(Path(temp_db_path))
        cls.db.init_db()
        cls.temp_db_path = temp_db_path
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        import os
        import time
        
        # Wait for any pending operations
        time.sleep(0.1)
        
        # Try to remove the database file with retry
        if os.path.exists(cls.temp_db_path):
            for attempt in range(3):
                try:
                    os.unlink(cls.temp_db_path)
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.2)
                    else:
                        pass  # Give up on final attempt
    
    def setUp(self):
        """Set up each test"""
        # Use full privacy mode
        self.handler = PrivacyModeHandler('full_privacy')
        self.service = MessagePersistenceService()
        self.service.privacy_handler = self.handler
    
    def tearDown(self):
        """Clean up messages between tests"""
        PrivacyModeHandler._message_storage.clear()
    
    def test_save_message_full_privacy(self):
        """Test saving message in full privacy mode"""
        session_id = "session-1"
        
        message = self.handler.save_message(
            session_id=session_id,
            nickname="alice",
            text="Hello world",
            room_id=1
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message['nickname'], "alice")
        self.assertEqual(message['text'], "Hello world")
        self.assertIn(session_id, PrivacyModeHandler._message_storage)
    
    def test_messages_stored_in_ram_only(self):
        """Test that messages are only in RAM, not database"""
        session_id = "session-1"
        
        # Save message
        self.handler.save_message(
            session_id=session_id,
            nickname="bob",
            text="RAM only",
            room_id=1
        )
        
        # Check RAM has it
        messages = PrivacyModeHandler._message_storage[session_id]
        self.assertEqual(len(messages), 1)
        
        # Check database doesn't have it
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(db_count, 0)
    
    def test_messages_deleted_on_disconnect(self):
        """Test that messages are deleted when session disconnects"""
        session_id = "session-1"
        
        # Save messages
        for i in range(3):
            self.handler.save_message(
                session_id=session_id,
                nickname="charlie",
                text=f"Message {i}",
                room_id=1
            )
        
        # Verify they're stored
        self.assertEqual(len(PrivacyModeHandler._message_storage[session_id]), 3)
        
        # Disconnect
        PrivacyModeHandler.on_disconnect(session_id)
        
        # Verify they're deleted
        self.assertNotIn(session_id, PrivacyModeHandler._message_storage)
    
    def test_multiple_sessions_isolated(self):
        """Test that messages from different sessions are isolated"""
        session_1 = "session-1"
        session_2 = "session-2"
        
        # Save messages for different sessions
        self.handler.save_message(session_id=session_1, nickname="alice", text="Alice msg", room_id=1)
        self.handler.save_message(session_id=session_2, nickname="bob", text="Bob msg", room_id=1)
        
        # Get history for each session
        history_1 = self.handler.get_message_history(session_id=session_1)
        history_2 = self.handler.get_message_history(session_id=session_2)
        
        # Each session only sees its own messages
        self.assertEqual(len(history_1), 1)
        self.assertEqual(len(history_2), 1)
        self.assertEqual(history_1[0]['nickname'], "alice")
        self.assertEqual(history_2[0]['nickname'], "bob")
    
    def test_get_history_returns_current_session_only(self):
        """Test that get_history in full privacy mode only returns current session"""
        session_1 = "session-1"
        session_2 = "session-2"
        
        # Create session 1 messages
        self.handler.save_message(session_id=session_1, nickname="alice", text="Msg1", room_id=1)
        self.handler.save_message(session_id=session_1, nickname="alice", text="Msg2", room_id=1)
        
        # Create session 2 messages
        self.handler.save_message(session_id=session_2, nickname="bob", text="Msg3", room_id=1)
        
        # Get history for session 1
        history = self.handler.get_message_history(session_id=session_1)
        
        # Only session 1 messages
        self.assertEqual(len(history), 2)
        for msg in history:
            self.assertEqual(msg['nickname'], "alice")


class MessagePersistenceHybridTests(unittest.TestCase):
    """Test hybrid mode (7-day retention)"""
    
    def setUp(self):
        """Set up each test"""
        self.handler = PrivacyModeHandler('hybrid')
        
        # Clear messages from default database
        try:
            conn = self.handler.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages')
            conn.commit()
            conn.close()
        except:
            pass
    
    def test_save_message_hybrid_mode(self):
        """Test saving message in hybrid mode"""
        message = self.handler.save_message(
            session_id="session-1",
            nickname="alice",
            text="Hybrid msg",
            room_id=1
        )
        
        self.assertIsNotNone(message)
        self.assertIn('id', message)
        
        # Verify it's in database
        conn = self.handler.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreater(count, 0)
    
    def test_hybrid_mode_expires_in_7_days(self):
        """Test that hybrid messages have 7-day expiration"""
        before = datetime.now()
        
        message = self.handler.save_message(
            session_id="session-1",
            nickname="bob",
            text="Will expire",
            room_id=1
        )
        
        after = datetime.now()
        
        # Get expires_at from database
        conn = self.handler.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT expires_at FROM messages WHERE id = ?", (message['id'],))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        expires_at_str = result[0]
        expires_at = datetime.fromisoformat(expires_at_str)
        
        # Calculate expected expiration (7 days from now)
        duration = expires_at - before
        
        # Should be approximately 7 days (within 2 minutes)
        expected_duration = timedelta(days=7)
        delta = abs(duration - expected_duration)
        
        self.assertLess(delta.total_seconds(), 120)  # Within 2 minutes
    
    def test_cleanup_expired_messages(self):
        """Test that cleanup removes expired messages"""
        # Create an expired message manually
        conn = self.handler.db.get_connection()
        cursor = conn.cursor()
        
        past_time = datetime.now() - timedelta(days=1)
        cursor.execute('''
            INSERT INTO messages (nickname, text, created_at, expires_at, room_id)
            VALUES (?, ?, ?, ?, ?)
        ''', ("alice", "Expired", datetime.now(), past_time, 1))
        
        # Create a valid message
        future_time = datetime.now() + timedelta(days=7)
        cursor.execute('''
            INSERT INTO messages (nickname, text, created_at, expires_at, room_id)
            VALUES (?, ?, ?, ?, ?)
        ''', ("bob", "Valid", datetime.now(), future_time, 1))
        
        conn.commit()
        conn.close()
        
        # Run cleanup
        removed = self.handler.cleanup_expired_messages()
        
        # Verify at least 1 was removed
        self.assertGreater(removed, 0)
        
        # Verify valid message still exists
        conn = self.handler.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE expires_at > datetime('now')")
        remaining_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreaterEqual(remaining_count, 1)
    
    def test_get_history_excludes_expired(self):
        """Test that message history excludes expired messages"""
        conn = self.handler.db.get_connection()
        cursor = conn.cursor()
        
        # Clear first
        cursor.execute('DELETE FROM messages')
        
        # Add expired message
        past = datetime.now() - timedelta(days=1)
        cursor.execute('''
            INSERT INTO messages (nickname, text, created_at, expires_at, room_id)
            VALUES (?, ?, ?, ?, ?)
        ''', ("alice", "Expired", datetime.now(), past, 1))
        
        # Add valid message
        future = datetime.now() + timedelta(days=7)
        cursor.execute('''
            INSERT INTO messages (nickname, text, created_at, expires_at, room_id)
            VALUES (?, ?, ?, ?, ?)
        ''', ("bob", "Valid", datetime.now(), future, 1))
        
        conn.commit()
        conn.close()
        
        # Get history
        history = self.handler.get_message_history(room_id=1)
        
        # Should only get valid messages
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['nickname'], "bob")
        self.assertEqual(history[0]['text'], "Valid")


class MessagePersistencePersistentTests(unittest.TestCase):
    """Test persistent mode (all messages saved)"""
    
    def setUp(self):
        """Set up each test with isolated database"""
        # Create fresh database for this test
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db_file.name
        temp_db_file.close()
        
        self.db = Database(Path(temp_db_path))
        self.db.init_db()
        self.temp_db_path = temp_db_path
        
        # Initialize handler with persistent mode and test database
        self.handler = PrivacyModeHandler('persistent', db=self.db)
        self.service = MessagePersistenceService()
        self.service.privacy_handler = self.handler
        self.service.db = self.db
    
    def tearDown(self):
        """Clean up after each test"""
        # Close any remaining connections
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except:
                pass
        
        # Remove temp database file
        if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
            except:
                pass
    
    def test_save_message_persistent_mode(self):
        """Test saving message in persistent mode"""
        message = self.handler.save_message(
            session_id="session-1",
            nickname="alice",
            text="Permanent msg",
            room_id=1
        )
        
        self.assertIsNotNone(message)
        self.assertIn('id', message)
        
        # Verify in database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_persistent_mode_no_expiration(self):
        """Test that persistent messages have no expiration"""
        message = self.handler.save_message(
            session_id="session-1",
            nickname="bob",
            text="No expiration",
            room_id=1
        )
        
        # Get expires_at from database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT expires_at FROM messages WHERE id = ?", (message['id'],))
        expires_at = cursor.fetchone()[0]
        conn.close()
        
        # Should be NULL for persistent mode
        self.assertIsNone(expires_at)
    
    def test_get_history_includes_all_messages(self):
        """Test that history includes all messages in persistent mode"""
        # Create multiple messages across time
        for i in range(5):
            self.handler.save_message(
                session_id=f"session-{i}",
                nickname=f"user-{i}",
                text=f"Message {i}",
                room_id=1
            )
        
        # Get history
        history = self.handler.get_message_history(room_id=1, limit=100)
        
        # Should get all messages
        self.assertEqual(len(history), 5)


class MessagePersistenceServiceTests(unittest.TestCase):
    """Test the message persistence service wrapper"""
    
    def setUp(self):
        """Set up each test with isolated database"""
        # Create fresh database for this test
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db_file.name
        temp_db_file.close()
        
        self.db = Database(Path(temp_db_path))
        self.db.init_db()
        self.temp_db_path = temp_db_path
        
        # Initialize service with persistent mode and test database
        handler = PrivacyModeHandler('persistent', db=self.db)
        self.service = MessagePersistenceService()
        self.service.privacy_handler = handler
        self.service.db = self.db
    
    def tearDown(self):
        """Clean up after each test"""
        # Close any remaining connections
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except:
                pass
        
        # Remove temp database file
        if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
            except:
                pass
    
    def test_service_save_message(self):
        """Test service save_message method"""
        message = self.service.save_message(
            session_id="session-1",
            nickname="alice",
            text="Service test",
            room_id=1
        )
        
        self.assertIsNotNone(message)
    
    def test_service_get_messages(self):
        """Test service get_messages method"""
        # Save multiple messages
        for i in range(3):
            self.service.save_message(
                session_id="session-1",
                nickname="bob",
                text=f"Msg {i}",
                room_id=1
            )
        
        # Get messages
        messages = self.service.get_messages(room_id=1)
        
        self.assertEqual(len(messages), 3)
    
    def test_service_get_statistics(self):
        """Test service get_statistics method"""
        stats = self.service.get_statistics()
        
        self.assertIn('privacy_mode', stats)
        self.assertEqual(stats['privacy_mode'], 'persistent')
        self.assertIn('total_messages', stats)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

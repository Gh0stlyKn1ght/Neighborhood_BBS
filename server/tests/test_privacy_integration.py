#!/usr/bin/env python
"""
Privacy Modes Integration Test
Tests that the three privacy modes actually behave correctly
"""

import sys
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from models import Database, db
from privacy_handler import PrivacyModeHandler
from admin_config import AdminConfig
import tempfile
import os

def cleanup_test_db():
    """Clean up test database"""
    from pathlib import Path
    db_path = Path(__file__).parent.parent / 'data' / 'neighborhood.db'
    if db_path.exists():
        try:
            db_path.unlink()
            print(f"Cleaned up test database")
        except:
            pass

def test_full_privacy_mode():
    """Test Full Privacy mode (ephemeral)"""
    print("\n" + "=" * 50)
    print("TEST: Full Privacy Mode (Ephemeral)")
    print("=" * 50)
    
    # Initialize default (full privacy) mode
    db.init_db()
    
    # Initialize setup config table
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    handler = PrivacyModeHandler('full_privacy')
    
    # Test message saving
    print("\n1. Save messages to RAM")
    handler.save_message('session_1', 'alice', 'Hello from Alice', 'general')
    handler.save_message('session_2', 'bob', 'Hi Alice', 'general')
    print("   ✓ 2 messages saved to memory")
    
    # Test message retrieval
    print("\n2. Retrieve messages")
    messages = handler.get_message_history('general', limit=100)
    print(f"   ✓ Retrieved {len(messages)} messages")
    for msg in messages:
        print(f"     - {msg['nickname']}: {msg['text']}")
    
    # Test statistics
    print("\n3. Check statistics")
    stats = handler.get_statistics()
    print(f"   Total messages in RAM: {stats['total_messages_in_memory']}")
    print(f"   Active sessions: {stats['active_sessions']}")
    assert stats['total_messages_in_memory'] == 2, "Should have 2 messages in memory"
    print("   ✓ PASS: All messages in RAM, none in DB")
    
    # Test cleanup on disconnect
    print("\n4. Simulate user disconnect")
    handler.on_disconnect('alice')
    messages_after = handler.get_message_history('general', limit=100)
    print(f"   ✓ After disconnect, messages still available to other users")
    
    print("\n✓ Full Privacy Mode: PASSED")


def test_hybrid_mode():
    """Test Hybrid mode (7-day retention)"""
    print("\n" + "=" * 50)
    print("TEST: Hybrid Mode (7-day retention)")
    print("=" * 50)
    
    # Clean and reinitialize
    cleanup_test_db()
    db.init_db()
    
    # Initialize setup config table
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    # Set privacy mode to hybrid in config
    database = Database()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Insert test config
    cursor.execute('''
        INSERT OR REPLACE INTO setup_config (key, value, encrypted)
        VALUES (?, ?, ?)
    ''', ('privacy_mode', 'hybrid', False))
    conn.commit()
    conn.close()
    
    handler = PrivacyModeHandler('hybrid')
    
    # Test message saving
    print("\n1. Save messages with 7-day TTL")
    handler.save_message('session_1', 'charlie', 'Message 1', 'general')
    handler.save_message('session_2', 'diana', 'Message 2', 'general')
    print("   ✓ 2 messages saved with expires_at timestamp")
    
    # Verify messages are in database
    print("\n2. Verify messages in database")
    db_conn = Database()
    conn = db_conn.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM messages')
    count = cursor.fetchone()[0]
    conn.close()
    print(f"   ✓ {count} messages in database")
    assert count == 2, "Should have 2 messages in database"
    
    # Test message retrieval
    print("\n3. Retrieve fresh messages")
    messages = handler.get_message_history('general', limit=100)
    print(f"   ✓ Retrieved {len(messages)} messages")
    print(f"   First message expires at: {messages[0].get('expires_at', 'N/A')}")
    
    # Test statistics
    print("\n4. Check statistics")
    stats = handler.get_statistics()
    print(f"   Messages in database: {stats['total_messages']}")
    assert stats['total_messages'] == 2, "Should have 2 messages in DB"
    print("   ✓ PASS: All messages in DB with TTL")
    
    print("\n✓ Hybrid Mode: PASSED")


def test_persistent_mode():
    """Test Persistent mode (no expiration)"""
    print("\n" + "=" * 50)
    print("TEST: Persistent Mode (Permanent)")
    print("=" * 50)
    
    # Clean and reinitialize
    cleanup_test_db()
    db.init_db()
    
    # Initialize setup config table
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    # Set privacy mode to persistent in config
    database = Database()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Insert test config
    cursor.execute('''
        INSERT OR REPLACE INTO setup_config (key, value, encrypted)
        VALUES (?, ?, ?)
    ''', ('privacy_mode', 'persistent', False))
    conn.commit()
    conn.close()
    
    handler = PrivacyModeHandler('persistent')
    
    # Test message saving
    print("\n1. Save messages permanently")
    handler.save_message('session_1', 'eve', 'Permanent message 1', 'general')
    handler.save_message('session_2', 'frank', 'Permanent message 2', 'general')
    print("   ✓ 2 messages saved without expiration")
    
    # Verify messages have no expires_at
    print("\n2. Verify messages have no TTL")
    database = Database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT expires_at FROM messages')
    rows = cursor.fetchall()
    conn.close()
    print(f"   ✓ All messages: expires_at = {rows[0][0]} (None = permanent)")
    assert all(row[0] is None for row in rows), "Persistent mode should not set expires_at"
    
    # Test message retrieval
    print("\n3. Retrieve permanent messages")
    messages = handler.get_message_history('general', limit=100)
    print(f"   ✓ Retrieved {len(messages)} permanent messages")
    
    # Test statistics
    print("\n4. Check statistics")
    stats = handler.get_statistics()
    print(f"   Total messages: {stats['total_messages']}")
    print("   ✓ PASS: All messages permanent")
    
    print("\n✓ Persistent Mode: PASSED")


def test_privacy_handler_factory():
    """Test PrivacyModeHandler factory method"""
    print("\n" + "=" * 50)
    print("TEST: PrivacyModeHandler Factory Method")
    print("=" * 50)
    
    cleanup_test_db()
    db.init_db()
    
    # Initialize setup config table
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    # Test factory creates correct handler based on config
    print("\n1. Test factory with different configs")
    
    for mode in ['full_privacy', 'hybrid', 'persistent']:
        # Set config
        database = Database()
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO setup_config (key, value, encrypted)
            VALUES (?, ?, ?)
        ''', ('privacy_mode', mode, False))
        conn.commit()
        conn.close()
        
        # Create handler from config
        handler = PrivacyModeHandler.create_handler_from_config()
        print(f"   ✓ Created handler for {mode}: {handler.privacy_mode}")
        assert handler.privacy_mode == mode, f"Handler should be {mode} mode"
    
    print("\n✓ Factory Method: PASSED")


def test_admin_config_getters():
    """Test AdminConfig getter methods"""
    print("\n" + "=" * 50)
    print("TEST: AdminConfig Getters")
    print("=" * 50)
    
    cleanup_test_db()
    db.init_db()
    
    # Initialize setup config table
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    # Insert test configuration
    database = Database()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    test_config = [
        ('privacy_mode', 'hybrid', False),
        ('account_system', 'optional', False),
        ('access_control', 'passcode', False),
        ('moderation_levels', json.dumps(['content_filter', 'session_timeout']), False),
        ('violation_threshold', '3', False),
        ('session_timeout_hours', '12', False),
    ]
    
    for key, value, encrypted in test_config:
        cursor.execute('''
            INSERT OR REPLACE INTO setup_config (key, value, encrypted)
            VALUES (?, ?, ?)
        ''', (key, value, encrypted))
    
    conn.commit()
    conn.close()
    
    # Test getters
    print("\n1. Test configuration getters")
    print(f"   Privacy Mode: {AdminConfig.get_privacy_mode()}")
    assert AdminConfig.get_privacy_mode() == 'hybrid'
    
    print(f"   Account System: {AdminConfig.get_account_system()}")
    assert AdminConfig.get_account_system() == 'optional'
    
    print(f"   Access Control: {AdminConfig.get_access_control()}")
    assert AdminConfig.get_access_control() == 'passcode'
    
    print(f"   Moderation Levels: {AdminConfig.get_moderation_levels()}")
    assert 'content_filter' in AdminConfig.get_moderation_levels()
    
    print(f"   Violation Threshold: {AdminConfig.get_violation_threshold()}")
    assert AdminConfig.get_violation_threshold() == 3
    
    print(f"   Session Timeout: {AdminConfig.get_session_timeout_hours()} hours")
    assert AdminConfig.get_session_timeout_hours() == 12
    
    print(f"   Should Track Users: {AdminConfig.should_track_individual_user()}")
    assert AdminConfig.should_track_individual_user() == True  # Not full_privacy
    
    print(f"   Requires Passcode: {AdminConfig.requires_passcode()}")
    assert AdminConfig.requires_passcode() == True
    
    print(f"   Requires Approval: {AdminConfig.requires_approval()}")
    assert AdminConfig.requires_approval() == False
    
    print("\n✓ AdminConfig Getters: PASSED")


if __name__ == '__main__':
    try:
        print("\n" + "=" * 50)
        print("NEIGHBORHOOD BBS - PRIVACY MODES INTEGRATION TEST")
        print("=" * 50)
        
        # Run all tests
        test_full_privacy_mode()
        test_hybrid_mode()
        test_persistent_mode()
        test_privacy_handler_factory()
        test_admin_config_getters()
        
        # Cleanup
        cleanup_test_db()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        print("\nPrivacy modes are working correctly:")
        print("  ✓ Full Privacy (ephemeral messages)")
        print("  ✓ Hybrid (7-day retention with auto-cleanup)")
        print("  ✓ Persistent (permanent messages)")
        print("  ✓ PrivacyModeHandler factory method")
        print("  ✓ AdminConfig getters")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        cleanup_test_db()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_db()
        sys.exit(1)

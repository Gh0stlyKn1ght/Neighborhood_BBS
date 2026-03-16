#!/usr/bin/env python
"""
Test script for User Authentication and Session Management
"""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from models import Database, db
from session_manager import SessionManager
import json

def cleanup_test_db():
    """Clean up test database"""
    db_path = Path(__file__).parent.parent / 'data' / 'neighborhood.db'
    if db_path.exists():
        try:
            db_path.unlink()
            print(f"Cleaned up test database")
        except:
            pass


def test_session_creation():
    """Test creating user sessions"""
    print("\n" + "=" * 50)
    print("TEST: Session Creation")
    print("=" * 50)
    
    # Initialize database
    db.init_db()
    from setup_config import SetupConfig
    SetupConfig.init_setup_table()
    
    # Create session
    print("\n1. Create session for alice")
    session1 = SessionManager.create_session('alice')
    print(f"   ✓ Session created: {session1['session_id']}")
    print(f"   ✓ Nickname: {session1['nickname']}")
    print(f"   ✓ Connected at: {session1['connected_at']}")
    
    # Create another session
    print("\n2. Create session for bob")
    session2 = SessionManager.create_session('bob')
    print(f"   ✓ Session created: {session2['session_id']}")
    
    # Get active sessions
    print("\n3. Check active sessions")
    active = SessionManager.get_active_sessions()
    print(f"   ✓ Active sessions: {active}")
    assert active == 2, "Should have 2 active sessions"
    
    print("\n✓ Session Creation: PASSED")
    return session1, session2


def test_session_retrieval(session1, session2):
    """Test retrieving session data"""
    print("\n" + "=" * 50)
    print("TEST: Session Retrieval")
    print("=" * 50)
    
    # Get session by ID
    print("\n1. Retrieve alice's session")
    retrieved = SessionManager.get_session(session1['session_id'])
    print(f"   ✓ Retrieved: {retrieved['nickname']}")
    assert retrieved['nickname'] == 'alice', "Should retrieve alice's session"
    
    # Get online users
    print("\n2. Get list of online users")
    users = SessionManager.get_connected_users()
    print(f"   ✓ Online users: {users}")
    assert 'alice' in users and 'bob' in users, "Both users should be online"
    
    print("\n✓ Session Retrieval: PASSED")


def test_nickname_change(session1):
    """Test changing nickname mid-session"""
    print("\n" + "=" * 50)
    print("TEST: Nickname Change")
    print("=" * 50)
    
    print("\n1. Change alice's nickname to alice_smith")
    success = SessionManager.update_nickname(session1['session_id'], 'alice_smith')
    print(f"   ✓ Update successful: {success}")
    assert success, "Should successfully update nickname"
    
    # Verify change
    print("\n2. Verify nickname changed")
    updated_session = SessionManager.get_session(session1['session_id'])
    print(f"   ✓ New nickname: {updated_session['nickname']}")
    assert updated_session['nickname'] == 'alice_smith', "Nickname should be updated"
    
    print("\n✓ Nickname Change: PASSED")


def test_activity_tracking(session1):
    """Test activity timestamp updates"""
    print("\n" + "=" * 50)
    print("TEST: Activity Tracking")
    print("=" * 50)
    
    # Update activity
    print("\n1. Update session activity")
    from datetime import datetime
    before = datetime.now().isoformat()
    SessionManager.update_activity(session1['session_id'])
    after = datetime.now().isoformat()
    
    # Get session and check
    session_data = SessionManager.get_session(session1['session_id'])
    last_activity = session_data['last_activity']
    print(f"   ✓ Activity timestamp: {last_activity}")
    assert before <= last_activity <= after or datetime.fromisoformat(last_activity) >= datetime.fromisoformat(before), \
        "Activity should be recent"
    
    print("\n✓ Activity Tracking: PASSED")


def test_session_disconnect(session2):
    """Test closing sessions"""
    print("\n" + "=" * 50)
    print("TEST: Session Disconnect")
    print("=" * 50)
    
    # Close session
    print("\n1. Close bob's session")
    SessionManager.close_session(session2['session_id'])
    print(f"   ✓ Session closed")
    
    # Verify closed
    print("\n2. Verify session is disconnected")
    closed_session = SessionManager.get_session(session2['session_id'])
    print(f"   ✓ Session retrieved: {closed_session}")
    # Session should be None since it's expired now
    
    # Check active count
    active = SessionManager.get_active_sessions()
    print(f"   ✓ Remaining active sessions: {active}")
    assert active == 1, "Should have 1 active session remaining"
    
    print("\n✓ Session Disconnect: PASSED")


def test_session_statistics():
    """Test getting session statistics"""
    print("\n" + "=" * 50)
    print("TEST: Session Statistics")
    print("=" * 50)
    
    # Create a few temporary sessions
    s1 = SessionManager.create_session('test1')
    s2 = SessionManager.create_session('test2')
    s3 = SessionManager.create_session('test3')
    
    print("\n1. Get session statistics")
    stats = SessionManager.get_session_statistics()
    print(f"   ✓ Active sessions: {stats['active_sessions']}")
    print(f"   ✓ Total sessions: {stats['total_sessions']}")
    print(f"   ✓ Sessions today: {stats['sessions_today']}")
    print(f"   ✓ Avg duration: {stats['avg_duration_minutes']} minutes")
    
    assert stats['active_sessions'] > 0, "Should have active sessions"
    assert stats['total_sessions'] >= stats['active_sessions'], "Total should >= active"
    
    print("\n✓ Session Statistics: PASSED")


def test_flask_integration():
    """Test Flask app integration"""
    print("\n" + "=" * 50)
    print("TEST: Flask App Integration")
    print("=" * 50)
    
    try:
        from server import create_app
        
        print("\n1. Create Flask app")
        app = create_app()
        print(f"   ✓ App created successfully")
        
        # Test with client
        print("\n2. Test user endpoints")
        client = app.test_client()
        
        # Test join endpoint
        response = client.post('/api/user/join', 
            json={'nickname': 'testuser'},
            content_type='application/json'
        )
        print(f"   POST /api/user/join: {response.status_code}")
        assert response.status_code == 201, f"Should return 201, got {response.status_code}"
        
        data = response.get_json()
        session_id = data['session_id']
        print(f"   ✓ Session created: {session_id}")
        
        # Test get info endpoint
        response = client.get(f'/api/user/info?session_id={session_id}')
        print(f"   GET /api/user/info: {response.status_code}")
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        
        info = response.get_json()
        print(f"   ✓ Nickname: {info['nickname']}")
        print(f"   ✓ Online count: {info['online_count']}")
        
        # Test online users
        response = client.get('/api/user/online-users')
        print(f"   GET /api/user/online-users: {response.status_code}")
        assert response.status_code == 200
        
        users = response.get_json()
        print(f"   ✓ Online users: {users['count']}")
        
        # Test disconnect
        response = client.post('/api/user/disconnect',
            json={'session_id': session_id},
            content_type='application/json'
        )
        print(f"   POST /api/user/disconnect: {response.status_code}")
        assert response.status_code == 200
        
        print("\n✓ Flask App Integration: PASSED")
    
    except Exception as e:
        print(f"\n✗ Flask Integration FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    try:
        print("\n" + "=" * 50)
        print("NEIGHBORHOOD BBS - USER AUTH TESTS")
        print("=" * 50)
        
        # Cleanup first
        cleanup_test_db()
        
        # Run tests
        session1, session2 = test_session_creation()
        test_session_retrieval(session1, session2)
        test_nickname_change(session1)
        test_activity_tracking(session1)
        test_session_disconnect(session2)
        
        # Cleanup between tests
        cleanup_test_db()
        db.init_db()
        from setup_config import SetupConfig
        SetupConfig.init_setup_table()
        
        test_session_statistics()
        
        # Test Flask integration
        cleanup_test_db()
        test_flask_integration()
        
        # Final cleanup
        cleanup_test_db()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        print("\nUser authentication system is working correctly:")
        print("  ✓ Anonymous sessions created")
        print("  ✓ Nicknames stored and retrievable")
        print("  ✓ Nickname changes work")
        print("  ✓ Activity tracking works")
        print("  ✓ Session disconnection works")
        print("  ✓ Statistics generation works")
        print("  ✓ Flask API endpoints working")
        
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

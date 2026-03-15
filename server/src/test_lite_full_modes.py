#!/usr/bin/env python
"""
Test Lite vs Full mode functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models import db
from setup_config import SetupConfig
from mode_helper import ModeHelper
from server import create_app
from session_manager import SessionManager


def cleanup_test_db():
    """Clean up test database"""
    db_path = Path(__file__).parent.parent / 'data' / 'neighborhood.db'
    if db_path.exists():
        try:
            db_path.unlink()
        except:
            pass


def test_lite_mode():
    """Test Lite mode setup and features"""
    print("\n" + "=" * 60)
    print("TEST: Lite Mode")
    print("=" * 60)
    
    cleanup_test_db()
    db.init_db()
    SetupConfig.init_setup_table()
    
    # Set mode to Lite
    print("\n[1] Setting BBS mode to LITE")
    SetupConfig.save_bbs_mode('lite')
    mode = SetupConfig.get_bbs_mode()
    assert mode == 'lite', f"Expected 'lite', got '{mode}'"
    print(f"  ✓ Mode set to: {mode}")
    
    # Check feature flags
    print("\n[2] Checking Lite mode features")
    flags = ModeHelper.get_feature_flags()
    print(f"  ✓ is_lite: {flags['is_lite']}")
    print(f"  ✓ is_full: {flags['is_full']}")
    print(f"  ✓ allow_admin_panel: {flags['allow_admin_panel']}")
    print(f"  ✓ allow_themes: {flags['allow_themes']}")
    print(f"  ✓ allow_settings: {flags['allow_settings']}")
    print(f"  ✓ privacy_mode: {flags['privacy_mode']}")
    print(f"  ✓ messages_ephemeral: {flags['messages_ephemeral']}")
    
    assert flags['is_lite'] == True
    assert flags['is_full'] == False
    assert flags['allow_admin_panel'] == False
    assert flags['allow_themes'] == False
    assert flags['allow_settings'] == False
    assert flags['privacy_mode'] == 'full_privacy'
    assert flags['messages_ephemeral'] == True
    print("  ✓ All Lite mode feature flags correct")
    
    # Check user blocking is available
    print("\n[3] Testing user blocking in Lite mode")
    SetupConfig.mark_setup_complete()
    app = create_app()
    
    client = app.test_client()
    
    # Join users
    join1 = client.post('/api/user/join', json={'nickname': 'alice'}, content_type='application/json')
    session1_id = join1.get_json()['session_id']
    
    join2 = client.post('/api/user/join', json={'nickname': 'bob'}, content_type='application/json')
    session2_id = join2.get_json()['session_id']
    
    print(f"  ✓ Alice joined: {session1_id[:8]}...")
    print(f"  ✓ Bob joined: {session2_id[:8]}...")
    
    # Alice blocks Bob
    print("\n[4] Alice blocks Bob")
    block_response = client.post('/api/user/block',
        json={
            'session_id': session1_id,
            'blocked_nickname': 'bob',
            'reason': 'Spam'
        },
        content_type='application/json'
    )
    assert block_response.status_code == 200
    block_data = block_response.get_json()
    assert 'bob' in block_data['blocked_users']
    print(f"  ✓ Bob blocked: {block_data['blocked_users']}")
    
    # Check blocked list
    print("\n[5] Getting blocked users list")
    blocked = client.get(f'/api/user/blocked-list?session_id={session1_id}')
    assert blocked.status_code == 200
    blocked_data = blocked.get_json()
    assert 'bob' in blocked_data['blocked_users']
    print(f"  ✓ Blocked users: {blocked_data['blocked_users']}")
    
    # Unblock
    print("\n[6] Alice unblocks Bob")
    unblock_response = client.post('/api/user/unblock',
        json={
            'session_id': session1_id,
            'blocked_nickname': 'bob'
        },
        content_type='application/json'
    )
    assert unblock_response.status_code == 200
    unblock_data = unblock_response.get_json()
    assert 'bob' not in unblock_data['blocked_users']
    print(f"  ✓ Bob unblocked. Blocked list: {unblock_data['blocked_users']}")
    
    print("\n" + "=" * 60)
    print("✓ LITE MODE TEST PASSED")
    print("=" * 60)


def test_full_mode():
    """Test Full mode setup and features"""
    print("\n" + "=" * 60)
    print("TEST: Full Mode")
    print("=" * 60)
    
    cleanup_test_db()
    db.init_db()
    SetupConfig.init_setup_table()
    
    # Set mode to Full
    print("\n[1] Setting BBS mode to FULL")
    SetupConfig.save_bbs_mode('full')
    mode = SetupConfig.get_bbs_mode()
    assert mode == 'full', f"Expected 'full', got '{mode}'"
    print(f"  ✓ Mode set to: {mode}")
    
    # Check feature flags
    print("\n[2] Checking Full mode features")
    flags = ModeHelper.get_feature_flags()
    print(f"  ✓ is_lite: {flags['is_lite']}")
    print(f"  ✓ is_full: {flags['is_full']}")
    print(f"  ✓ allow_admin_panel: {flags['allow_admin_panel']}")
    print(f"  ✓ allow_themes: {flags['allow_themes']}")
    print(f"  ✓ allow_settings: {flags['allow_settings']}")
    print(f"  ✓ allow_room_creation: {flags.get('allow_room_creation', False)}")
    
    assert flags['is_lite'] == False
    assert flags['is_full'] == True
    assert flags['allow_admin_panel'] == True
    assert flags['allow_themes'] == True
    assert flags['allow_settings'] == True
    print("  ✓ All Full mode feature flags correct")
    
    # Test session blocking also works in Full mode
    print("\n[3] Testing user blocking in Full mode")
    SetupConfig.mark_setup_complete()
    app = create_app()
    
    client = app.test_client()
    
    join1 = client.post('/api/user/join', json={'nickname': 'charlie'}, content_type='application/json')
    session1_id = join1.get_json()['session_id']
    print(f"  ✓ Charlie joined: {session1_id[:8]}...")
    
    # Block someone
    block_response = client.post('/api/user/block',
        json={
            'session_id': session1_id,
            'blocked_nickname': 'troll'
        },
        content_type='application/json'
    )
    assert block_response.status_code == 200
    print("  ✓ User blocking works in Full mode too")
    
    print("\n" + "=" * 60)
    print("✓ FULL MODE TEST PASSED")
    print("=" * 60)


def test_mode_persistence():
    """Test that mode persists in setup config"""
    print("\n" + "=" * 60)
    print("TEST: Mode Persistence")
    print("=" * 60)
    
    cleanup_test_db()
    db.init_db()
    SetupConfig.init_setup_table()
    
    # Save Lite mode
    print("\n[1] Saving Lite mode")
    SetupConfig.save_bbs_mode('lite')
    
    # Retrieve it
    print("[2] Retrieving mode")
    mode = SetupConfig.get_bbs_mode()
    assert mode == 'lite'
    print(f"  ✓ Mode persists: {mode}")
    
    # Change to Full
    print("\n[3] Changing to Full mode")
    SetupConfig.save_bbs_mode('full')
    mode = SetupConfig.get_bbs_mode()
    assert mode == 'full'
    print(f"  ✓ Mode changed: {mode}")
    
    # Verify default is Full
    print("\n[4] Testing default mode")
    cleanup_test_db()
    db.init_db()
    SetupConfig.init_setup_table()
    mode = SetupConfig.get_bbs_mode()
    assert mode == 'full'
    print(f"  ✓ Default mode is: {mode}")
    
    print("\n" + "=" * 60)
    print("✓ MODE PERSISTENCE TEST PASSED")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_lite_mode()
        cleanup_test_db()
        test_full_mode()
        cleanup_test_db()
        test_mode_persistence()
        cleanup_test_db()
        
        print("\n" + "=" * 60)
        print("✓ ALL LITE/FULL MODE TESTS PASSED")
        print("=" * 60)
        print("\nLite/Full mode implementation verified:")
        print("  ✓ Mode selection and storage working")
        print("  ✓ Feature flags correct for each mode")
        print("  ✓ User blocking works in both modes")
        print("  ✓ Lite mode forces full_privacy (ephemeral messages)")
        print("  ✓ Mode persistence across sessions")
        
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

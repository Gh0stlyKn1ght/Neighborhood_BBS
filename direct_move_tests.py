#!/usr/bin/env python3
"""
Move test files from server/src to server/tests and verify
This bypasses shell and pytest auto-discovery
"""
import shutil
import sys
from pathlib import Path

def main():
    src_dir = Path('server/src')
    tests_dir = Path('server/tests')
    
    test_files = [
        'test_access_control_phase3.py',
        'test_admin_api_endpoints_phase4w11.py',
        'test_admin_auth_week9.py',
        'test_admin_user_management_phase4w10.py',
        'test_analytics_phase4w13.py',
        'test_analytics_phase4_w12.py',
        'test_approval_week9.py',
        'test_audit_log_phase4_w11.py',
        'test_bulletins_week4.py',
        'test_device_banning_week7.py',
        'test_lite_full_modes.py',
        'test_message_persistence_week5.py',
        'test_moderation_phase2.py',
        'test_moderation_week6.py',
        'test_notifications_phase4w14.py',
        'test_passcode_week8.py',
        'test_privacy_api.py',
        'test_privacy_consent_phase4_w10.py',
        'test_privacy_integration.py',
        'test_user_auth.py',
        'test_week3_integration.py',
    ]
    
    print("=" * 70)
    print("MOVING TEST FILES FROM server/src TO server/tests")
    print("=" * 70)
    
    moved = []
    failed = []
    
    for test_file in test_files:
        src_file = src_dir / test_file
        dst_file = tests_dir / test_file
        
        if not src_file.exists():
            failed.append(f"NOT FOUND: {test_file}")
            continue
        
        try:
            # Copy file first
            shutil.copy2(src_file, dst_file)
            
            # Verify destination exists
            if not dst_file.exists():
                failed.append(f"COPY FAILED: {test_file}")
                continue
            
            # Remove source
            src_file.unlink()
            
            # Verify source is gone
            if src_file.exists():
                failed.append(f"DELETE FAILED: {test_file}")
                continue
            
            moved.append(test_file)
            print(f"[OK] {test_file}")
        except Exception as e:
            failed.append(f"ERROR {test_file}: {e}")
            print(f"[FAIL] {test_file}: {e}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Verify final state
    remaining_in_src = list(src_dir.glob('test_*.py'))
    in_tests = sorted([f.name for f in tests_dir.glob('test_*.py')])
    
    print(f"\n[OK] Moved successfully: {len(moved)}")
    print(f"[FAIL] Failed: {len(failed)}")
    print(f"\nTest files in server/tests/: {len(in_tests)}")
    
    if in_tests:
        for f in in_tests[:5]:
            print(f"  - {f}")
        if len(in_tests) > 5:
            print(f"  ... and {len(in_tests) - 5} more")
    
    print(f"\nRemaining in server/src/: {len(remaining_in_src)}")
    if remaining_in_src:
        for f in remaining_in_src[:5]:
            print(f"  - {f.name}")
    
    if failed:
        print(f"\nFailed operations:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] ALL TEST FILES SUCCESSFULLY MOVED\n")
        sys.exit(0)

if __name__ == '__main__':
    main()

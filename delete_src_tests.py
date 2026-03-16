#!/usr/bin/env python3
"""
Delete all test_*.py files from server/src/ 
(since they should be in server/tests/ instead)
"""
import os
from pathlib import Path

src_dir = Path('server/src')

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

print("Removing test files from server/src/...")
for test_file in test_files:
    file_path = src_dir / test_file
    if file_path.exists():
        os.remove(file_path)
        print(f"  Deleted {test_file}")
    else:
        print(f"  Not found: {test_file}")

print("\nDone! Test files removed from server/src/")

# Verify
remaining = list(src_dir.glob('test_*.py'))
if remaining:
    print(f"\nWarning: {len(remaining)} test files still remain:")
    for f in remaining:
        print(f"  - {f.name}")
else:
    print("\nVerification: No test files remain in server/src/")

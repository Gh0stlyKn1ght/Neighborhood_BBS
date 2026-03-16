#!/usr/bin/env python3
"""Move test files from server/src to server/tests"""
import os
import shutil
from pathlib import Path

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

print(f"Moving {len(test_files)} test files...")
for test_file in test_files:
    src_file = src_dir / test_file
    dst_file = tests_dir / test_file
    
    if src_file.exists():
        print(f"Moving {test_file}...")
        shutil.move(str(src_file), str(dst_file))
    else:
        print(f"Not found: {test_file}")

print("Done!")

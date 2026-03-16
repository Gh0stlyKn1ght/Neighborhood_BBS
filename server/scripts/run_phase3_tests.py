#!/usr/bin/env python3
"""
Phase 3 Complete Test Suite Runner
Validates all moderation, device banning, passcode, approval, and admin auth functionality
"""

import subprocess
import sys
import os
from pathlib import Path

# Test files for Phase 3
PHASE3_TESTS = [
    'test_moderation_week6.py',
    'test_device_banning_week7.py',
    'test_passcode_week8.py',
    'test_approval_week9.py',
    'test_admin_auth_week9.py',
]

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print colored header"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_section(text):
    """Print section header"""
    print(f"{BOLD}{YELLOW}{text}{RESET}")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def run_test(test_file, src_dir):
    """Run a single test file and return result"""
    test_path = src_dir / test_file
    
    if not test_path.exists():
        print_error(f"Test file not found: {test_file}")
        return False, 0, 0
    
    print_section(f"\nRunning {test_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(test_path), '-v', '--tb=short'],
            cwd=str(src_dir.parent),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse output for pass/fail counts
        output = result.stdout + result.stderr
        
        # Extract test counts from pytest output
        import re
        match = re.search(r'(\d+) passed', output)
        passed = int(match.group(1)) if match else 0
        
        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0
        
        if result.returncode == 0:
            print_success(f"{test_file}: {passed} tests passed")
            return True, passed, failed
        else:
            print_error(f"{test_file}: {failed} tests failed")
            print("\nTest output:")
            print(output[-1000:])  # Last 1000 chars
            return False, passed, failed
    
    except subprocess.TimeoutExpired:
        print_error(f"{test_file}: Test timeout (>60s)")
        return False, 0, 0
    except Exception as e:
        print_error(f"{test_file}: {str(e)}")
        return False, 0, 0


def main():
    """Run all Phase 3 tests"""
    print_header("PHASE 3 COMPLETE TEST VALIDATION")
    
    src_dir = Path(__file__).parent.parent / 'src'
    
    if not src_dir.exists():
        print_error(f"Source directory not found: {src_dir}")
        sys.exit(1)
    
    print("Phase 3 includes:")
    print_section("  Week 6: Moderation System (session-based violation tracking)")
    print_section("  Week 7: Device Banning (MAC hashing, escalation)")
    print_section("  Week 8: Passcode Access (PBKDF2, rate limiting)")
    print_section("  Week 9: Approval Access (manual admin approval)")
    print_section("  Week 9 Auth: Admin authentication (X-Admin-Password header)")
    
    # Run all tests
    results = []
    total_passed = 0
    total_failed = 0
    
    for test_file in PHASE3_TESTS:
        success, passed, failed = run_test(test_file, src_dir)
        results.append((test_file, success, passed, failed))
        total_passed += passed
        total_failed += failed
    
    # Print summary
    print_header("TEST SUMMARY")
    
    print(f"{BOLD}Individual Test Files:{RESET}")
    for test_file, success, passed, failed in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {test_file:40} {status:10} ({passed} passed, {failed} failed)")
    
    print(f"\n{BOLD}Totals:{RESET}")
    print(f"  Total Tests: {total_passed + total_failed}")
    print(f"  {GREEN}Passed: {total_passed}{RESET}")
    if total_failed > 0:
        print(f"  {RED}Failed: {total_failed}{RESET}")
    
    # Overall status
    all_passed = all(success for _, success, _, _ in results)
    
    print(f"\n{BOLD}Overall Status:{RESET}")
    if all_passed and total_failed == 0:
        print_success("ALL PHASE 3 TESTS PASSED!")
        print(f"\n{GREEN}{BOLD}Phase 3 is production-ready ✓{RESET}\n")
        return 0
    else:
        print_error("SOME TESTS FAILED - Review output above")
        print(f"\n{RED}{BOLD}Phase 3 validation incomplete ✗{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

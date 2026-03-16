#!/usr/bin/env python3
"""
Move all test_*.py files from server/src/ to server/tests/
"""
import shutil
from pathlib import Path

src_dir = Path('server/src')
tests_dir = Path('server/tests')

# Find all test_*.py files
test_files = sorted(src_dir.glob('test_*.py'))

print(f"\n{'='*60}")
print(f"Moving {len(test_files)} test files from server/src/ to server/tests/")
print(f"{'='*60}\n")

failed_moves = []
successful_moves = []

for test_file in test_files:
    dest_file = tests_dir / test_file.name
    try:
        print(f"Moving: {test_file.name}")
        shutil.copy2(test_file, dest_file)
        # Verify the file was copied
        if dest_file.exists():
            test_file.unlink()
            print(f"  ✓ Moved successfully\n")
            successful_moves.append(test_file.name)
        else:
            print(f"  ✗ Copy failed - destination doesn't exist\n")
            failed_moves.append(test_file.name)
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        failed_moves.append(test_file.name)

# Verify by listing both directories
print(f"\n{'='*60}")
print("VERIFICATION")
print(f"{'='*60}\n")

remaining_in_src = list(src_dir.glob('test_*.py'))
in_tests = list(tests_dir.glob('test_*.py'))

print(f"Remaining test files in server/src/: {len(remaining_in_src)}")
for f in remaining_in_src:
    print(f"  - {f.name}")

print(f"\nTest files now in server/tests/: {len(in_tests)}")
for f in sorted(in_tests):
    print(f"  - {f.name}")

print(f"\n{'='*60}")
print(f"Successful moves: {len(successful_moves)}")
print(f"Failed moves: {len(failed_moves)}")
print(f"{'='*60}\n")

if failed_moves:
    print("Failed to move:")
    for f in failed_moves:
        print(f"  - {f}")
    exit(1)
else:
    print("✓ All test files successfully moved!")
    exit(0)

#!/usr/bin/env python
"""
Create initial admin user for Neighborhood BBS
Usage: python create_admin_user.py --username admin --password secret --email admin@bbs.local
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models import Database, AdminUser
from admin.auth import hash_password


def create_admin_user(username, password, email, role='admin'):
    """Create a new admin user"""
    # Initialize database if needed
    db = Database()
    db.init_db()

    # Check if user already exists
    existing_user = AdminUser.get_by_username(username)
    if existing_user:
        print(f"❌ Admin user '{username}' already exists")
        return False

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user_id = AdminUser.create(
        username=username,
        password_hash=password_hash,
        email=email,
        role=role
    )

    if user_id:
        print(f"✓ Admin user '{username}' created successfully")
        print(f"  - ID: {user_id}")
        print(f"  - Email: {email}")
        print(f"  - Role: {role}")
        return True
    else:
        print(f"❌ Failed to create admin user")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Create an initial admin user for Neighborhood BBS'
    )
    parser.add_argument('--username', required=True, help='Admin username')
    parser.add_argument('--password', required=True, help='Admin password')
    parser.add_argument('--email', required=True, help='Admin email')
    parser.add_argument('--role', default='admin', choices=['admin', 'moderator'],
                        help='Admin role (default: admin)')

    args = parser.parse_args()

    if len(args.password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False

    success = create_admin_user(args.username, args.password, args.email, args.role)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

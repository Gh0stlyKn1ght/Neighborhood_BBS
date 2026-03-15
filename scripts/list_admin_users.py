#!/usr/bin/env python
"""
List all admin users in the system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models import Database


def list_admin_users():
    """List all admin users"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, is_active, created_at, last_login FROM admin_users')
    users = cursor.fetchall()
    conn.close()

    if not users:
        print("No admin users found")
        return

    print("\nAdmin Users:")
    print("-" * 100)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<15} {'Active':<7} {'Created':<20} {'Last Login':<20}")
    print("-" * 100)

    for user in users:
        print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<15} {'Yes' if user[4] else 'No':<7} {user[5]:<20} {user[6] or 'Never':<20}")

    print("-" * 100)
    print(f"Total: {len(users)} admin user(s)")


if __name__ == '__main__':
    list_admin_users()

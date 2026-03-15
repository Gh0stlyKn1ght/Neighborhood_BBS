#!/usr/bin/env python3
"""
Initialize local SQLite database for Neighborhood BBS
Run this once before starting the app for the first time
"""

import sqlite3
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def init_database():
    """Initialize the SQLite database with schema"""
    
    db_path = "data/neighborhood_bbs.db"
    
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Check if database already exists
    if os.path.exists(db_path):
        print(f"✓ Database already exists: {db_path}")
        return
    
    print(f"📦 Initializing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            device_id TEXT,
            edited_at DATETIME,
            deleted_at DATETIME
        )
    ''')
    print("  ✓ messages table")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    print("  ✓ users table")
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    print("  ✓ admin_users table")
    
    # Banned devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            mac_address TEXT,
            ip_address TEXT,
            reason TEXT,
            banned_by TEXT,
            banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    print("  ✓ banned_devices table")
    
    # Network config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            data_type TEXT DEFAULT 'string',
            set_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            set_by TEXT
        )
    ''')
    print("  ✓ network_config table")
    
    # Themes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            primary_color TEXT,
            secondary_color TEXT,
            background_color TEXT,
            text_color TEXT,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 0
        )
    ''')
    print("  ✓ themes table")
    
    # Connections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            username TEXT,
            ip_address TEXT,
            connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            disconnected_at DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    print("  ✓ connections table")
    
    # Session table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            device_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    print("  ✓ sessions table")
    
    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            admin_user TEXT,
            target_entity TEXT,
            target_id TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')
    print("  ✓ audit_logs table")
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_banned_devices_ip ON banned_devices(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_banned_devices_mac ON banned_devices(mac_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_device ON connections(device_id)')
    print("  ✓ database indexes")
    
    # Add default configuration
    default_configs = [
        ('chat_log_retention_days', '30', 'integer'),
        ('theme_dark_mode', 'false', 'boolean'),
        ('max_message_length', '1000', 'integer'),
        ('enable_user_registration', 'false', 'boolean'),
        ('session_timeout_minutes', '1440', 'integer'),
    ]
    
    for key, value, dtype in default_configs:
        cursor.execute(
            'INSERT OR IGNORE INTO network_config (key, value, data_type) VALUES (?, ?, ?)',
            (key, value, dtype)
        )
    print("  ✓ default configuration")
    
    # Add default retro theme (IBM PC Blue on Black)
    cursor.execute('''
        INSERT OR IGNORE INTO themes 
        (name, primary_color, secondary_color, background_color, text_color, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', ('Retro Blue IBM', '#0055FF', '#0077FF', '#000000', '#0055FF'))
    print("  ✓ retro blue IBM theme (default)")
    
    # Add additional theme option
    cursor.execute('''
        INSERT OR IGNORE INTO themes 
        (name, primary_color, secondary_color, background_color, text_color, is_active)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', ('Modern', '#3498db', '#2ecc71', '#1a1a1a', '#ffffff'))
    print("  ✓ modern theme (optional)")
    
    conn.commit()
    conn.close()
    
    print("")
    print("✅ Database initialized successfully!")
    print(f"   Location: {db_path}")
    print("   Next step: python scripts/create_admin_user.py")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

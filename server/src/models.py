"""
Database models for Neighborhood BBS
"""

from datetime import datetime
from pathlib import Path
import sqlite3
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'neighborhood.db'


class Database:
    """SQLite database connection manager"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database with schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat messages table (supports privacy modes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                nickname TEXT NOT NULL,
                author TEXT,
                text TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
            )
        ''')
        
        # Board posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Post replies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'moderator',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Banned devices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_type TEXT,
                mac_address TEXT,
                ip_address TEXT,
                ban_reason TEXT,
                banned_by TEXT NOT NULL,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Network configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                description TEXT,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Theme settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_name TEXT UNIQUE NOT NULL,
                primary_color TEXT,
                secondary_color TEXT,
                background_color TEXT,
                text_color TEXT,
                font_family TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_banned_devices_active ON banned_devices(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_themes_active ON themes(is_active)')
        
        conn.commit()
        conn.close()
    
    def ensure_privacy_columns(self):
        """
        Ensure messages table has privacy-mode columns
        Adds expires_at and nickname columns if missing
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if expires_at column exists
            cursor.execute("PRAGMA table_info(messages)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'expires_at' not in columns:
                logger.info("Adding expires_at column to messages table")
                cursor.execute('''
                    ALTER TABLE messages ADD COLUMN expires_at TIMESTAMP
                ''')
                conn.commit()
            
            if 'nickname' not in columns:
                logger.info("Adding nickname column to messages table")
                cursor.execute('''
                    ALTER TABLE messages ADD COLUMN nickname TEXT
                ''')
                conn.commit()
            
            conn.close()
        except Exception as e:
            logger.warning(f"Error ensuring privacy columns: {e}")


# Database instance
db = Database()

# Initialize privacy mode columns
try:
    db.ensure_privacy_columns()
except Exception as e:
    logger.warning(f"Failed to ensure privacy columns: {e}")


class ChatRoom:
    """Chat room model"""
    
    @staticmethod
    def get_all():
        """Get all chat rooms"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chat_rooms ORDER BY created_at DESC')
        rooms = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rooms
    
    @staticmethod
    def get_by_id(room_id):
        """Get chat room by ID"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chat_rooms WHERE id = ?', (room_id,))
        room = cursor.fetchone()
        conn.close()
        return dict(room) if room else None
    
    @staticmethod
    def create(name, description=''):
        """Create a new chat room"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO chat_rooms (name, description) VALUES (?, ?)',
                (name, description)
            )
            conn.commit()
            room_id = cursor.lastrowid
            conn.close()
            return room_id
        except sqlite3.IntegrityError:
            conn.close()
            return None


class Message:
    """Chat message model"""
    
    @staticmethod
    def create(room_id, author, content):
        """Create a new message"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO messages (room_id, author, content) VALUES (?, ?, ?)',
            (room_id, author, content)
        )
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return message_id
    
    @staticmethod
    def get_by_room(room_id, limit=50, offset=0):
        """Get messages from a room"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, room_id, author, content, created_at FROM messages 
               WHERE room_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            (room_id, limit, offset)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return list(reversed(messages))  # Return in chronological order


class Post:
    """Community board post model"""
    
    @staticmethod
    def get_all(limit=30, offset=0):
        """Get all posts"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            (limit, offset)
        )
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts
    
    @staticmethod
    def get_by_id(post_id):
        """Get post by ID"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        post = cursor.fetchone()
        
        if post:
            post = dict(post)
            # Get replies
            cursor.execute(
                'SELECT * FROM post_replies WHERE post_id = ? ORDER BY created_at',
                (post_id,)
            )
            post['replies'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return post
    
    @staticmethod
    def create(title, content, author, category='general'):
        """Create a new post"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO posts (title, content, author, category) 
               VALUES (?, ?, ?, ?)''',
            (title, content, author, category)
        )
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id
    
    @staticmethod
    def delete(post_id):
        """Delete a post"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM post_replies WHERE post_id = ?', (post_id,))
        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_reply(post_id, author, content):
        """Add a reply to a post"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO post_replies (post_id, author, content) VALUES (?, ?, ?)',
            (post_id, author, content)
        )
        conn.commit()
        reply_id = cursor.lastrowid
        cursor.execute('UPDATE posts SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return reply_id


class AdminUser:
    """Admin user model"""
    
    @staticmethod
    def create(username, password_hash, email, role='moderator'):
        """Create a new admin user"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO admin_users (username, password_hash, email, role) 
                   VALUES (?, ?, ?, ?)''',
                (username, password_hash, email, role)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_username(username):
        """Get admin user by username"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def update_last_login(user_id):
        """Update last login timestamp"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()


class BannedDevice:
    """Banned device model"""
    
    @staticmethod
    def ban_device(device_id, device_type, mac_address, ip_address, ban_reason, banned_by, expires_at=None):
        """Ban a device"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO banned_devices 
                   (device_id, device_type, mac_address, ip_address, ban_reason, banned_by, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (device_id, device_type, mac_address, ip_address, ban_reason, banned_by, expires_at)
            )
            conn.commit()
            ban_id = cursor.lastrowid
            conn.close()
            return ban_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_all_bans(active_only=True):
        """Get all banned devices"""
        conn = db.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute(
                '''SELECT * FROM banned_devices 
                   WHERE is_active = 1 
                   ORDER BY banned_at DESC'''
            )
        else:
            cursor.execute('SELECT * FROM banned_devices ORDER BY banned_at DESC')
        bans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bans
    
    @staticmethod
    def get_by_device_id(device_id):
        """Get ban info by device ID"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM banned_devices WHERE device_id = ? AND is_active = 1', (device_id,))
        ban = cursor.fetchone()
        conn.close()
        return dict(ban) if ban else None
    
    @staticmethod
    def get_by_ip(ip_address):
        """Get ban info by IP address"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM banned_devices WHERE ip_address = ? AND is_active = 1',
            (ip_address,)
        )
        ban = cursor.fetchone()
        conn.close()
        return dict(ban) if ban else None
    
    @staticmethod
    def unban_device(device_id):
        """Unban a device"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE banned_devices SET is_active = 0 WHERE device_id = ?',
            (device_id,)
        )
        conn.commit()
        conn.close()


class NetworkConfig:
    """Network configuration model"""
    
    @staticmethod
    def set_config(setting_name, setting_value, setting_type='string', description='', updated_by='system'):
        """Set or update network configuration"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT OR REPLACE INTO network_config 
                   (setting_name, setting_value, setting_type, description, updated_by) 
                   VALUES (?, ?, ?, ?, ?)''',
                (setting_name, setting_value, setting_type, description, updated_by)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False
    
    @staticmethod
    def get_config(setting_name):
        """Get network configuration setting"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM network_config WHERE setting_name = ?', (setting_name,))
        config = cursor.fetchone()
        conn.close()
        return dict(config) if config else None
    
    @staticmethod
    def get_all_configs():
        """Get all network configurations"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM network_config ORDER BY setting_name')
        configs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return configs


class ThemeSettings:
    """Theme settings model"""
    
    @staticmethod
    def create_theme(theme_name, primary_color='#007bff', secondary_color='#6c757d', 
                    background_color='#ffffff', text_color='#000000', font_family='Arial, sans-serif'):
        """Create a new theme"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO themes 
                   (theme_name, primary_color, secondary_color, background_color, text_color, font_family)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (theme_name, primary_color, secondary_color, background_color, text_color, font_family)
            )
            conn.commit()
            theme_id = cursor.lastrowid
            conn.close()
            return theme_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_all_themes():
        """Get all themes"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM themes ORDER BY created_at DESC')
        themes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return themes
    
    @staticmethod
    def get_active_theme():
        """Get the currently active theme"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM themes WHERE is_active = 1 LIMIT 1')
        theme = cursor.fetchone()
        conn.close()
        return dict(theme) if theme else None
    
    @staticmethod
    def set_active_theme(theme_id):
        """Set a theme as active (only one can be active)"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE themes SET is_active = 0')
        cursor.execute('UPDATE themes SET is_active = 1 WHERE id = ?', (theme_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_theme(theme_id, **kwargs):
        """Update theme settings"""
        conn = db.get_connection()
        cursor = conn.cursor()
        allowed_fields = ['primary_color', 'secondary_color', 'background_color', 'text_color', 'font_family']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                cursor.execute(
                    f'UPDATE themes SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (value, theme_id)
                )
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete_theme(theme_id):
        """Delete a theme"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM themes WHERE id = ?', (theme_id,))
        conn.commit()
        conn.close()

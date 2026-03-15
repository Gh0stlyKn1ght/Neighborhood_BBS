"""
Database models for Neighborhood BBS
"""

from datetime import datetime
from pathlib import Path
import sqlite3
import json

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
        
        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)')
        
        conn.commit()
        conn.close()


# Database instance
db = Database()


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

"""
Privacy Modes Handler - Manages message storage based on admin's privacy choice
Supports three modes:
- FULL_PRIVACY: Messages in RAM only, deleted on disconnect (default)
- HYBRID: Messages saved 7 days then auto-deleted
- PERSISTENT: All messages saved permanently
"""

import json
import logging
from datetime import datetime, timedelta
from threading import Lock
from collections import defaultdict
from models import Database

logger = logging.getLogger(__name__)


class PrivacyModeHandler:
    """Manages message storage based on privacy mode selected during setup"""
    
    # In-memory storage for full privacy mode
    _message_storage = defaultdict(list)
    _storage_lock = Lock()
    
    def __init__(self, privacy_mode='full_privacy', db=None):
        """
        Initialize handler with privacy mode
        
        Args:
            privacy_mode: 'full_privacy', 'hybrid', or 'persistent'
            db: Optional Database instance (for testing); defaults to main database
        """
        if privacy_mode not in ['full_privacy', 'hybrid', 'persistent']:
            raise ValueError(f"Invalid privacy mode: {privacy_mode}")
        
        self.privacy_mode = privacy_mode
        self.db = db if db is not None else Database()
    
    @staticmethod
    def get_current_mode():
        """Get currently configured privacy mode from setup_config"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('privacy_mode',)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return 'full_privacy'  # Default
        except Exception as e:
            logger.error(f"Error getting privacy mode: {e}")
            return 'full_privacy'
    
    @classmethod
    def create_handler_from_config(cls):
        """Factory method: Create handler using current config"""
        mode = cls.get_current_mode()
        return cls(mode)
    
    def save_message(self, session_id, nickname, text, room_id=None):
        """
        Save message according to privacy mode
        
        Args:
            session_id: User's session ID (not tracked to user)
            nickname: User's chosen nickname
            text: Message text
            room_id: Optional chat room ID
            
        Returns:
            dict with message data or None if error
        """
        try:
            message_data = {
                'session_id': session_id,
                'nickname': nickname,
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'room_id': room_id
            }
            
            if self.privacy_mode == 'full_privacy':
                return self._save_full_privacy(session_id, message_data)
            
            elif self.privacy_mode == 'hybrid':
                return self._save_hybrid(message_data)
            
            elif self.privacy_mode == 'persistent':
                return self._save_persistent(message_data)
        
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    @classmethod
    def _save_full_privacy(cls, session_id, message_data):
        """
        Save message in RAM only (full privacy mode)
        Message deleted when session disconnects
        """
        with cls._storage_lock:
            cls._message_storage[session_id].append(message_data)
            logger.debug(f"Saved message to RAM for session {session_id}")
        
        return message_data
    
    def _save_hybrid(self, message_data):
        """
        Save message to database with 7-day TTL (hybrid mode)
        Auto-delete older than 7 days
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(days=7)
            
            cursor.execute('''
                INSERT INTO messages (nickname, text, created_at, expires_at, room_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                message_data['nickname'],
                message_data['text'],
                datetime.now(),
                expires_at,
                message_data.get('room_id')
            ))
            
            conn.commit()
            message_id = cursor.lastrowid
            conn.close()
            
            logger.debug(f"Saved message to DB (hybrid) with ID {message_id}")
            message_data['id'] = message_id
            return message_data
        
        except Exception as e:
            logger.error(f"Error saving hybrid message: {e}")
            return None
    
    def _save_persistent(self, message_data):
        """
        Save message to database permanently (persistent mode)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (nickname, text, created_at, room_id)
                VALUES (?, ?, ?, ?)
            ''', (
                message_data['nickname'],
                message_data['text'],
                datetime.now(),
                message_data.get('room_id')
            ))
            
            conn.commit()
            message_id = cursor.lastrowid
            conn.close()
            
            logger.debug(f"Saved message to DB (persistent) with ID {message_id}")
            message_data['id'] = message_id
            return message_data
        
        except Exception as e:
            logger.error(f"Error saving persistent message: {e}")
            return None
    
    def get_message_history(self, session_id=None, room_id=None, limit=100):
        """
        Get message history based on privacy mode
        
        Args:
            session_id: Optional session ID (for full privacy current session only)
            room_id: Optional room ID to filter by
            limit: Max messages to return
            
        Returns:
            List of message dicts
        """
        try:
            if self.privacy_mode == 'full_privacy':
                return self._get_history_full_privacy(session_id, limit)
            
            elif self.privacy_mode == 'hybrid':
                return self._get_history_hybrid(room_id, limit)
            
            elif self.privacy_mode == 'persistent':
                return self._get_history_persistent(room_id, limit)
        
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    @classmethod
    def _get_history_full_privacy(cls, session_id, limit):
        """
        Get messages from RAM for current session only
        (For full privacy mode: admin dashboard shows live chat only)
        """
        if not session_id:
            return []
        
        with cls._storage_lock:
            messages = cls._message_storage.get(session_id, [])
            return messages[-limit:] if messages else []
    
    def _get_history_hybrid(self, room_id, limit):
        """
        Get messages from DB, only non-expired ones (hybrid mode)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if room_id:
                cursor.execute('''
                    SELECT id, nickname, text, created_at, room_id
                    FROM messages
                    WHERE room_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (room_id, limit))
            else:
                cursor.execute('''
                    SELECT id, nickname, text, created_at, room_id
                    FROM messages
                    WHERE expires_at IS NULL OR expires_at > datetime('now')
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in rows:
                messages.append({
                    'id': row[0],
                    'nickname': row[1],
                    'text': row[2],
                    'timestamp': row[3],
                    'room_id': row[4]
                })
            
            return list(reversed(messages))  # Return chronological order
        
        except Exception as e:
            logger.error(f"Error getting hybrid history: {e}")
            return []
    
    def _get_history_persistent(self, room_id, limit):
        """
        Get all messages from DB (persistent mode, no TTL)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if room_id:
                cursor.execute('''
                    SELECT id, nickname, text, created_at, room_id
                    FROM messages
                    WHERE room_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (room_id, limit))
            else:
                cursor.execute('''
                    SELECT id, nickname, text, created_at, room_id
                    FROM messages
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in rows:
                messages.append({
                    'id': row[0],
                    'nickname': row[1],
                    'text': row[2],
                    'timestamp': row[3],
                    'room_id': row[4]
                })
            
            return list(reversed(messages))  # Return chronological order
        
        except Exception as e:
            logger.error(f"Error getting persistent history: {e}")
            return []
    
    @classmethod
    def on_disconnect(cls, session_id):
        """
        Called when user disconnects
        In full privacy mode: delete message history for this session
        """
        try:
            with cls._storage_lock:
                if session_id in cls._message_storage:
                    count = len(cls._message_storage[session_id])
                    del cls._message_storage[session_id]
                    logger.debug(f"Cleared {count} messages for session {session_id} (full privacy)")
        
        except Exception as e:
            logger.error(f"Error on_disconnect: {e}")
    
    def cleanup_expired_messages(self):
        """
        Clean up expired messages (hybrid mode)
        Called by scheduler nightly
        """
        if self.privacy_mode != 'hybrid':
            logger.debug(f"Cleanup not needed for {self.privacy_mode} mode")
            return 0
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM messages
                WHERE expires_at < datetime('now')
            ''')
            count = cursor.fetchone()[0]
            
            cursor.execute('''
                DELETE FROM messages
                WHERE expires_at < datetime('now')
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {count} expired messages (hybrid mode)")
            return count
        
        except Exception as e:
            logger.error(f"Error cleaning up messages: {e}")
            return 0
    
    def get_statistics(self):
        """
        Get statistics about message storage
        Admin-visible, aggregate data only (no individual tracking)
        """
        try:
            if self.privacy_mode == 'full_privacy':
                with self._storage_lock:
                    total_messages = sum(len(msgs) for msgs in self._message_storage.values())
                    total_sessions = len(self._message_storage)
                    
                    return {
                        'privacy_mode': 'full_privacy',
                        'total_messages_in_memory': total_messages,
                        'active_sessions': total_sessions,
                        'note': 'All messages deleted on disconnect'
                    }
            
            else:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM messages')
                total = cursor.fetchone()[0]
                
                if self.privacy_mode == 'hybrid':
                    cursor.execute('''
                        SELECT COUNT(*) FROM messages
                        WHERE expires_at < datetime('now')
                    ''')
                    expired = cursor.fetchone()[0]
                    conn.close()
                    
                    return {
                        'privacy_mode': 'hybrid',
                        'total_messages': total,
                        'expired_pending_cleanup': expired,
                        'retention_days': 7,
                        'note': 'Messages auto-delete after 7 days'
                    }
                
                else:  # persistent
                    conn.close()
                    return {
                        'privacy_mode': 'persistent',
                        'total_messages': total,
                        'note': 'All messages permanently stored'
                    }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}

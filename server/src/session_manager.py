"""
Session Manager - Manages anonymous user sessions
Tracks connected users, nicknames, session UUIDs
"""

import uuid
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
from models import Database
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages anonymous user sessions"""
    
    # In-memory active sessions
    _active_sessions = {}
    _session_lock = Lock()
    
    # Session timeout (24 hours)
    SESSION_TIMEOUT = 24 * 60 * 60  # seconds
    
    @staticmethod
    def create_session(nickname):
        """
        Create a new session for an anonymous user
        
        Args:
            nickname: User's chosen nickname
            
        Returns:
            dict: {session_id, nickname, connected_at, expires_at}
        """
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=SessionManager.SESSION_TIMEOUT)

            session_data = {
                'session_id': session_id,
                'nickname': nickname,
                'connected_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_activity': now.isoformat()
            }

            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            try:
                # Serialize create-session checks and writes to prevent nickname races.
                cursor.execute('BEGIN IMMEDIATE')

                # Expire stale sessions first so nickname checks use current active set.
                cursor.execute('''
                    UPDATE sessions
                    SET disconnected_at = ?
                    WHERE disconnected_at IS NULL AND expires_at IS NOT NULL AND expires_at <= ?
                ''', (now, now))

                cursor.execute('''
                    SELECT 1 FROM sessions
                    WHERE disconnected_at IS NULL
                      AND (expires_at IS NULL OR expires_at > ?)
                      AND LOWER(nickname) = LOWER(?)
                    LIMIT 1
                ''', (now, nickname))

                if cursor.fetchone():
                    conn.rollback()
                    logger.warning(f"Nickname collision attempted: {nickname}")
                    return {'error': 'nickname_taken', 'message': 'That nickname is already in use'}

                cursor.execute('''
                    INSERT INTO sessions (session_id, nickname, connected_at, expires_at, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    nickname,
                    now,
                    expires_at,
                    now,
                ))

                conn.commit()
            finally:
                conn.close()

            with SessionManager._session_lock:
                SessionManager._active_sessions[session_id] = session_data
            
            logger.info(f"Created session {session_id} for {nickname}")
            return session_data
        
        except sqlite3.IntegrityError:
            logger.warning(f"Session creation collision for nickname: {nickname}")
            return {'error': 'nickname_taken', 'message': 'That nickname is already in use'}
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    @staticmethod
    def get_session(session_id):
        """
        Get session by ID
        
        Args:
            session_id: Session UUID
            
        Returns:
            dict: Session data or None
        """
        try:
            with SessionManager._session_lock:
                session = SessionManager._active_sessions.get(session_id)
            
            if session:
                # Check if expired
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    SessionManager.close_session(session_id)
                    return None
                
                return session
            
            # Try from database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions
                WHERE session_id = ? AND disconnected_at IS NULL AND expires_at > datetime('now')
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'session_id': row['session_id'],
                    'nickname': row['nickname'],
                    'connected_at': row['connected_at'],
                    'expires_at': row['expires_at']
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    @staticmethod
    def update_nickname(session_id, new_nickname):
        """
        Update user's nickname mid-session
        
        Args:
            session_id: Session UUID
            new_nickname: New nickname
            
        Returns:
            dict: {'ok': True} on success or {'error': '<reason>'} on failure
        """
        try:
            now = datetime.utcnow()

            # Update database in a serialized transaction to prevent nickname collisions.
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute('BEGIN IMMEDIATE')

                cursor.execute('''
                    SELECT 1 FROM sessions
                    WHERE session_id = ?
                      AND disconnected_at IS NULL
                      AND (expires_at IS NULL OR expires_at > ?)
                    LIMIT 1
                ''', (session_id, now))
                if not cursor.fetchone():
                    conn.rollback()
                    return {'error': 'session_not_found'}

                cursor.execute('''
                    SELECT 1 FROM sessions
                    WHERE disconnected_at IS NULL
                      AND (expires_at IS NULL OR expires_at > ?)
                      AND LOWER(nickname) = LOWER(?)
                      AND session_id != ?
                    LIMIT 1
                ''', (now, new_nickname, session_id))
                if cursor.fetchone():
                    conn.rollback()
                    return {'error': 'nickname_taken'}

                cursor.execute('''
                    UPDATE sessions
                    SET nickname = ?, updated_at = datetime('now')
                    WHERE session_id = ?
                ''', (new_nickname, session_id))

                conn.commit()
            finally:
                conn.close()

            # Update memory cache only after DB commit succeeds.
            with SessionManager._session_lock:
                if session_id in SessionManager._active_sessions:
                    SessionManager._active_sessions[session_id]['nickname'] = new_nickname
            
            logger.info(f"Updated session {session_id} nickname to {new_nickname}")
            return {'ok': True}
        
        except Exception as e:
            logger.error(f"Error updating nickname: {e}")
            return {'error': 'update_failed'}
    
    @staticmethod
    def update_activity(session_id):
        """
        Update last activity timestamp (keep alive)
        
        Args:
            session_id: Session UUID
        """
        try:
            with SessionManager._session_lock:
                if session_id in SessionManager._active_sessions:
                    SessionManager._active_sessions[session_id]['last_activity'] = datetime.now().isoformat()
            
            # Update database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions
                SET last_activity = datetime('now')
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.debug(f"Error updating activity: {e}")
    
    @staticmethod
    def close_session(session_id):
        """
        Close a session when user disconnects
        
        Args:
            session_id: Session UUID
        """
        try:
            # Remove from memory
            with SessionManager._session_lock:
                if session_id in SessionManager._active_sessions:
                    del SessionManager._active_sessions[session_id]
            
            # Update database
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions
                SET disconnected_at = datetime('now')
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Closed session {session_id}")
        
        except Exception as e:
            logger.error(f"Error closing session: {e}")
    
    @staticmethod
    def get_active_sessions():
        """
        Get count of active sessions
        
        Returns:
            int: Number of connected users
        """
        try:
            with SessionManager._session_lock:
                # Clean up expired sessions in memory
                now = datetime.now()
                expired = []
                for sid, session in SessionManager._active_sessions.items():
                    expires_at = datetime.fromisoformat(session['expires_at'])
                    if now > expires_at:
                        expired.append(sid)
                
                for sid in expired:
                    del SessionManager._active_sessions[sid]
                
                return len(SessionManager._active_sessions)
        
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return 0
    
    @staticmethod
    def get_connected_users():
        """
        Get list of currently connected users (nicknames only)
        
        Returns:
            list: List of nicknames
        """
        try:
            with SessionManager._session_lock:
                users = [
                    session['nickname']
                    for session in SessionManager._active_sessions.values()
                ]
            return users
        
        except Exception as e:
            logger.error(f"Error getting connected users: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_sessions():
        """
        Clean up expired sessions from database
        Runs periodically (e.g., daily)
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get count of expired sessions
            cursor.execute('''
                SELECT COUNT(*) FROM sessions
                WHERE disconnected_at < datetime('now', '-7 days')
            ''')
            count = cursor.fetchone()[0]
            
            # Delete sessions older than 7 days
            cursor.execute('''
                DELETE FROM sessions
                WHERE disconnected_at < datetime('now', '-7 days')
            ''')
            
            conn.commit()
            conn.close()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired session records")
        
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    @staticmethod
    def get_session_statistics():
        """
        Get stats about sessions (for admin dashboard)
        
        Returns:
            dict: Session statistics
        """
        try:
            active_count = SessionManager.get_active_sessions()
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Total sessions since app started
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total = cursor.fetchone()[0]
            
            # Sessions today
            cursor.execute('''
                SELECT COUNT(*) FROM sessions
                WHERE date(connected_at) = date('now')
            ''')
            today = cursor.fetchone()[0]
            
            # Average session duration
            cursor.execute('''
                SELECT AVG(
                    (julianday(disconnected_at) - julianday(connected_at)) * 24 * 60
                ) as avg_duration_minutes
                FROM sessions
                WHERE disconnected_at IS NOT NULL
            ''')
            avg_duration = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'active_sessions': active_count,
                'total_sessions': total,
                'sessions_today': today,
                'avg_duration_minutes': round(avg_duration, 1)
            }
        
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {
                'active_sessions': 0,
                'total_sessions': 0,
                'sessions_today': 0,
                'avg_duration_minutes': 0
            }
    
    @staticmethod
    def block_user(session_id, blocked_nickname, reason=None):
        """
        Block another user (prevent seeing their messages)
        
        Args:
            session_id: Your session ID
            blocked_nickname: Nickname to block
            reason: Optional reason for blocking
            
        Returns:
            bool: True if successful
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO blocked_users 
                (session_id, blocked_nickname, reason)
                VALUES (?, ?, ?)
            ''', (session_id, blocked_nickname, reason))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Session {session_id[:8]} blocked {blocked_nickname}")
            return True
        
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return False
    
    @staticmethod
    def unblock_user(session_id, blocked_nickname):
        """
        Unblock a previously blocked user
        
        Args:
            session_id: Your session ID
            blocked_nickname: Nickname to unblock
            
        Returns:
            bool: True if successful
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM blocked_users
                WHERE session_id = ? AND blocked_nickname = ?
            ''', (session_id, blocked_nickname))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Session {session_id[:8]} unblocked {blocked_nickname}")
            return True
        
        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            return False
    
    @staticmethod
    def get_blocked_users(session_id):
        """
        Get list of blocked user nicknames for a session
        
        Args:
            session_id: Your session ID
            
        Returns:
            list: Blocked nicknames
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT blocked_nickname FROM blocked_users
                WHERE session_id = ?
                ORDER BY blocked_at DESC
            ''', (session_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]
        
        except Exception as e:
            logger.error(f"Error getting blocked users: {e}")
            return []
    
    @staticmethod
    def is_blocked(session_id, other_nickname):
        """
        Check if a nickname is blocked for this session
        
        Args:
            session_id: Your session ID
            other_nickname: Nickname to check
            
        Returns:
            bool: True if blocked
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM blocked_users
                WHERE session_id = ? AND blocked_nickname = ?
            ''', (session_id, other_nickname))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
        
        except Exception as e:
            logger.error(f"Error checking if blocked: {e}")
            return False

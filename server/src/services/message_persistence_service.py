"""
Message Persistence Service - Wraps privacy handler with additional features
Manages message storage based on privacy mode and provides statistics
"""

import logging
from datetime import datetime, timedelta
from threading import Lock, Thread
import time
from privacy_handler import PrivacyModeHandler
from models import Database
from mode_helper import ModeHelper

logger = logging.getLogger(__name__)


class MessagePersistenceService:
    """Service for managing message persistence based on privacy mode"""
    
    def __init__(self):
        """Initialize service with privacy handler"""
        self.privacy_handler = PrivacyModeHandler(ModeHelper.get_privacy_mode())
        self.db = Database()
        self._cleanup_thread = None
        self._cleanup_running = False
    
    def save_message(self, session_id, nickname, text, room_id=None):
        """
        Save a message according to privacy mode
        
        Args:
            session_id: User's session ID
            nickname: User's nickname
            text: Message text
            room_id: Optional chat room ID
        
        Returns:
            dict: Message data or None
        """
        try:
            message = self.privacy_handler.save_message(
                session_id=session_id,
                nickname=nickname,
                text=text,
                room_id=room_id
            )
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    def get_messages(self, session_id=None, room_id=None, limit=100, offset=0):
        """
        Get message history based on privacy mode
        
        Args:
            session_id: Optional session ID (for full privacy: current session only)
            room_id: Optional room ID to filter by
            limit: Max messages to return
            offset: Pagination offset
        
        Returns:
            list: Messages in chronological order
        """
        try:
            messages = self.privacy_handler.get_message_history(
                session_id=session_id,
                room_id=room_id,
                limit=limit + offset
            )
            
            # Apply pagination
            return messages[offset:offset+limit]
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def on_user_disconnect(self, session_id):
        """
        Called when user disconnects
        In full privacy mode: purges message history for this session
        
        Args:
            session_id: User's session ID
        """
        try:
            mode = self.privacy_handler.privacy_mode
            
            if mode == 'full_privacy':
                # Delete session's entire message history
                PrivacyModeHandler.on_disconnect(session_id)
                logger.info(f"Cleared messages for session {session_id} ({mode} mode)")
            else:
                logger.debug(f"No cleanup for session {session_id} ({mode} mode)")
        
        except Exception as e:
            logger.error(f"Error on_user_disconnect: {e}")
    
    def get_message_count(self, room_id=None):
        """
        Get count of stored messages
        
        Args:
            room_id: Optional room ID to filter by
        
        Returns:
            int: Message count
        """
        try:
            mode = self.privacy_handler.privacy_mode
            
            if mode == 'full_privacy':
                # Can't count RAM messages reliably
                return 0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if room_id:
                cursor.execute('''
                    SELECT COUNT(*) FROM messages
                    WHERE room_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                ''', (room_id,))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM messages
                    WHERE expires_at IS NULL OR expires_at > datetime('now')
                ''')
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
        
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def cleanup_expired_messages(self):
        """
        Clean up expired messages (hybrid mode)
        Returns count of deleted messages
        """
        try:
            if self.privacy_handler.privacy_mode != 'hybrid':
                return 0
            
            return self.privacy_handler.cleanup_expired_messages()
        
        except Exception as e:
            logger.error(f"Error cleaning up expired messages: {e}")
            return 0
    
    def get_privacy_mode(self):
        """Get current privacy mode"""
        return self.privacy_handler.privacy_mode
    
    def get_statistics(self):
        """Get privacy/message statistics"""
        try:
            mode = self.privacy_handler.privacy_mode
            
            stats = {
                'privacy_mode': mode,
                'total_messages': self.get_message_count(),
                'timestamp': datetime.now().isoformat()
            }
            
            if mode == 'hybrid':
                # Count expired messages waiting for cleanup
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM messages
                    WHERE expires_at < datetime('now')
                ''')
                expired_count = cursor.fetchone()[0]
                conn.close()
                
                stats['expired_messages_pending_cleanup'] = expired_count
                stats['retention_days'] = 7
            
            elif mode == 'persistent':
                stats['message_retention'] = 'Permanent'
            
            elif mode == 'full_privacy':
                stats['message_storage'] = 'RAM only (session-based)'
                stats['persistence'] = 'No database storage'
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    def start_cleanup_scheduler(self, interval_hours=6):
        """
        Start background scheduler to clean up expired messages
        
        Args:
            interval_hours: Cleanup interval in hours (default 6 hours)
        """
        if self._cleanup_running:
            logger.warning("Cleanup scheduler already running")
            return
        
        if self.privacy_handler.privacy_mode != 'hybrid':
            logger.debug(f"Cleanup scheduler not needed for {self.privacy_handler.privacy_mode} mode")
            return
        
        logger.info(f"Starting message cleanup scheduler (every {interval_hours} hours)")
        
        self._cleanup_running = True
        self._cleanup_thread = Thread(
            target=self._cleanup_worker,
            args=(interval_hours * 3600,),
            daemon=True
        )
        self._cleanup_thread.start()
    
    def stop_cleanup_scheduler(self):
        """Stop the background cleanup scheduler"""
        self._cleanup_running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("Message cleanup scheduler stopped")
    
    def _cleanup_worker(self, interval_seconds):
        """
        Background worker that periodically cleans up expired messages
        
        Args:
            interval_seconds: Interval between cleanups
        """
        while self._cleanup_running:
            try:
                time.sleep(interval_seconds)
                
                if not self._cleanup_running:
                    break
                
                count = self.cleanup_expired_messages()
                if count > 0:
                    logger.info(f"Cleanup worker: deleted {count} expired messages")
            
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")


# Singleton instance
_message_persistence_service = None


def get_message_persistence_service():
    """Get or create singleton service instance"""
    global _message_persistence_service
    
    if _message_persistence_service is None:
        _message_persistence_service = MessagePersistenceService()
    
    return _message_persistence_service

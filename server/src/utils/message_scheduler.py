"""
Message Cleanup Scheduler - Manages auto-deletion of expired messages
For HYBRID privacy mode: auto-delete messages older than 7 days
"""

import logging
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread
from models import Database
from admin_config import AdminConfig

logger = logging.getLogger(__name__)


class MessageCleanupScheduler:
    """Manages scheduled cleanup of expired messages"""
    
    _scheduler_running = False
    _scheduler_thread = None
    
    @staticmethod
    def schedule_daily_cleanup():
        """Schedule daily message cleanup (runs at 2 AM)"""
        schedule.every().day.at("02:00").do(MessageCleanupScheduler.cleanup_expired_messages)
        logger.info("Scheduled daily message cleanup at 02:00 UTC")
    
    @staticmethod
    def cleanup_expired_messages():
        """
        Clean up expired messages from database
        Only runs if hybrid privacy mode is enabled
        """
        try:
            privacy_mode = AdminConfig.get_privacy_mode()
            
            if privacy_mode != 'hybrid':
                logger.debug(f"Cleanup skipped (privacy mode: {privacy_mode})")
                return 0
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Count expired messages
            cursor.execute('''
                SELECT COUNT(*) FROM messages
                WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
            ''')
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Delete expired messages
                cursor.execute('''
                    DELETE FROM messages
                    WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
                ''')
                
                conn.commit()
                logger.info(f"Cleanup: Deleted {count} expired messages (hybrid mode)")
            else:
                logger.debug("Cleanup: No expired messages to delete")
            
            # Get statistics
            cursor.execute('SELECT COUNT(*) FROM messages')
            total = cursor.fetchone()[0]
            
            logger.info(f"After cleanup: {total} messages remaining in database")
            
            conn.close()
            return count
        
        except Exception as e:
            logger.error(f"Error during message cleanup: {e}")
            return 0
    
    @staticmethod
    def start_scheduler():
        """Start the background scheduler thread"""
        if MessageCleanupScheduler._scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule the cleanup
        MessageCleanupScheduler.schedule_daily_cleanup()
        
        # Start background thread
        MessageCleanupScheduler._scheduler_running = True
        MessageCleanupScheduler._scheduler_thread = Thread(
            target=MessageCleanupScheduler._run_scheduler,
            daemon=True,
            name='MessageCleanupScheduler'
        )
        MessageCleanupScheduler._scheduler_thread.start()
        logger.info("Message cleanup scheduler started (background thread)")
    
    @staticmethod
    def _run_scheduler():
        """
        Run the scheduler in background
        This blocks, so it should run in a separate thread
        """
        try:
            while MessageCleanupScheduler._scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if scheduled tasks need to run
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            MessageCleanupScheduler._scheduler_running = False
    
    @staticmethod
    def stop_scheduler():
        """Stop the background scheduler"""
        MessageCleanupScheduler._scheduler_running = False
        if MessageCleanupScheduler._scheduler_thread:
            MessageCleanupScheduler._scheduler_thread.join(timeout=5)
        logger.info("Message cleanup scheduler stopped")
    
    @staticmethod
    def force_cleanup():
        """Force immediate cleanup (for testing/debugging)"""
        logger.info("Force cleanup initiated")
        return MessageCleanupScheduler.cleanup_expired_messages()
    
    @staticmethod
    def get_cleanup_stats():
        """Get statistics about cleanup"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Total messages
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            
            # Expired messages
            cursor.execute('''
                SELECT COUNT(*) FROM messages
                WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
            ''')
            expired_messages = cursor.fetchone()[0]
            
            # Messages expiring in next 24 hours
            cursor.execute('''
                SELECT COUNT(*) FROM messages
                WHERE expires_at > datetime('now') AND expires_at <= datetime('now', '+1 day')
            ''')
            expiring_soon = cursor.fetchone()[0]
            
            conn.close()
            
            privacy_mode = AdminConfig.get_privacy_mode()
            
            return {
                'privacy_mode': privacy_mode,
                'total_messages': total_messages,
                'expired_pending_cleanup': expired_messages,
                'expiring_in_24h': expiring_soon,
                'last_cleanup': None,  # Could be tracked in DB if needed
                'cleanup_enabled': privacy_mode == 'hybrid',
                'next_cleanup': '02:00 UTC (daily)' if privacy_mode == 'hybrid' else 'N/A'
            }
        
        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}")
            return {
                'error': str(e)
            }


def initialize_message_scheduler():
    """Initialize and start message scheduler on app startup"""
    try:
        privacy_mode = AdminConfig.get_privacy_mode()
        
        if privacy_mode == 'hybrid':
            MessageCleanupScheduler.start_scheduler()
            logger.info("Message scheduler initialized (hybrid mode detected)")
        else:
            logger.info(f"Message scheduler not needed (privacy mode: {privacy_mode})")
    
    except Exception as e:
        logger.warning(f"Failed to initialize message scheduler: {e}")

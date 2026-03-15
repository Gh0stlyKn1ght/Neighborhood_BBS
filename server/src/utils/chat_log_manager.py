"""
Chat log management - Automatic daily deletion
"""

from models import Database, Message
from datetime import datetime, timedelta
import logging
import schedule
import threading

logger = logging.getLogger(__name__)

# Default: keep chat logs for 30 days
DEFAULT_RETENTION_DAYS = 30


def delete_old_chat_logs(days=DEFAULT_RETENTION_DAYS):
    """Delete chat logs older than specified days"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = Database().get_connection()
        cursor = conn.cursor()
        
        # Get count of messages to be deleted
        cursor.execute('SELECT COUNT(*) FROM messages WHERE created_at < ?', (cutoff_date,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Delete old messages
            cursor.execute('DELETE FROM messages WHERE created_at < ?', (cutoff_date,))
            conn.commit()
            logger.info(f"Deleted {count} chat logs older than {days} days")
        
        conn.close()
        return count
    
    except Exception as e:
        logger.error(f"Error deleting old chat logs: {e}")
        return 0


def schedule_daily_chat_log_cleanup(days=DEFAULT_RETENTION_DAYS):
    """Schedule daily chat log cleanup at midnight"""
    def cleanup_task():
        delete_old_chat_logs(days)
    
    # Schedule for daily at midnight
    schedule.every().day.at("00:00").do(cleanup_task)
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            # Check every minute
            import time
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info(f"Chat log cleanup scheduled daily at 00:00 (retention: {days} days)")


def get_chat_log_retention_config():
    """Get chat log retention configuration"""
    from models import NetworkConfig
    
    config = NetworkConfig.get_config('chat_log_retention_days')
    if config:
        try:
            return int(config['setting_value'])
        except (ValueError, TypeError):
            pass
    
    return DEFAULT_RETENTION_DAYS


def set_chat_log_retention(days, admin_user='system'):
    """Set chat log retention period"""
    from models import NetworkConfig
    
    if days < 1:
        days = 1
    if days > 365:
        days = 365
    
    success = NetworkConfig.set_config(
        setting_name='chat_log_retention_days',
        setting_value=str(days),
        setting_type='integer',
        description=f'Delete chat logs older than {days} days (daily at 00:00 UTC)',
        updated_by=admin_user
    )
    
    if success:
        logger.info(f"Chat log retention set to {days} days by {admin_user}")
    
    return success


def get_message_stats():
    """Get message and storage statistics"""
    try:
        from models import Database
        
        conn = Database().get_connection()
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        
        # Messages by room
        cursor.execute('SELECT room_id, COUNT(*) as count FROM messages GROUP BY room_id ORDER BY count DESC')
        messages_by_room = cursor.fetchall()
        
        # Oldest and newest messages
        cursor.execute('SELECT MIN(created_at), MAX(created_at) FROM messages')
        result = cursor.fetchone()
        oldest_message = result[0] if result[0] else None
        newest_message = result[1] if result[1] else None
        
        conn.close()
        
        return {
            'total_messages': total_messages,
            'messages_by_room': messages_by_room,
            'oldest_message': oldest_message,
            'newest_message': newest_message
        }
    
    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        return None

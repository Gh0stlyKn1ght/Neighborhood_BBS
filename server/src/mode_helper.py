"""
Mode Helper - Determines Lite vs Full mode behavior
Provides utility functions for conditional features
"""

from setup_config import SetupConfig
import logging

logger = logging.getLogger(__name__)


class ModeHelper:
    """Helper class for determining BBS mode features"""
    
    _cached_mode = None
    _cache_timestamp = None
    
    @staticmethod
    def get_mode():
        """Get current BBS mode (lite or full)"""
        return SetupConfig.get_bbs_mode()
    
    @staticmethod
    def is_lite():
        """Check if running in Lite mode"""
        return ModeHelper.get_mode() == 'lite'
    
    @staticmethod
    def is_full():
        """Check if running in Full mode"""
        return ModeHelper.get_mode() == 'full'
    
    @staticmethod
    def get_privacy_mode():
        """
        Get privacy mode for this setup
        Lite mode always uses full_privacy (ephemeral)
        Full mode uses configured mode
        """
        mode = ModeHelper.get_mode()
        
        if mode == 'lite':
            return 'full_privacy'  # Always ephemeral in Lite
        else:
            # Full mode - get configured privacy mode
            try:
                from models import Database
                db = Database()
                conn = db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT value FROM setup_config WHERE key = ?',
                    ('privacy_mode',)
                )
                result = cursor.fetchone()
                conn.close()
                
                return result[0] if result else 'full_privacy'
            except Exception as e:
                logger.error(f"Error getting privacy mode: {e}")
                return 'full_privacy'
    
    @staticmethod
    def allow_room_creation():
        """Allow users to create chat rooms?"""
        return ModeHelper.is_full()
    
    @staticmethod
    def allow_admin_panel():
        """Allow admin panel access?"""
        return ModeHelper.is_full()
    
    @staticmethod
    def allow_themes():
        """Allow theme customization?"""
        return ModeHelper.is_full()
    
    @staticmethod
    def allow_settings():
        """Allow settings panel?"""
        return ModeHelper.is_full()
    
    @staticmethod
    def get_default_room_count():
        """
        Get number of default rooms to create
        Lite: 1 room (General chat)
        Full: Multiple rooms for different topics
        """
        if ModeHelper.is_lite():
            return 1  # Just one room for Lite
        else:
            return 3  # General, Off-Topic, Announcements for Full
    
    @staticmethod
    def get_feature_flags():
        """Get all feature flags for frontend UI"""
        mode = ModeHelper.get_mode()
        
        return {
            'bbs_mode': mode,
            'is_lite': mode == 'lite',
            'is_full': mode == 'full',
            'allow_room_creation': ModeHelper.allow_room_creation(),
            'allow_admin_panel': ModeHelper.allow_admin_panel(),
            'allow_themes': ModeHelper.allow_themes(),
            'allow_settings': ModeHelper.allow_settings(),
            'allow_user_blocking': True,  # Both modes have blocking
            'privacy_mode': ModeHelper.get_privacy_mode(),
            'messages_ephemeral': ModeHelper.get_privacy_mode() == 'full_privacy'
        }

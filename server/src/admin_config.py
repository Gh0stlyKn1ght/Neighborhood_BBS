"""
Admin Configuration - Get and manage admin-set configuration
Respects privacy settings and admin choices from setup wizard
"""

import json
import logging
from models import Database

logger = logging.getLogger(__name__)


class AdminConfig:
    """Centralized admin configuration manager"""
    
    @staticmethod
    def get_privacy_mode():
        """Get configured privacy mode"""
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
            
            return result[0] if result else 'full_privacy'
        except Exception as e:
            logger.error(f"Error getting privacy mode: {e}")
            return 'full_privacy'
    
    @staticmethod
    def get_account_system():
        """Get configured account system"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('account_system',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 'anonymous'
        except Exception as e:
            logger.error(f"Error getting account system: {e}")
            return 'anonymous'
    
    @staticmethod
    def get_access_control():
        """Get configured access control method"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('access_control',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 'open'
        except Exception as e:
            logger.error(f"Error getting access control: {e}")
            return 'open'
    
    @staticmethod
    def get_moderation_levels():
        """Get configured moderation levels"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('moderation_levels',)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                try:
                    return json.loads(result[0])
                except:
                    return ['content_filter']
            return ['content_filter']
        except Exception as e:
            logger.error(f"Error getting moderation levels: {e}")
            return ['content_filter']
    
    @staticmethod
    def get_violation_threshold():
        """Get violations threshold before timeout"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('violation_threshold',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return int(result[0]) if result else 5
        except Exception as e:
            logger.error(f"Error getting violation threshold: {e}")
            return 5
    
    @staticmethod
    def get_violation_window_minutes():
        """Get time window for counting violations"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('violation_window_minutes',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return int(result[0]) if result else 10
        except Exception as e:
            logger.error(f"Error getting violation window: {e}")
            return 10
    
    @staticmethod
    def get_session_timeout_hours():
        """Get session timeout duration in hours"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('session_timeout_hours',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return int(result[0]) if result else 24
        except Exception as e:
            logger.error(f"Error getting session timeout: {e}")
            return 24
    
    @staticmethod
    def get_all_config():
        """Get all non-encrypted configuration"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT key, value FROM setup_config WHERE encrypted = FALSE'
            )
            rows = cursor.fetchall()
            conn.close()
            
            config = {}
            for row in rows:
                key, value = row
                # Parse JSON values
                if key in ['moderation_levels']:
                    try:
                        config[key] = json.loads(value)
                    except:
                        config[key] = value
                # Parse integer values
                elif key in ['violation_threshold', 'violation_window_minutes', 'session_timeout_hours']:
                    try:
                        config[key] = int(value)
                    except:
                        config[key] = value
                else:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"Error getting all config: {e}")
            return {}
    
    @staticmethod
    def is_feature_enabled(feature_name):
        """
        Check if a moderation feature is enabled
        
        Args:
            feature_name: 'content_filter', 'session_timeout', 'device_ban'
            
        Returns:
            bool: True if feature enabled
        """
        levels = AdminConfig.get_moderation_levels()
        return feature_name in levels
    
    @staticmethod
    def should_track_individual_user():
        """
        Determine if individual user tracking is appropriate
        Returns False for full_privacy mode (privacy-first)
        """
        privacy_mode = AdminConfig.get_privacy_mode()
        return privacy_mode != 'full_privacy'
    
    @staticmethod
    def requires_passcode():
        """Check if joining requires passcode"""
        return AdminConfig.get_access_control() == 'passcode'
    
    @staticmethod
    def requires_approval():
        """Check if new users need approval"""
        return AdminConfig.get_access_control() == 'approved'

"""
Setup module - Initial configuration wizard for Neighborhood BBS
Guides admin through 5-step setup on first launch
"""

import json
import logging
from datetime import datetime
from models import Database

logger = logging.getLogger(__name__)


class SetupConfig:
    """Manage setup configuration"""
    
    def __init__(self, db=None):
        self.db = db or Database()
    
    @staticmethod
    def init_setup_table():
        """Create setup_config table if not exists"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setup_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                encrypted BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def is_setup_complete():
        """Check if initial setup is complete"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('setup_complete',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result and result[0] == 'true'
        except Exception as e:
            logger.error(f"Error checking setup status: {e}")
            return False
    
    @staticmethod
    def get_setup_step_1_data():
        """Get step 1 (admin password) data"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('admin_password_hash',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return {'completed': result is not None}
        except Exception as e:
            logger.error(f"Error getting step 1: {e}")
            return {'completed': False}
    
    @staticmethod
    def save_step_1(password_hash):
        """Save step 1 (admin password)"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value, encrypted) VALUES (?, ?, ?)',
                ('admin_password_hash', password_hash, True)
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving step 1: {e}")
            return False
    
    @staticmethod
    def save_step_2(privacy_mode):
        """Save step 2 (privacy mode selection)"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Validate privacy mode
            if privacy_mode not in ['full_privacy', 'hybrid', 'persistent']:
                raise ValueError(f"Invalid privacy mode: {privacy_mode}")
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('privacy_mode', privacy_mode)
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving step 2: {e}")
            return False
    
    @staticmethod
    def save_step_3(account_system):
        """Save step 3 (account system type)"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if account_system not in ['anonymous', 'optional', 'required']:
                raise ValueError(f"Invalid account system: {account_system}")
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('account_system', account_system)
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving step 3: {e}")
            return False
    
    @staticmethod
    def save_step_4(moderation_levels):
        """Save step 4 (moderation strategy)"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Moderation can be: content_only, hybrid
            if moderation_levels not in ['content_only', 'hybrid']:
                raise ValueError(f"Invalid moderation: {moderation_levels}")
            
            levels = {
                'content_only': ['content_filter'],
                'hybrid': ['content_filter', 'session_timeout', 'device_ban']
            }
            
            moderation_json = json.dumps(levels[moderation_levels])
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('moderation_levels', moderation_json)
            )
            
            # Set thresholds for hybrid
            if moderation_levels == 'hybrid':
                cursor.execute(
                    'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('violation_threshold', '5')
                )
                cursor.execute(
                    'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('violation_window_minutes', '10')
                )
                cursor.execute(
                    'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                    ('session_timeout_hours', '24')
                )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving step 4: {e}")
            return False
    
    @staticmethod
    def save_step_5(access_control, passcode_hash=None):
        """Save step 5 (access control)"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if access_control not in ['open', 'passcode', 'approved']:
                raise ValueError(f"Invalid access control: {access_control}")
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('access_control', access_control)
            )
            
            if access_control == 'passcode' and passcode_hash:
                cursor.execute(
                    'INSERT OR REPLACE INTO setup_config (key, value, encrypted) VALUES (?, ?, ?)',
                    ('passcode_hash', passcode_hash, True)
                )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving step 5: {e}")
            return False
    
    @staticmethod
    def mark_setup_complete():
        """Mark setup as complete"""
        try:
            SetupConfig.init_setup_table()
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('setup_complete', 'true')
            )
            cursor.execute(
                'INSERT OR REPLACE INTO setup_config (key, value) VALUES (?, ?)',
                ('setup_completed_at', datetime.now().isoformat())
            )
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error marking setup complete: {e}")
            return False
    
    @staticmethod
    def get_all_config():
        """Get all configuration (non-encrypted values)"""
        try:
            SetupConfig.init_setup_table()
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
                # Try to parse JSON values
                if key in ['moderation_levels']:
                    try:
                        config[key] = json.loads(value)
                    except:
                        config[key] = value
                else:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"Error getting all config: {e}")
            return {}
    
    @staticmethod
    def verify_admin_password(password_hash):
        """Verify if admin password is set"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value FROM setup_config WHERE key = ?',
                ('admin_password_hash',)
            )
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error verifying admin password: {e}")
            return False

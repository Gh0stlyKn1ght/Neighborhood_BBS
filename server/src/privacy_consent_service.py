"""
Privacy Consent Service - PHASE 4 Week 10
Manages privacy policy acknowledgments and user consent tracking
"""

from datetime import datetime
from models import Database
import logging

logger = logging.getLogger(__name__)

class PrivacyConsentService:
    """Manages privacy disclosures and user consent"""
    
    def __init__(self):
        self.db = Database()
    
    def get_active_privacy_bulletin(self):
        """Get the current active privacy bulletin"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, title, content, version FROM privacy_bulletins
                WHERE is_active = 1
                ORDER BY version DESC
                LIMIT 1
            ''')
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'title': result[1],
                    'content': result[2],
                    'version': result[3]
                }
            return None
        
        except Exception as e:
            logger.error(f"Error fetching privacy bulletin: {e}")
            conn.close()
            return None
    
    def record_consent_acknowledgment(self, session_id, bulletin_version, ip_address=None, device_info=None):
        """
        Record that a user acknowledged the privacy policy
        
        Args:
            session_id: User session ID
            bulletin_version: Version of privacy bulletin they acknowledged
            ip_address: Optional IP address from request
            device_info: Optional device/browser info
        
        Returns:
            bool: True if recorded successfully
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO privacy_consents
                (session_id, bulletin_version, acknowledged, acknowledged_at, ip_address, device_info)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
            ''', (session_id, bulletin_version, ip_address, device_info))
            
            conn.commit()
            logger.info(f"Recorded consent acknowledgment for session {session_id}")
            conn.close()
            return True
        
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            conn.close()
            return False
    
    def has_acknowledged_current_privacy_policy(self, session_id):
        """
        Check if user has acknowledged the current privacy policy
        
        Args:
            session_id: User session ID
        
        Returns:
            bool: True if acknowledged current version
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current bulletin version
            cursor.execute('SELECT version FROM privacy_bulletins WHERE is_active = 1 ORDER BY version DESC LIMIT 1')
            current_version = cursor.fetchone()
            
            if not current_version:
                conn.close()
                return True  # No policy = assume OK
            
            current_version = current_version[0]
            
            # Check if user has acknowledged this version
            cursor.execute('''
                SELECT 1 FROM privacy_consents
                WHERE session_id = ? AND bulletin_version = ? AND acknowledged = 1
            ''', (session_id, current_version))
            
            result = cursor.fetchone() is not None
            conn.close()
            return result
        
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            conn.close()
            return False
    
    def get_consent_status_for_session(self, session_id):
        """Get full consent status for a session"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT session_id, bulletin_version, acknowledged, acknowledged_at
                FROM privacy_consents
                WHERE session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'session_id': result[0],
                    'bulletin_version': result[1],
                    'acknowledged': result[2],
                    'acknowledged_at': result[3]
                }
            return None
        
        except Exception as e:
            logger.error(f"Error fetching consent status: {e}")
            conn.close()
            return None
    
    def create_privacy_bulletin(self, title, content, created_by):
        """
        Create a new privacy bulletin (for admin)
        
        Args:
            title: Bulletin title
            content: Markdown content of privacy policy
            created_by: Admin username
        
        Returns:
            dict: Bulletin info or None on error
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Deactivate old bulletins
            cursor.execute('UPDATE privacy_bulletins SET is_active = 0')
            
            # Insert new bulletin
            cursor.execute('''
                INSERT INTO privacy_bulletins (title, content, version, created_by, is_active)
                SELECT ?, ?, COALESCE(MAX(version), 0) + 1, ?, 1
                FROM privacy_bulletins
            ''', (title, content, created_by))
            
            conn.commit()
            bulletin_id = cursor.lastrowid
            
            # Get the inserted record
            cursor.execute('SELECT id, version FROM privacy_bulletins WHERE id = ?', (bulletin_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                logger.info(f"Created privacy bulletin v{result[1]} by {created_by}")
                return {'id': result[0], 'version': result[1]}
            return None
        
        except Exception as e:
            logger.error(f"Error creating privacy bulletin: {e}")
            conn.close()
            return None
    
    def get_consent_statistics(self):
        """Get statistics on privacy policy acknowledgments"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Total acknowledged
            cursor.execute('SELECT COUNT(*) FROM privacy_consents WHERE acknowledged = 1')
            total_acknowledged = cursor.fetchone()[0]
            
            # Current version acknowledgments
            cursor.execute('''
                SELECT COUNT(*) FROM privacy_consents pc
                WHERE pc.acknowledged = 1
                AND pc.bulletin_version = (
                    SELECT version FROM privacy_bulletins WHERE is_active = 1 LIMIT 1
                )
            ''')
            current_version = cursor.fetchone()[0]
            
            # By date
            cursor.execute('''
                SELECT DATE(acknowledged_at), COUNT(*)
                FROM privacy_consents
                WHERE acknowledged = 1
                GROUP BY DATE(acknowledged_at)
                ORDER BY DATE(acknowledged_at) DESC
            ''')
            by_date = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_acknowledged': total_acknowledged,
                'current_version_acknowledged': current_version,
                'by_date': by_date
            }
        
        except Exception as e:
            logger.error(f"Error fetching consent statistics: {e}")
            conn.close()
            return None

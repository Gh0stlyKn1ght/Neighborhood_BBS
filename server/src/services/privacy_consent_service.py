"""
Privacy Consent Service - PHASE 4 Week 10

Handles privacy disclaimers and user consent management:
- Privacy bulletin management (create, update, retrieve)
- Consent tracking (recording user acknowledgments)
- Consent verification (checking if user accepted terms)
- Bulletin version management

Author: AI Assistant
Date: 2026
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import json

from models import db

logger = logging.getLogger(__name__)


class PrivacyConsentService:
    """
    Privacy consent management service for Neighborhood BBS.
    
    Handles:
    - Privacy bulletins (disclaimers)
    - Consent acknowledgment tracking
    - Version management
    - Non-identity based consent recording
    """
    
    def __init__(self):
        """Initialize the consent service"""
        self.db = db
    
    def create_bulletin(self, title: str, content: str, created_by: str = 'admin') -> Tuple[bool, str]:
        """
        Create or update privacy bulletin
        
        Args:
            title: Bulletin title
            content: Full text of privacy disclaimer
            created_by: Admin creating the bulletin
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get next version number
            cursor.execute('SELECT MAX(version) FROM privacy_bulletins WHERE is_active = 1')
            result = cursor.fetchone()
            max_version = result[0] if result and result[0] else 0
            next_version = max_version + 1
            
            # Deactivate old bulletins
            cursor.execute('UPDATE privacy_bulletins SET is_active = 0')
            
            # Insert new bulletin
            cursor.execute('''
                INSERT INTO privacy_bulletins (title, content, version, created_by)
                VALUES (?, ?, ?, ?)
            ''', (title, content, next_version, created_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Privacy bulletin created (v{next_version}) by {created_by}")
            return True, f"Privacy bulletin v{next_version} created"
        except Exception as e:
            logger.error(f"Error creating bulletin: {e}")
            return False, f"Error creating bulletin: {str(e)}"
    
    def get_active_bulletin(self) -> Optional[Dict]:
        """Get the currently active privacy bulletin"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, version, created_at
                FROM privacy_bulletins
                WHERE is_active = 1
                ORDER BY version DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Error getting active bulletin: {e}")
            return None
    
    def get_bulletin_history(self, limit: int = 10) -> List[Dict]:
        """Get history of privacy bulletins"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, version, is_active, created_by, created_at
                FROM privacy_bulletins
                ORDER BY version DESC
                LIMIT ?
            ''', (limit,))
            
            bulletins = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return bulletins
        except Exception as e:
            logger.error(f"Error getting bulletin history: {e}")
            return []
    
    def record_consent(self, session_id: str, bulletin_version: int = None,
                      ip_address: str = '', device_info: str = '') -> Tuple[bool, str]:
        """
        Record user consent acknowledgment
        
        Important: Only records the fact of acknowledgment, not user identity
        
        Args:
            session_id: Session identifier (not linked to user)
            bulletin_version: Version of bulletin acknowledged
            ip_address: User's IP (for fraud detection only)
            device_info: User agent string
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Get active bulletin version if not specified
            if bulletin_version is None:
                active = self.get_active_bulletin()
                if not active:
                    return False, "No active privacy bulletin"
                bulletin_version = active['version']
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if already recorded (prevent duplicates)
            cursor.execute('''
                SELECT id FROM privacy_consents
                WHERE session_id = ?
            ''', (session_id,))
            
            if cursor.fetchone():
                # Already recorded, just return success
                conn.close()
                return True, "Consent already recorded for this session"
            
            # Insert consent record
            cursor.execute('''
                INSERT INTO privacy_consents 
                (session_id, bulletin_version, acknowledged, ip_address, device_info)
                VALUES (?, ?, 1, ?, ?)
            ''', (session_id, bulletin_version, ip_address, device_info))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Privacy consent recorded for session {session_id} (v{bulletin_version})")
            return True, "Privacy consent recorded"
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            return False, f"Error recording consent: {str(e)}"
    
    def has_consented(self, session_id: str) -> bool:
        """Check if session has acknowledged privacy terms"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM privacy_consents
                WHERE session_id = ? AND acknowledged = 1
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            return False
    
    def get_consent_stats(self) -> Dict:
        """Get privacy consent statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total consents
            cursor.execute('SELECT COUNT(*) FROM privacy_consents WHERE acknowledged = 1')
            stats['total_consents'] = cursor.fetchone()[0]
            
            # Consents for current bulletin
            active = self.get_active_bulletin()
            if active:
                cursor.execute('''
                    SELECT COUNT(*) FROM privacy_consents
                    WHERE bulletin_version = ? AND acknowledged = 1
                ''', (active['version'],))
                stats['current_version_consents'] = cursor.fetchone()[0]
                stats['current_version'] = active['version']
            
            # Unique sessions
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM privacy_consents')
            stats['unique_sessions'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting consent stats: {e}")
            return {}
    
    def cleanup_old_consents(self, days_old: int = 90) -> int:
        """
        Remove consent records older than specified days
        (GDPR compliance: don't retain consent logs longer than needed)
        
        Args:
            days_old: How old records need to be to delete (default 90 days)
            
        Returns:
            int: Number of records deleted
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM privacy_consents
                WHERE acknowledged_at < datetime('now', '-' || ? || ' days')
            ''', (days_old,))
            
            count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if count > 0:
                logger.info(f"Cleaned up {count} old privacy consent records")
            
            return count
        except Exception as e:
            logger.error(f"Error cleaning up consent records: {e}")
            return 0
    
    def export_consent_summary(self) -> Dict:
        """
        Export consent data for transparency reports
        (Aggregate data only, no individual tracking)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get consent stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_consents,
                    COUNT(DISTINCT DATE(acknowledged_at)) as days_with_consents,
                    MIN(acknowledged_at) as first_consent,
                    MAX(acknowledged_at) as last_consent
                FROM privacy_consents
                WHERE acknowledged = 1
            ''')
            
            row = cursor.fetchone()
            if row:
                summary = {
                    'total_consents': row[0],
                    'days_with_activity': row[1],
                    'first_consent': row[2],
                    'last_consent': row[3]
                }
            else:
                summary = {
                    'total_consents': 0,
                    'days_with_activity': 0
                }
            
            # Get bulletin info
            cursor.execute('''
                SELECT bulletin_version, COUNT(*) as consent_count
                FROM privacy_consents
                WHERE acknowledged = 1
                GROUP BY bulletin_version
                ORDER BY bulletin_version
            ''')
            
            summary['consents_by_version'] = [
                {'version': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return summary
        except Exception as e:
            logger.error(f"Error exporting consent summary: {e}")
            return {}


# Service instance
privacy_consent_service = PrivacyConsentService()

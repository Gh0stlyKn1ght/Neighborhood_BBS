"""
Bulletins service for admin announcements
Handles CRUD operations for bulletins with expiration and pinning
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from models import Database

logger = logging.getLogger(__name__)


class BullletinService:
    """Service for managing admin bulletins/announcements"""
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
    
    def create_bulletin(self, title: str, content: str, created_by: str, 
                       category: str = 'general', is_pinned: bool = False, 
                       expires_at: Optional[str] = None) -> Dict:
        """
        Create a new bulletin
        
        Args:
            title: Bulletin title
            content: Bulletin content/message
            created_by: Admin username who created it
            category: Category (general, maintenance, important, etc.)
            is_pinned: Whether to pin at top
            expires_at: ISO timestamp when bulletin expires (optional)
        
        Returns:
            Created bulletin dict with id, or error dict
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bulletins 
                (title, content, category, is_pinned, created_by, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (title, content, category, is_pinned, created_by, expires_at))
            
            bulletin_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Bulletin created: id={bulletin_id}, title={title}, by={created_by}")
            return self.get_bulletin(bulletin_id)
        
        except Exception as e:
            logger.error(f"Error creating bulletin: {e}")
            return {'error': str(e), 'status': 400}
    
    def get_bulletin(self, bulletin_id: int) -> Dict:
        """Get single bulletin by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, category, is_pinned, created_by, 
                       created_at, updated_at, expires_at, is_active
                FROM bulletins
                WHERE id = ?
            ''', (bulletin_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {'error': 'Bulletin not found', 'status': 404}
            
            return {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3],
                'is_pinned': bool(row[4]),
                'created_by': row[5],
                'created_at': row[6],
                'updated_at': row[7],
                'expires_at': row[8],
                'is_active': bool(row[9])
            }
        
        except Exception as e:
            logger.error(f"Error getting bulletin {bulletin_id}: {e}")
            return {'error': str(e), 'status': 400}
    
    def list_bulletins(self, active_only: bool = True, include_expired: bool = False) -> List[Dict]:
        """
        List all bulletins, optionally filtered
        
        Args:
            active_only: Only return active bulletins
            include_expired: Include expired bulletins
        
        Returns:
            List of bulletin dicts, newest first (pinned first)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, content, category, is_pinned, created_by, 
                       created_at, updated_at, expires_at, is_active
                FROM bulletins
                WHERE 1=1
            '''
            params = []
            
            if active_only:
                query += ' AND is_active = 1'
            
            if not include_expired:
                query += ' AND (expires_at IS NULL OR expires_at > datetime("now"))'
            
            # Order by: pinned first, then newest
            query += ' ORDER BY is_pinned DESC, created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            bulletins = []
            for row in rows:
                bulletins.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'category': row[3],
                    'is_pinned': bool(row[4]),
                    'created_by': row[5],
                    'created_at': row[6],
                    'updated_at': row[7],
                    'expires_at': row[8],
                    'is_active': bool(row[9])
                })
            
            return bulletins
        
        except Exception as e:
            logger.error(f"Error listing bulletins: {e}")
            return []
    
    def update_bulletin(self, bulletin_id: int, **kwargs) -> Dict:
        """
        Update bulletin fields
        
        Args:
            bulletin_id: ID of bulletin to update
            **kwargs: Fields to update (title, content, category, is_pinned, expires_at, is_active)
        
        Returns:
            Updated bulletin dict or error
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build UPDATE query dynamically
            allowed_fields = {'title', 'content', 'category', 'is_pinned', 'expires_at', 'is_active'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                return {'error': 'No valid fields to update', 'status': 400}
            
            update_fields['updated_at'] = datetime.utcnow().isoformat()
            
            set_clause = ', '.join([f'{k} = ?' for k in update_fields.keys()])
            values = list(update_fields.values()) + [bulletin_id]
            
            cursor.execute(f'''
                UPDATE bulletins
                SET {set_clause}
                WHERE id = ?
            ''', values)
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount == 0:
                return {'error': 'Bulletin not found', 'status': 404}
            
            logger.info(f"Bulletin {bulletin_id} updated with fields: {list(update_fields.keys())}")
            return self.get_bulletin(bulletin_id)
        
        except Exception as e:
            logger.error(f"Error updating bulletin {bulletin_id}: {e}")
            return {'error': str(e), 'status': 400}
    
    def delete_bulletin(self, bulletin_id: int) -> Dict:
        """
        Soft delete bulletin (mark as inactive)
        
        Args:
            bulletin_id: ID of bulletin to delete
        
        Returns:
            Success/error dict
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE bulletins
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), bulletin_id))
            
            conn.commit()
            conn.close()
            
            if cursor.rowcount == 0:
                return {'error': 'Bulletin not found', 'status': 404}
            
            logger.info(f"Bulletin {bulletin_id} deleted (soft delete)")
            return {'success': True, 'message': 'Bulletin deleted'}
        
        except Exception as e:
            logger.error(f"Error deleting bulletin {bulletin_id}: {e}")
            return {'error': str(e), 'status': 400}
    
    def pin_bulletin(self, bulletin_id: int) -> Dict:
        """Pin a bulletin to top"""
        return self.update_bulletin(bulletin_id, is_pinned=True)
    
    def unpin_bulletin(self, bulletin_id: int) -> Dict:
        """Unpin a bulletin"""
        return self.update_bulletin(bulletin_id, is_pinned=False)
    
    def get_active_bulletins(self) -> List[Dict]:
        """Get only active, non-expired bulletins (most common use case)"""
        return self.list_bulletins(active_only=True, include_expired=False)

"""
Audit Log Service - PHASE 4 Week 11

Comprehensive logging of all admin actions for accountability:
- Admin action logging (bans, timeouts, device suspensions)
- Bulletin edits, config changes
- Complete audit trail (permanent, never deleted)
- Filtering and search capabilities
- Export for transparency/legal compliance

Action Categories:
- USER_BAN: User suspension/permanent ban
- TIMEOUT: User temporary timeout
- DEVICE_BAN: Device suspension
- CONTENT_BAN: Content removed/flagged
- BULLETIN: Privacy bulletin created/updated
- CONFIG: System configuration changed
- ADMIN: Admin user created/modified
- ACCESS_CONTROL: Access rules modified
- OTHER: Miscellaneous admin action

Author: AI Assistant
Date: 2026
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json

from models import db

logger = logging.getLogger(__name__)


class AuditLogService:
    """
    Admin action audit logging service for Neighborhood BBS.
    
    Features:
    - Comprehensive action logging
    - Never-deleted permanent records
    - Rich filtering and search
    - Export capabilities for compliance
    - Performance optimized with proper indexing
    """
    
    # Action categories
    CATEGORY_USER_BAN = 'USER_BAN'
    CATEGORY_TIMEOUT = 'TIMEOUT'
    CATEGORY_DEVICE_BAN = 'DEVICE_BAN'
    CATEGORY_CONTENT = 'CONTENT'
    CATEGORY_BULLETIN = 'BULLETIN'
    CATEGORY_CONFIG = 'CONFIG'
    CATEGORY_ADMIN = 'ADMIN'
    CATEGORY_ACCESS = 'ACCESS_CONTROL'
    CATEGORY_OTHER = 'OTHER'
    
    # Action statuses
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_PARTIAL = 'partial'
    
    def __init__(self):
        """Initialize the audit log service"""
        self.db = db
    
    def log_action(self, action: str, category: str, admin_user: str,
                  target_user: str = None, target_type: str = None,
                  details: Dict = None, admin_ip: str = '',
                  status: str = STATUS_SUCCESS, notes: str = '') -> Tuple[bool, str]:
        """
        Log an admin action
        
        Args:
            action: Description of the action (e.g., "suspended_user")
            category: Category constant (USER_BAN, CONFIG, etc.)
            admin_user: Admin who performed action
            target_user: User affected (if applicable)
            target_type: Type of target (user, device, config, etc.)
            details: JSON-serializable dict with action details
            admin_ip: Admin's IP address
            status: success, failed, or partial
            notes: Additional notes about the action
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Serialize details
            details_json = json.dumps(details) if details else None
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log 
                (action, action_category, target_user, target_type, details, 
                 admin_user, admin_ip, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (action, category, target_user, target_type, details_json,
                  admin_user, admin_ip, status, notes))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Audit log: {category} - {action} by {admin_user}")
            return True, "Action logged"
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            return False, f"Error logging action: {str(e)}"
    
    def get_recent_actions(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get recent admin actions"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, target_type,
                    admin_user, admin_ip, timestamp, status, notes
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting recent actions: {e}")
            return []
    
    def get_actions_by_admin(self, admin_user: str, limit: int = 50) -> List[Dict]:
        """Get all actions by a specific admin"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, target_type,
                    admin_user, admin_ip, timestamp, status, notes
                FROM audit_log
                WHERE admin_user = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (admin_user, limit))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting admin actions: {e}")
            return []
    
    def get_actions_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get actions by category"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, target_type,
                    admin_user, admin_ip, timestamp, status, notes
                FROM audit_log
                WHERE action_category = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (category, limit))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting category actions: {e}")
            return []
    
    def get_actions_by_target(self, target_user: str, limit: int = 50) -> List[Dict]:
        """Get all actions targeting a specific user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, target_type,
                    admin_user, admin_ip, timestamp, status, notes
                FROM audit_log
                WHERE target_user = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (target_user, limit))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting target actions: {e}")
            return []
    
    def get_actions_by_date_range(self, start_date: datetime, end_date: datetime,
                                  limit: int = 100) -> List[Dict]:
        """Get actions within a date range"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, admin_user, 
                    timestamp, status
                FROM audit_log
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (start_date, end_date, limit))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting date range actions: {e}")
            return []
    
    def get_failed_actions(self, limit: int = 50) -> List[Dict]:
        """Get failed admin actions (for monitoring)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, action, action_category, target_user, target_type,
                    admin_user, admin_ip, timestamp, status, notes
                FROM audit_log
                WHERE status = 'failed'
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            actions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return actions
        except Exception as e:
            logger.error(f"Error getting failed actions: {e}")
            return []
    
    def get_action_count(self, category: str = None) -> int:
        """Get total number of logged actions (optionally by category)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute(
                    'SELECT COUNT(*) FROM audit_log WHERE action_category = ?',
                    (category,)
                )
            else:
                cursor.execute('SELECT COUNT(*) FROM audit_log')
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting action count: {e}")
            return 0
    
    def get_audit_summary(self) -> Dict:
        """Get comprehensive audit log summary"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            summary = {}
            
            # Total actions
            cursor.execute('SELECT COUNT(*) FROM audit_log')
            summary['total_actions'] = cursor.fetchone()[0]
            
            # By category
            cursor.execute('''
                SELECT action_category, COUNT(*) as count
                FROM audit_log
                GROUP BY action_category
                ORDER BY count DESC
            ''')
            summary['by_category'] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            # Failed actions
            cursor.execute(
                "SELECT COUNT(*) FROM audit_log WHERE status = 'failed'"
            )
            summary['failed_actions'] = cursor.fetchone()[0]
            
            # Most active admins
            cursor.execute('''
                SELECT admin_user, COUNT(*) as count
                FROM audit_log
                GROUP BY admin_user
                ORDER BY count DESC
                LIMIT 5
            ''')
            summary['top_admins'] = [
                {'admin': row[0], 'actions': row[1]}
                for row in cursor.fetchall()
            ]
            
            # Date range
            cursor.execute(
                'SELECT MIN(timestamp), MAX(timestamp) FROM audit_log'
            )
            row = cursor.fetchone()
            if row and row[0]:
                summary['period_start'] = row[0]
                summary['period_end'] = row[1]
            
            conn.close()
            return summary
        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")
            return {}
    
    def export_audit_log(self, filters: Dict = None) -> List[Dict]:
        """
        Export audit log (filtered) for transparency/compliance reports
        
        Filters can include:
        - admin_user: Filter by admin
        - category: Filter by action category
        - target_user: Filter by target user
        - status: Filter by status
        - start_date: ISO format date
        - end_date: ISO format date
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM audit_log WHERE 1=1'
            params = []
            
            if filters:
                if filters.get('admin_user'):
                    query += ' AND admin_user = ?'
                    params.append(filters['admin_user'])
                
                if filters.get('category'):
                    query += ' AND action_category = ?'
                    params.append(filters['category'])
                
                if filters.get('target_user'):
                    query += ' AND target_user = ?'
                    params.append(filters['target_user'])
                
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                
                if filters.get('start_date'):
                    query += ' AND timestamp >= ?'
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    query += ' AND timestamp <= ?'
                    params.append(filters['end_date'])
            
            query += ' ORDER BY timestamp DESC'
            
            cursor.execute(query, params)
            records = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return records
        except Exception as e:
            logger.error(f"Error exporting audit log: {e}")
            return []
    
    def get_audit_report(self, admin_user: str = None) -> Dict:
        """Generate audit report for specific admin or all admins"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if admin_user:
                # Single admin report
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_actions,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        MIN(timestamp) as first_action,
                        MAX(timestamp) as last_action
                    FROM audit_log
                    WHERE admin_user = ?
                ''', (admin_user,))
                
                row = cursor.fetchone()
                if row:
                    report = {
                        'admin_user': admin_user,
                        'total_actions': row[0],
                        'successful': row[1] or 0,
                        'failed': row[2] or 0,
                        'first_action': row[3],
                        'last_action': row[4]
                    }
                else:
                    report = {}
            else:
                # Summary report
                report = {
                    'all_admins': True,
                    'summary': self.get_audit_summary()
                }
            
            conn.close()
            return report
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return {}


# Service instance
audit_log_service = AuditLogService()

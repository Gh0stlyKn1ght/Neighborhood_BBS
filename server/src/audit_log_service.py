"""
Audit Log Service - PHASE 4 Week 11
Admin action logging for accountability and compliance
"""

from datetime import datetime
from models import Database
import logging

logger = logging.getLogger(__name__)

class AuditLogService:
    """Tracks admin actions for transparency and compliance"""
    
    def __init__(self):
        self.db = Database()
    
    # Action categories
    CATEGORIES = {
        'user_management': 'User account actions (create, delete, ban, etc)',
        'content': 'Content moderation (remove, flag, etc)',
        'access_control': 'Access control changes (passcode, whitelist, etc)',
        'configuration': 'System configuration changes',
        'security': 'Security & authentication changes',
        'privacy': 'Privacy settings and policy changes',
        'admin': 'Admin panel and dashboard actions'
    }
    
    def log_action(self, action, category='admin', admin_user=None, admin_ip=None, 
                   target_user=None, target_type=None, details={}, status='success', notes=None):
        """
        Log an admin action
        
        Args:
            action: Action description (e.g., 'ban_user', 'delete_post')
            category: Action category from CATEGORIES
            admin_user: Username/ID of admin who performed action
            admin_ip: IP address of admin
            target_user: User affected by action (if applicable)
            target_type: Type of target (user, post, comment, etc)
            details: Dict with additional details
            status: 'success' or 'failed'
            notes: Optional admin notes
        
        Returns:
            int: Audit log ID or None on error
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Serialize details dict to JSON
            import json
            details_json = json.dumps(details) if details else None
            
            cursor.execute('''
                INSERT INTO audit_log
                (action, action_category, target_user, target_type, details, 
                 admin_user, admin_ip, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (action, category, target_user, target_type, details_json,
                  admin_user, admin_ip, status, notes))
            
            conn.commit()
            audit_id = cursor.lastrowid
            
            logger.info(f"Logged action: {action} by {admin_user} (id={audit_id})")
            conn.close()
            return audit_id
        
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            conn.close()
            return None
    
    def get_audit_log(self, limit=100, offset=0, admin_user=None, action_category=None, status=None):
        """
        Retrieve audit log entries
        
        Args:
            limit: Max results to return
            offset: Pagination offset
            admin_user: Filter by admin user
            action_category: Filter by category
            status: Filter by status ('success' or 'failed')
        
        Returns:
            list: Audit log entries
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM audit_log WHERE 1=1'
            params = []
            
            if admin_user:
                query += ' AND admin_user = ?'
                params.append(admin_user)
            
            if action_category:
                query += ' AND action_category = ?'
                params.append(action_category)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                import json
                details = json.loads(row[4]) if row[4] else {}
                
                result.append({
                    'id': row[0],
                    'action': row[1],
                    'category': row[2],
                    'target_user': row[3],
                    'target_type': row[4],
                    'details': details,
                    'admin_user': row[6],
                    'admin_ip': row[7],
                    'timestamp': row[8],
                    'status': row[9],
                    'notes': row[10]
                })
            
            conn.close()
            return result
        
        except Exception as e:
            logger.error(f"Error fetching audit log: {e}")
            conn.close()
            return []
    
    def get_admin_activity_summary(self, admin_user, days=7):
        """
        Get summary of an admin's recent activity
        
        Args:
            admin_user: Admin username
            days: Look back this many days
        
        Returns:
            dict: Activity summary
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Actions by category
            cursor.execute('''
                SELECT action_category, COUNT(*) as count, COUNT(CASE WHEN status='failed' THEN 1 END) as failures
                FROM audit_log
                WHERE admin_user = ? AND timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY action_category
                ORDER BY count DESC
            ''', (admin_user, days))
            
            by_category = [{'category': row[0], 'count': row[1], 'failures': row[2]} 
                          for row in cursor.fetchall()]
            
            # Total summary
            cursor.execute('''
                SELECT COUNT(*), COUNT(CASE WHEN status='failed' THEN 1 END)
                FROM audit_log
                WHERE admin_user = ? AND timestamp >= datetime('now', '-' || ? || ' days')
            ''', (admin_user, days))
            
            summary_row = cursor.fetchone()
            total_actions = summary_row[0] if summary_row else 0
            total_failures = summary_row[1] if summary_row else 0
            
            conn.close()
            
            return {
                'admin_user': admin_user,
                'days': days,
                'total_actions': total_actions,
                'failed_actions': total_failures,
                'by_category': by_category
            }
        
        except Exception as e:
            logger.error(f"Error fetching activity summary: {e}")
            conn.close()
            return None
    
    def get_audit_trail_for_target(self, target_user, target_type='user', limit=50):
        """
        Get complete audit trail for a specific target (user, post, etc)
        
        Args:
            target_user: Target user or identifier
            target_type: Type of target
            limit: Max results
        
        Returns:
            list: Audit entries related to this target
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, action, admin_user, timestamp, status, notes
                FROM audit_log
                WHERE target_user = ? AND target_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (target_user, target_type, limit))
            
            result = [
                {
                    'id': row[0],
                    'action': row[1],
                    'admin_user': row[2],
                    'timestamp': row[3],
                    'status': row[4],
                    'notes': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return result
        
        except Exception as e:
            logger.error(f"Error fetching target audit trail: {e}")
            conn.close()
            return []
    
    def get_system_activity_stats(self, days=7):
        """Get system-wide activity statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Total actions
            cursor.execute('''
                SELECT COUNT(*) FROM audit_log
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            total_actions = cursor.fetchone()[0]
            
            # Actions by admin
            cursor.execute('''
                SELECT admin_user, COUNT(*) FROM audit_log
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY admin_user
                ORDER BY count DESC
            ''', (days,))
            by_admin = [{'admin': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Actions by category
            cursor.execute('''
                SELECT action_category, COUNT(*) FROM audit_log
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY action_category
                ORDER BY count DESC
            ''', (days,))
            by_category = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Success rate
            cursor.execute('''
                SELECT COUNT(CASE WHEN status='success' THEN 1 END) * 100.0 / COUNT(*)
                FROM audit_log
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            success_rate = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'period_days': days,
                'total_actions': total_actions,
                'success_rate': round(success_rate, 2),
                'by_admin': by_admin,
                'by_category': by_category
            }
        
        except Exception as e:
            logger.error(f"Error fetching system stats: {e}")
            conn.close()
            return None

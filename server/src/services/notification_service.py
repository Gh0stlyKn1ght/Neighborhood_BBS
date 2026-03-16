"""
Notification Service for Admin Dashboard
Manages real-time notifications for admins about moderation events and system alerts

Phase 4 Week 14
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'neighborhood.db'


class NotificationType(Enum):
    """Notification types"""
    VIOLATION = "violation"           # New content violation detected
    MODERATION = "moderation"         # Moderation action taken (mute, ban)
    APPROVAL_REQUEST = "approval"     # New access approval request
    ADMIN_ACTION = "admin_action"     # Admin created/modified
    SYSTEM_ALERT = "system_alert"     # System warnings/errors
    AUDIT_IMPORTANT = "audit_log"     # Important audit events


class NotificationSeverity(Enum):
    """Notification severity levels"""
    INFO = "info"          # Informational
    WARNING = "warning"    # Warning but no action needed
    CRITICAL = "critical"  # Requires attention


class NotificationService:
    """Service for managing admin notifications"""
    
    def __init__(self, db_path: str = None):
        """Initialize notification service"""
        self.db_path = db_path or str(DB_PATH)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_notifications_table(self):
        """Initialize notifications table if it doesn't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT UNIQUE NOT NULL,
                    admin_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    related_resource_type TEXT,
                    related_resource_id TEXT,
                    data JSON,
                    read BOOLEAN DEFAULT 0,
                    read_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES admin_users(id)
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_notifications_admin_read 
                ON admin_notifications(admin_id, read, created_at DESC)
            ''')
            
            conn.commit()
            logger.info("Notifications table initialized")
        finally:
            conn.close()
    
    # ========================================================================
    # NOTIFICATION CREATION
    # ========================================================================
    
    def create_notification(
        self,
        admin_id: str,
        notification_type: str,
        title: str,
        message: str,
        severity: str = "info",
        related_resource_type: str = None,
        related_resource_id: str = None,
        data: Dict = None,
        expires_in_hours: int = 24
    ) -> str:
        """
        Create a new notification
        
        Args:
            admin_id: Admin user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            severity: Severity level (info, warning, critical)
            related_resource_type: Type of resource (admin, violation, etc)
            related_resource_id: ID of related resource
            data: Additional data as JSON
            expires_in_hours: Hours until notification expires (default 24)
        
        Returns:
            notification_id: The created notification ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            import secrets
            notification_id = secrets.token_hex(16)
            
            expires_at = (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat()
            
            cursor.execute('''
                INSERT INTO admin_notifications (
                    notification_id, admin_id, notification_type, title, message,
                    severity, related_resource_type, related_resource_id, 
                    data, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                notification_id, admin_id, notification_type, title, message,
                severity, related_resource_type, related_resource_id,
                json.dumps(data) if data else None, expires_at
            ))
            
            conn.commit()
            logger.info(f"Created notification {notification_id} for admin {admin_id}")
            return notification_id
        
        finally:
            conn.close()
    
    def create_violation_notification(self, admin_id: str, violation_context: Dict) -> str:
        """Create notification for a new violation"""
        return self.create_notification(
            admin_id=admin_id,
            notification_type=NotificationType.VIOLATION.value,
            title=f"New Content Violation",
            message=f"Violation detected: {violation_context.get('violation_type', 'unknown')}",
            severity=NotificationSeverity.WARNING.value,
            related_resource_type="violation",
            related_resource_id=violation_context.get('violation_id'),
            data=violation_context
        )
    
    def create_moderation_notification(self, admin_id: str, action_context: Dict) -> str:
        """Create notification for a moderation action"""
        action_type = action_context.get('action_type', 'unknown')
        return self.create_notification(
            admin_id=admin_id,
            notification_type=NotificationType.MODERATION.value,
            title=f"Moderation Action: {action_type}",
            message=action_context.get('description', 'A moderation action was taken'),
            severity=NotificationSeverity.INFO.value,
            related_resource_type="moderation",
            related_resource_id=action_context.get('action_id'),
            data=action_context
        )
    
    def create_approval_notification(self, admin_id: str, approval_context: Dict) -> str:
        """Create notification for a new approval request"""
        return self.create_notification(
            admin_id=admin_id,
            notification_type=NotificationType.APPROVAL_REQUEST.value,
            title="New Access Approval Request",
            message=f"User {approval_context.get('username', 'unknown')} is requesting access",
            severity=NotificationSeverity.WARNING.value,
            related_resource_type="approval",
            related_resource_id=approval_context.get('approval_id'),
            data=approval_context
        )
    
    def create_system_alert(self, admin_id: str, alert_context: Dict) -> str:
        """Create system alert notification"""
        severity = alert_context.get('severity', NotificationSeverity.WARNING.value)
        return self.create_notification(
            admin_id=admin_id,
            notification_type=NotificationType.SYSTEM_ALERT.value,
            title=alert_context.get('title', 'System Alert'),
            message=alert_context.get('message', 'A system alert was issued'),
            severity=severity,
            data=alert_context
        )
    
    # ========================================================================
    # NOTIFICATION RETRIEVAL
    # ========================================================================
    
    def get_unread_count(self, admin_id: str) -> int:
        """Get count of unread notifications for admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM admin_notifications
                WHERE admin_id = ? AND read = 0 AND (expires_at IS NULL OR expires_at > ?)
            ''', (admin_id, datetime.utcnow().isoformat()))
            
            return cursor.fetchone()['count']
        finally:
            conn.close()
    
    def get_notifications(
        self,
        admin_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict]:
        """
        Get notifications for admin
        
        Args:
            admin_id: Admin user ID
            limit: Maximum notifications to return (max 500)
            offset: Pagination offset
            unread_only: Only get unread notifications
        
        Returns:
            List of notification dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            limit = min(limit, 500)
            
            where_clause = "WHERE admin_id = ? AND (expires_at IS NULL OR expires_at > ?)"
            params = [admin_id, datetime.utcnow().isoformat()]
            
            if unread_only:
                where_clause += " AND read = 0"
            
            where_clause += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(f'''
                SELECT 
                    id, notification_id, admin_id, notification_type, title, message,
                    severity, related_resource_type, related_resource_id,
                    data, read, read_at, created_at
                FROM admin_notifications
                {where_clause}
            ''', params)
            
            rows = cursor.fetchall()
            notifications = []
            
            for row in rows:
                notif = dict(row)
                if notif['data']:
                    notif['data'] = json.loads(notif['data'])
                notifications.append(notif)
            
            return notifications
        
        finally:
            conn.close()
    
    def get_unread_notifications(self, admin_id: str, limit: int = 50) -> List[Dict]:
        """Get unread notifications for admin"""
        return self.get_notifications(admin_id, limit=limit, unread_only=True)
    
    def get_notification(self, notification_id: str, admin_id: str = None) -> Optional[Dict]:
        """Get a specific notification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if admin_id:
                cursor.execute('''
                    SELECT * FROM admin_notifications
                    WHERE notification_id = ? AND admin_id = ?
                ''', (notification_id, admin_id))
            else:
                cursor.execute('''
                    SELECT * FROM admin_notifications
                    WHERE notification_id = ?
                ''', (notification_id,))
            
            row = cursor.fetchone()
            if row:
                notif = dict(row)
                if notif['data']:
                    notif['data'] = json.loads(notif['data'])
                return notif
            
            return None
        finally:
            conn.close()
    
    # ========================================================================
    # NOTIFICATION MANAGEMENT
    # ========================================================================
    
    def mark_as_read(self, notification_id: str, admin_id: str) -> bool:
        """Mark notification as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE admin_notifications
                SET read = 1, read_at = ?
                WHERE notification_id = ? AND admin_id = ?
            ''', (datetime.utcnow().isoformat(), notification_id, admin_id))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def mark_all_as_read(self, admin_id: str) -> int:
        """Mark all notifications as read for admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE admin_notifications
                SET read = 1, read_at = ?
                WHERE admin_id = ? AND read = 0
            ''', (datetime.utcnow().isoformat(), admin_id))
            
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    def delete_notification(self, notification_id: str, admin_id: str) -> bool:
        """Delete a notification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM admin_notifications
                WHERE notification_id = ? AND admin_id = ?
            ''', (notification_id, admin_id))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def clear_old_notifications(self, days: int = 7) -> int:
        """Delete notifications older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                DELETE FROM admin_notifications
                WHERE created_at < ? OR (expires_at IS NOT NULL AND expires_at < ?)
            ''', (cutoff_date, datetime.utcnow().isoformat()))
            
            conn.commit()
            logger.info(f"Cleared {cursor.rowcount} old notifications")
            return cursor.rowcount
        finally:
            conn.close()
    
    # ========================================================================
    # NOTIFICATION STATISTICS
    # ========================================================================
    
    def get_notification_stats(self, admin_id: str = None) -> Dict[str, Any]:
        """Get notification statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if admin_id:
                # Stats for specific admin
                cursor.execute('''
                    SELECT COUNT(*) as total, SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread
                    FROM admin_notifications
                    WHERE admin_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ''', (admin_id, datetime.utcnow().isoformat()))
            else:
                # System-wide stats
                cursor.execute('''
                    SELECT COUNT(*) as total, SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread
                    FROM admin_notifications
                    WHERE expires_at IS NULL OR expires_at > ?
                ''', (datetime.utcnow().isoformat(),))
            
            row = cursor.fetchone()
            
            return {
                'total': row['total'] or 0,
                'unread': row['unread'] or 0,
                'read': (row['total'] or 0) - (row['unread'] or 0)
            }
        finally:
            conn.close()
    
    def get_notification_types_summary(self, admin_id: str) -> Dict[str, int]:
        """Get count of notifications by type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT notification_type, COUNT(*) as count
                FROM admin_notifications
                WHERE admin_id = ? AND (expires_at IS NULL OR expires_at > ?)
                GROUP BY notification_type
            ''', (admin_id, datetime.utcnow().isoformat()))
            
            return {row['notification_type']: row['count'] for row in cursor.fetchall()}
        finally:
            conn.close()

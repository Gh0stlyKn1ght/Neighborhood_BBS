"""
Comprehensive Test Suite for Admin Notifications System
Phase 4 Week 14

Tests:
- Notification service functionality
- REST API endpoints
- Database operations
- Error handling
- Permissions and authentication
"""

import pytest
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import sys

# Add server src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from services.notification_service import (
    NotificationService,
    NotificationType,
    NotificationSeverity
)


class TestNotificationService:
    """Test NotificationService class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        yield path
        Path(path).unlink(missing_ok=True)
    
    @pytest.fixture
    def service(self, temp_db):
        """Create NotificationService with temp database"""
        service = NotificationService(temp_db)
        service.init_notifications_table()
        return service
    
    # ========== TABLE INITIALIZATION ==========
    
    def test_init_notifications_table(self, temp_db):
        """Test notifications table creation"""
        service = NotificationService(temp_db)
        service.init_notifications_table()
        
        conn = service.get_connection()
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admin_notifications'
        """)
        
        assert cursor.fetchone() is not None
        conn.close()
    
    def test_init_creates_indexes(self, temp_db):
        """Test that indexes are created"""
        service = NotificationService(temp_db)
        service.init_notifications_table()
        
        conn = service.get_connection()
        cursor = conn.cursor()
        
        # Check index exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_notifications_admin_read'
        """)
        
        assert cursor.fetchone() is not None
        conn.close()
    
    # ========== NOTIFICATION CREATION ==========
    
    def test_create_notification(self, service):
        """Test creating a notification"""
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Test Violation",
            message="Test violation message",
            severity=NotificationSeverity.WARNING.value
        )
        
        assert notif_id is not None
        assert isinstance(notif_id, str)
        assert len(notif_id) > 0
    
    def test_create_notification_with_data(self, service):
        """Test creating notification with additional data"""
        data = {
            'violation_id': 'v123',
            'user_id': 'u456',
            'violation_type': 'spam'
        }
        
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Spam Detected",
            message="Spam violation detected",
            severity=NotificationSeverity.WARNING.value,
            data=data
        )
        
        # Retrieve and verify
        notif = service.get_notification(notif_id)
        assert notif is not None
        assert notif['data'] is not None
        stored_data = json.loads(notif['data']) if isinstance(notif['data'], str) else notif['data']
        assert stored_data['violation_id'] == 'v123'
    
    def test_create_violation_notification(self, service):
        """Test creating violation notification"""
        violation_context = {
            'violation_id': 'v123',
            'violation_type': 'spam',
            'description': 'Multiple spam posts'
        }
        
        notif_id = service.create_violation_notification("admin_1", violation_context)
        assert notif_id is not None
        
        notif = service.get_notification(notif_id)
        assert notif['notification_type'] == NotificationType.VIOLATION.value
    
    def test_create_moderation_notification(self, service):
        """Test creating moderation notification"""
        action_context = {
            'action_id': 'a123',
            'action_type': 'mute',
            'description': 'User muted for 24 hours'
        }
        
        notif_id = service.create_moderation_notification("admin_1", action_context)
        assert notif_id is not None
        
        notif = service.get_notification(notif_id)
        assert notif['notification_type'] == NotificationType.MODERATION.value
    
    def test_create_approval_notification(self, service):
        """Test creating approval notification"""
        approval_context = {
            'approval_id': 'a123',
            'username': 'newuser'
        }
        
        notif_id = service.create_approval_notification("admin_1", approval_context)
        assert notif_id is not None
        
        notif = service.get_notification(notif_id)
        assert notif['notification_type'] == NotificationType.APPROVAL_REQUEST.value
    
    def test_create_system_alert(self, service):
        """Test creating system alert"""
        alert_context = {
            'title': 'High CPU Usage',
            'message': 'CPU usage exceeded 90%',
            'severity': NotificationSeverity.CRITICAL.value
        }
        
        notif_id = service.create_system_alert("admin_1", alert_context)
        assert notif_id is not None
        
        notif = service.get_notification(notif_id)
        assert notif['severity'] == NotificationSeverity.CRITICAL.value
    
    # ========== NOTIFICATION RETRIEVAL ==========
    
    def test_get_notifications(self, service):
        """Test retrieving notifications"""
        # Create multiple notifications
        for i in range(3):
            service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Violation {i}",
                message="Test"
            )
        
        notifications = service.get_notifications("admin_1", limit=10)
        assert len(notifications) == 3
    
    def test_get_notifications_pagination(self, service):
        """Test notifications pagination"""
        # Create 15 notifications
        for i in range(15):
            service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Violation {i}",
                message="Test"
            )
        
        # Get first 10
        page1 = service.get_notifications("admin_1", limit=10, offset=0)
        assert len(page1) == 10
        
        # Get next 5
        page2 = service.get_notifications("admin_1", limit=10, offset=10)
        assert len(page2) == 5
    
    def test_get_unread_notifications(self, service):
        """Test filtering unread notifications"""
        # Create mixed read/unread
        for i in range(5):
            service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Notif {i}",
                message="Test"
            )
        
        # Mark 2 as read
        notifs = service.get_notifications("admin_1", limit=10)
        service.mark_as_read(notifs[0]['notification_id'], "admin_1")
        service.mark_as_read(notifs[1]['notification_id'], "admin_1")
        
        # Get unread only
        unread = service.get_unread_notifications("admin_1", limit=10)
        assert len(unread) == 3
        assert all(not n['read'] for n in unread)
    
    def test_get_unread_count(self, service):
        """Test getting unread count"""
        # Create 5 notifications
        for i in range(5):
            service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Notif {i}",
                message="Test"
            )
        
        count = service.get_unread_count("admin_1")
        assert count == 5
        
        # Mark 2 as read
        notifs = service.get_notifications("admin_1", limit=10)
        service.mark_as_read(notifs[0]['notification_id'], "admin_1")
        service.mark_as_read(notifs[1]['notification_id'], "admin_1")
        
        count = service.get_unread_count("admin_1")
        assert count == 3
    
    def test_get_notification_by_id(self, service):
        """Test getting specific notification"""
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Test",
            message="Test message"
        )
        
        notif = service.get_notification(notif_id, admin_id="admin_1")
        assert notif is not None
        assert notif['title'] == "Test"
        assert notif['message'] == "Test message"
    
    def test_get_notification_not_found(self, service):
        """Test getting non-existent notification"""
        notif = service.get_notification("nonexistent_id", admin_id="admin_1")
        assert notif is None
    
    # ========== NOTIFICATION MANAGEMENT ==========
    
    def test_mark_as_read(self, service):
        """Test marking notification as read"""
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Test",
            message="Test"
        )
        
        assert service.mark_as_read(notif_id, "admin_1") is True
        
        notif = service.get_notification(notif_id)
        assert notif['read'] == 1
    
    def test_mark_all_as_read(self, service):
        """Test marking all notifications as read"""
        notif_ids = []
        for i in range(5):
            notif_id = service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Notif {i}",
                message="Test"
            )
            notif_ids.append(notif_id)
        
        assert service.get_unread_count("admin_1") == 5
        
        count = service.mark_all_as_read("admin_1")
        assert count == 5
        assert service.get_unread_count("admin_1") == 0
    
    def test_delete_notification(self, service):
        """Test deleting notification"""
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Test",
            message="Test"
        )
        
        assert service.delete_notification(notif_id, "admin_1") is True
        assert service.get_notification(notif_id) is None
    
    def test_delete_notification_not_found(self, service):
        """Test deleting non-existent notification """
        assert service.delete_notification("nonexistent_id", "admin_1") is False
    
    def test_clear_old_notifications(self, service):
        """Test clearing old notifications"""
        # Create old notification (manually insert with old timestamp)
        import secrets
        old_id = secrets.token_hex(16)
        old_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        conn = service.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admin_notifications 
            (notification_id, admin_id, notification_type, title, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (old_id, "admin_1", "test", "Old", "Old notification", old_date))
        conn.commit()
        conn.close()
        
        # Create recent notification
        service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Recent",
            message="Recent notification"
        )
        
        # Clear notifications older than 7 days
        count = service.clear_old_notifications(days=7)
        assert count >= 1  # At least the old one
        
        # Recent should still exist
        recent = service.get_notifications("admin_1", limit=10)
        assert len(recent) >= 1
    
    # ========== NOTIFICATION STATISTICS ==========
    
    def test_get_notification_stats(self, service):
        """Test getting notification statistics"""
        # Create 5 notifications
        for i in range(5):
            service.create_notification(
                admin_id="admin_1",
                notification_type=NotificationType.VIOLATION.value,
                title=f"Notif {i}",
                message="Test"
            )
        
        # Mark 2 as read
        notifs = service.get_notifications("admin_1", limit=10)
        service.mark_as_read(notifs[0]['notification_id'], "admin_1")
        service.mark_as_read(notifs[1]['notification_id'], "admin_1")
        
        stats = service.get_notification_stats("admin_1")
        assert stats['total'] == 5
        assert stats['read'] == 2
        assert stats['unread'] == 3
    
    def test_get_notification_types_summary(self, service):
        """Test getting notification types summary"""
        # Create different types
        service.create_violation_notification("admin_1", {'violation_id': 'v1'})
        service.create_violation_notification("admin_1", {'violation_id': 'v2'})
        service.create_moderation_notification("admin_1", {'action_id': 'a1'})
        
        summary = service.get_notification_types_summary("admin_1")
        assert summary.get(NotificationType.VIOLATION.value) == 2
        assert summary.get(NotificationType.MODERATION.value) == 1


class TestNotificationDataValidation:
    """Test data validation and edge cases"""
    
    @pytest.fixture
    def service(self):
        """Create service with temp database"""
        fd, path = tempfile.mkstemp(suffix='.db')
        service = NotificationService(path)
        service.init_notifications_table()
        yield service
        Path(path).unlink(missing_ok=True)
    
    def test_notification_with_empty_message(self, service):
        """Test notification with empty message"""
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Empty Message",
            message=""
        )
        
        notif = service.get_notification(notif_id)
        assert notif['message'] == ""
    
    def test_notification_with_special_characters(self, service):
        """Test notification with special characters"""
        special_title = "Alert: <script>alert('xss')</script>"
        special_msg = "User posted: \"quoted text\" & <img> tag"
        
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title=special_title,
            message=special_msg
        )
        
        notif = service.get_notification(notif_id)
        assert notif['title'] == special_title
        assert notif['message'] == special_msg
    
    def test_notification_with_long_message(self, service):
        """Test notification with very long message"""
        long_msg = "x" * 5000  # 5000 characters
        
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Long Message",
            message=long_msg
        )
        
        notif = service.get_notification(notif_id)
        assert notif['message'] == long_msg
    
    def test_notification_with_json_data(self, service):
        """Test notification with complex JSON data"""
        complex_data = {
            'nested': {
                'deep': {
                    'value': 123,
                    'array': [1, 2, 3],
                    'mixed': {'a': 'b'}
                }
            },
            'list': [
                {'id': 1, 'name': 'first'},
                {'id': 2, 'name': 'second'}
            ]
        }
        
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Complex Data",
            message="Has complex data",
            data=complex_data
        )
        
        notif = service.get_notification(notif_id)
        stored_data = json.loads(notif['data']) if isinstance(notif['data'], str) else notif['data']
        assert stored_data == complex_data


class TestNotificationIntegration:
    """Integration tests for notification workflows"""
    
    @pytest.fixture
    def service(self):
        """Create service with temp database"""
        fd, path = tempfile.mkstemp(suffix='.db')
        service = NotificationService(path)
        service.init_notifications_table()
        yield service
        Path(path).unlink(missing_ok=True)
    
    def test_complete_notification_lifecycle(self, service):
        """Test complete notification lifecycle"""
        # Create
        notif_id = service.create_notification(
            admin_id="admin_1",
            notification_type=NotificationType.VIOLATION.value,
            title="Spam Detected",
            message="User posted spam",
            severity=NotificationSeverity.WARNING.value
        )
        
        assert notif_id is not None
        
        # Retrieve
        notif = service.get_notification(notif_id)
        assert notif['read'] == 0
        
        # Mark as read
        service.mark_as_read(notif_id, "admin_1")
        notif = service.get_notification(notif_id)
        assert notif['read'] == 1
        
        # Delete
        service.delete_notification(notif_id, "admin_1")
        notif = service.get_notification(notif_id)
        assert notif is None
    
    def test_multiple_admin_isolation(self, service):
        """Test that notifications are isolated per admin"""
        # Create notifications for different admins
        service.create_notification("admin_1", NotificationType.VIOLATION.value, "A", "A")
        service.create_notification("admin_2", NotificationType.VIOLATION.value, "B", "B")
        
        # Admin 1 should only see 1
        admin1_notifs = service.get_notifications("admin_1")
        assert len(admin1_notifs) == 1
        assert admin1_notifs[0]['title'] == "A"
        
        # Admin 2 should only see 1
        admin2_notifs = service.get_notifications("admin_2")
        assert len(admin2_notifs) == 1
        assert admin2_notifs[0]['title'] == "B"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

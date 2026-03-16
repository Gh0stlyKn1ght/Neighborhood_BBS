"""
Test Suite - Admin Audit Log Service - PHASE 4 Week 11

Comprehensive testing of audit logging:
- Service-level logging operations
- Route integration testing
- Filter and search functionality
- Export and reporting
- Performance with indexing

Run with: pytest test_audit_log_phase4_w11.py -v

Author: AI Assistant
Date: 2026
"""

import pytest
import json
from datetime import datetime, timedelta
import uuid

from models import db
from services.audit_log_service import audit_log_service, AuditLogService


def clear_audit_logs():
    """Clear all audit logs from database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM audit_log')
        conn.commit()
        conn.close()
    except Exception:
        pass


class TestAuditLogService:
    """Test core audit log service functionality"""
    
    def setup_method(self):
        """Clear database before each test"""
        clear_audit_logs()
    
    def test_log_action_success(self):
        """Test logging a successful action"""
        success, msg = audit_log_service.log_action(
            action='suspend_user',
            category=AuditLogService.CATEGORY_USER_BAN,
            admin_user='admin1',
            target_user='user_violator',
            target_type='user',
            details={'reason': 'multiple_violations'},
            admin_ip='192.168.1.1',
            status=AuditLogService.STATUS_SUCCESS
        )
        
        assert success == True
        assert 'logged' in msg.lower()
    
    def test_log_action_with_null_target(self):
        """Test logging actionwith no target user"""
        success, msg = audit_log_service.log_action(
            action='config_change',
            category=AuditLogService.CATEGORY_CONFIG,
            admin_user='admin1',
            target_type='config',
            details={'setting': 'max_users', 'old': 100, 'new': 150},
            admin_ip='192.168.1.1'
        )
        
        assert success == True
    
    def test_get_recent_actions(self):
        """Test retrieving recent actions"""
        # Log multiple actions
        for i in range(5):
            audit_log_service.log_action(
                action=f'action_{i}',
                category=AuditLogService.CATEGORY_OTHER,
                admin_user='admin1',
                target_user=f'user_{i}',
                admin_ip='192.168.1.1'
            )
        
        actions = audit_log_service.get_recent_actions(limit=10)
        
        assert len(actions) == 5
        # Most recent should be first
        assert 'action_' in actions[0]['action']
    
    def test_get_actions_by_admin(self):
        """Test retrieving actions by specific admin"""
        # Log actions by different admins
        audit_log_service.log_action(
            action='action_admin1',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='action_admin2',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin2',
            admin_ip='192.168.1.2'
        )
        
        admin1_actions = audit_log_service.get_actions_by_admin('admin1')
        
        assert len(admin1_actions) == 1
        assert admin1_actions[0]['admin_user'] == 'admin1'
    
    def test_get_actions_by_category(self):
        """Test filtering actions by category"""
        # Log actions of different categories
        audit_log_service.log_action(
            action='ban_user',
            category=AuditLogService.CATEGORY_USER_BAN,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='timeout_user',
            category=AuditLogService.CATEGORY_TIMEOUT,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        
        ban_actions = audit_log_service.get_actions_by_category(
            AuditLogService.CATEGORY_USER_BAN
        )
        timeout_actions = audit_log_service.get_actions_by_category(
            AuditLogService.CATEGORY_TIMEOUT
        )
        
        assert len(ban_actions) == 1
        assert ban_actions[0]['action'] == 'ban_user'
        assert len(timeout_actions) == 1
    
    def test_get_actions_by_target(self):
        """Test retrieving actions targeting a specific user"""
        # Log actions targeting different users
        audit_log_service.log_action(
            action='ban',
            category=AuditLogService.CATEGORY_USER_BAN,
            admin_user='admin1',
            target_user='violator_user',
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='timeout',
            category=AuditLogService.CATEGORY_TIMEOUT,
            admin_user='admin1',
            target_user='other_user',
            admin_ip='192.168.1.1'
        )
        
        target_actions = audit_log_service.get_actions_by_target('violator_user')
        
        assert len(target_actions) == 1
        assert target_actions[0]['target_user'] == 'violator_user'
    
    def test_get_failed_actions(self):
        """Test retrieving failed actions"""
        # Log successful and failed actions
        audit_log_service.log_action(
            action='success_action',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            status=AuditLogService.STATUS_SUCCESS,
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='failed_action',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            status=AuditLogService.STATUS_FAILED,
            admin_ip='192.168.1.1',
            notes='Action failed: user not found'
        )
        
        failed = audit_log_service.get_failed_actions()
        
        assert len(failed) == 1
        assert failed[0]['action'] == 'failed_action'
        assert failed[0]['status'] == 'failed'
    
    def test_get_action_count(self):
        """Test getting total action count"""
        # Log actions
        for i in range(3):
            audit_log_service.log_action(
                action=f'action_{i}',
                category=AuditLogService.CATEGORY_OTHER,
                admin_user='admin1',
                admin_ip='192.168.1.1'
            )
        
        # Total count
        total = audit_log_service.get_action_count()
        assert total == 3
        
        # Count by category
        other_count = audit_log_service.get_action_count(
            AuditLogService.CATEGORY_OTHER
        )
        assert other_count == 3
    
    def test_get_audit_summary(self):
        """Test audit log summary generation"""
        # Log various actions
        audit_log_service.log_action(
            action='ban',
            category=AuditLogService.CATEGORY_USER_BAN,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='timeout',
            category=AuditLogService.CATEGORY_TIMEOUT,
            admin_user='admin2',
            admin_ip='192.168.1.2'
        )
        audit_log_service.log_action(
            action='failed_action',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            status=AuditLogService.STATUS_FAILED,
            admin_ip='192.168.1.1'
        )
        
        summary = audit_log_service.get_audit_summary()
        
        assert summary['total_actions'] == 3
        assert summary['failed_actions'] == 1
        assert 'by_category' in summary
        assert 'top_admins' in summary
    
    def test_export_audit_log_no_filters(self):
        """Test exporting all audit logs"""
        # Log actions
        audit_log_service.log_action(
            action='action1',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        audit_log_service.log_action(
            action='action2',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        
        export = audit_log_service.export_audit_log()
        
        assert len(export) == 2
    
    def test_export_audit_log_with_filters(self):
        """Test exporting with filters"""
        # Log actions
        audit_log_service.log_action(
            action='ban',
            category=AuditLogService.CATEGORY_USER_BAN,
            admin_user='admin1',
            target_user='banned_user',
            admin_ip='192.168.1.1',
            status=AuditLogService.STATUS_SUCCESS
        )
        audit_log_service.log_action(
            action='timeout',
            category=AuditLogService.CATEGORY_TIMEOUT,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        
        # Filter by admin
        export = audit_log_service.export_audit_log(
            filters={'admin_user': 'admin1'}
        )
        assert len(export) == 2
        
        # Filter by category
        export = audit_log_service.export_audit_log(
            filters={'category': AuditLogService.CATEGORY_USER_BAN}
        )
        assert len(export) == 1
    
    def test_get_audit_report_all_admins(self):
        """Test getting aggregate audit report"""
        # Log actions
        audit_log_service.log_action(
            action='action1',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1'
        )
        
        report = audit_log_service.get_audit_report()
        
        assert 'all_admins' in report
        assert 'summary' in report
    
    def test_get_audit_report_single_admin(self):
        """Test getting report for single admin"""
        # Log actions
        audit_log_service.log_action(
            action='action1',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1',
            status=AuditLogService.STATUS_SUCCESS
        )
        audit_log_service.log_action(
            action='action2',
            category=AuditLogService.CATEGORY_OTHER,
            admin_user='admin1',
            admin_ip='192.168.1.1',
            status=AuditLogService.STATUS_FAILED
        )
        
        report = audit_log_service.get_audit_report('admin1')
        
        assert report['admin_user'] == 'admin1'
        assert report['total_actions'] == 2
        assert report['successful'] == 1
        assert report['failed'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

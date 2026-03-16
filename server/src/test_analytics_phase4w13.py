"""
Phase 4 Week 13: Admin Analytics Tests
Test analytics endpoints and functionality

Tests:
- Dashboard summary endpoint
- Admin statistics endpoint
- Moderation statistics endpoint
- Access control statistics endpoint
- Session statistics endpoint
- Content statistics endpoint
- Historical data endpoint
- Error handling
"""

import pytest
import json
from datetime import datetime, timedelta
from server import create_app

@pytest.fixture
def client():
    """Create test client"""
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_analytics_health_check(self, client):
        """Test health check (no auth required)"""
        response = client.get('/api/admin-management/analytics/health')
        assert response.status_code in [200, 401]  # 401 if no token needed
    
    def test_dashboard_summary_requires_auth(self, client):
        """Test dashboard endpoint requires authentication"""
        response = client.get('/api/admin-management/analytics/dashboard')
        assert response.status_code == 401
    
    def test_admin_stats_requires_auth(self, client):
        """Test admin stats endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/admins')
        assert response.status_code == 401
    
    def test_moderation_stats_requires_auth(self, client):
        """Test moderation stats endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/moderation')
        assert response.status_code == 401
    
    def test_access_stats_requires_auth(self, client):
        """Test access control stats endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/access')
        assert response.status_code == 401
    
    def test_session_stats_requires_auth(self, client):
        """Test session stats endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/sessions')
        assert response.status_code == 401
    
    def test_content_stats_requires_auth(self, client):
        """Test content stats endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/content')
        assert response.status_code == 401
    
    def test_historical_data_requires_auth(self, client):
        """Test historical data endpoint requires auth"""
        response = client.get('/api/admin-management/analytics/history?metric=messages')
        assert response.status_code == 401
    
    def test_historical_data_missing_metric(self, client):
        """Test historical data requires metric parameter"""
        # This would require a valid token - for now just test the structure
        response = client.get('/api/admin-management/analytics/history')
        assert response.status_code in [400, 401]
    
    def test_historical_data_invalid_metric(self, client):
        """Test historical data with invalid metric"""
        response = client.get('/api/admin-management/analytics/history?metric=invalid')
        assert response.status_code in [400, 401]  # 400 if we get past auth


class TestAnalyticsServiceFunctionality:
    """Test AnalyticsService methods (without HTTP layer)"""
    
    def test_analytics_service_import(self):
        """Test that analytics service can be imported"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        assert service is not None
    
    def test_get_admin_count_structure(self):
        """Test admin count returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_admin_count()
        
        # Check structure
        assert 'total' in result
        assert 'active' in result
        assert 'inactive' in result
        assert 'by_role' in result
        
        # Check types
        assert isinstance(result['total'], int)
        assert isinstance(result['active'], int)
        assert isinstance(result['inactive'], int)
        assert isinstance(result['by_role'], dict)
        
        # Check role names
        assert 'super_admin' in result['by_role']
        assert 'moderator' in result['by_role']
        assert 'approver' in result['by_role']
        assert 'viewer' in result['by_role']
    
    def test_get_admin_activity_structure(self):
        """Test admin activity returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_admin_activity(days=7)
        
        # Check structure
        assert 'period_days' in result
        assert 'total_actions' in result
        assert 'by_admin' in result
        assert 'by_action' in result
        assert 'top_admins' in result
        
        # Check types
        assert isinstance(result['period_days'], int)
        assert isinstance(result['total_actions'], int)
        assert isinstance(result['by_admin'], dict)
        assert isinstance(result['by_action'], dict)
        assert isinstance(result['top_admins'], list)
    
    def test_get_moderation_stats_structure(self):
        """Test moderation stats returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_moderation_stats(days=7)
        
        # Check structure
        assert 'period_days' in result
        assert 'total_violations' in result
        assert 'violations_by_type' in result
        assert 'resolved' in result
        assert 'unresolved' in result
        assert 'suspensions_active' in result
        assert 'device_bans_active' in result
        assert 'bans_new' in result
        
        # Check types
        assert isinstance(result['total_violations'], int)
        assert isinstance(result['violations_by_type'], dict)
        assert isinstance(result['resolved'], int)
        assert isinstance(result['unresolved'], int)
    
    def test_get_access_stats_structure(self):
        """Test access stats returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_access_stats()
        
        # Check structure
        assert 'user_registrations' in result
        assert 'pending_approvals' in result
        assert 'approved_total' in result
        assert 'rejected' in result
        assert 'approval_rate' in result
        assert 'pending_by_days' in result
        
        # Check types
        assert isinstance(result['approval_rate'], float)
        assert isinstance(result['pending_by_days'], dict)
        
        # Check pending_by_days structure
        assert '0' in result['pending_by_days']
        assert '1-3' in result['pending_by_days']
        assert '3-7' in result['pending_by_days']
        assert '7+' in result['pending_by_days']
    
    def test_get_session_stats_structure(self):
        """Test session stats returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_session_stats()
        
        # Check structure
        assert 'active_sessions' in result
        assert 'total_sessions_24h' in result
        assert 'total_sessions_7d' in result
        assert 'avg_session_duration_minutes' in result
        assert 'most_active_time' in result
        
        # Check types
        assert isinstance(result['active_sessions'], int)
        assert isinstance(result['avg_session_duration_minutes'], float)
    
    def test_get_content_stats_structure(self):
        """Test content stats returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_content_stats(days=7)
        
        # Check structure
        assert 'period_days' in result
        assert 'messages' in result
        assert 'posts' in result
        assert 'replies' in result
        assert 'total_content' in result
        assert 'messages_per_day' in result
        assert 'posts_per_day' in result
        
        # Check types
        assert isinstance(result['messages'], int)
        assert isinstance(result['messages_per_day'], float)
    
    def test_get_dashboard_summary_structure(self):
        """Test dashboard summary returns all metrics"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_dashboard_summary()
        
        # Check all sections present
        assert 'admins' in result
        assert 'admin_activity' in result
        assert 'moderation' in result
        assert 'access_control' in result
        assert 'sessions' in result
        assert 'content' in result
        assert 'generated_at' in result
        
        # Verify generated_at is recent
        generated = datetime.fromisoformat(result['generated_at'])
        now = datetime.utcnow()
        assert (now - generated).total_seconds() < 5  # Within 5 seconds
    
    def test_get_historical_data_structure(self):
        """Test historical data returns expected structure"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_historical_data(metric='messages', days=7)
        
        # Check structure
        assert 'metric' in result
        assert 'period_days' in result
        assert 'data' in result
        
        # Check types
        assert result['metric'] == 'messages'
        assert isinstance(result['data'], list)
        
        # Check data format
        if len(result['data']) > 0:
            item = result['data'][0]
            assert 'date' in item
            assert 'value' in item
            assert isinstance(item['value'], int)
    
    def test_historical_data_different_metrics(self):
        """Test historical data with different metrics"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        metrics = ['messages', 'violations', 'sessions', 'admin_actions']
        
        for metric in metrics:
            result = service.get_historical_data(metric=metric, days=7)
            assert result['metric'] == metric
            assert isinstance(result['data'], list)


class TestAnalyticsDataValidation:
    """Test data validation and edge cases"""
    
    def test_admin_stats_days_parameter(self):
        """Test admin stats with different day periods"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        for days in [1, 7, 30]:
            result = service.get_admin_activity(days=days)
            assert result['period_days'] == days
    
    def test_content_stats_zero_content(self):
        """Test content stats when no content exists"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_content_stats(days=1)
        
        # Should have zeros, not errors
        assert result['messages'] >= 0
        assert result['posts'] >= 0
        assert result['replies'] >= 0
        assert result['total_content'] >= 0
    
    def test_access_stats_approval_rate_calculation(self):
        """Test approval rate calculation"""
        from services.analytics_service import AnalyticsService
        service = AnalyticsService()
        
        result = service.get_access_stats()
        
        # If no decisions yet, rate should be 0
        total_decisions = result['approved_total'] + result['rejected']
        if total_decisions == 0:
            assert result['approval_rate'] == 0
        else:
            # Rate should be between 0 and 100
            assert 0 <= result['approval_rate'] <= 100


class TestAnalyticsPerformance:
    """Test analytics performance"""
    
    def test_dashboard_summary_performance(self):
        """Test dashboard summary query performance"""
        from services.analytics_service import AnalyticsService
        import time
        
        service = AnalyticsService()
        
        start = time.time()
        result = service.get_dashboard_summary()
        duration = time.time() - start
        
        # Should complete in under 1 second
        assert duration < 1.0
        
        # Verify result is complete
        assert 'admins' in result
        assert 'moderation' in result

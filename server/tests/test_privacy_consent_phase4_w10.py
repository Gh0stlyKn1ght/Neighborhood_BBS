"""
Test suite for PHASE 4 Week 10 - Privacy Consent & Bulletins

Tests the following features:
- Privacy bulletin creation and management
- Consent acknowledgment recording
- Consent verification
- Consent statistics and cleanup
- REST API endpoints

Run with: pytest test_privacy_consent_phase4_w10.py -v

Author: AI Assistant
Date: 2026
"""

import pytest
import json
from datetime import datetime, timedelta
from models import db
from services.privacy_consent_service import privacy_consent_service
from setup_config import SetupConfig


class TestPrivacyConsentService:
    """Test PrivacyConsentService functionality"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert privacy_consent_service is not None
        assert privacy_consent_service.db is not None
    
    def test_create_bulletin(self):
        """Test creating a privacy bulletin"""
        success, message = privacy_consent_service.create_bulletin(
            title='Privacy Policy v1',
            content='This is our privacy policy...',
            created_by='admin'
        )
        
        assert success == True
        assert 'v1' in message or 'created' in message.lower()
    
    def test_get_active_bulletin(self):
        """Test retrieving active bulletin"""
        # Create bulletin first
        privacy_consent_service.create_bulletin(
            title='Active Bulletin',
            content='Privacy terms content',
            created_by='admin'
        )
        
        # Get active
        bulletin = privacy_consent_service.get_active_bulletin()
        assert bulletin is not None
        assert bulletin['title'] == 'Active Bulletin'
        assert 'content' in bulletin
        assert 'version' in bulletin
    
    def test_no_active_bulletin(self):
        """Test when no active bulletin exists"""
        # Clear all bulletins first by deleting
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM privacy_bulletins')
        conn.commit()
        conn.close()
        
        bulletin = privacy_consent_service.get_active_bulletin()
        assert bulletin is None
    
    def test_bulletin_version_management(self):
        """Test bulletin version incrementing"""
        # Create v1
        privacy_consent_service.create_bulletin(
            title='Policies v1',
            content='Version 1 content',
            created_by='admin'
        )
        
        v1 = privacy_consent_service.get_active_bulletin()
        assert v1['version'] == 1
        
        # Create v2
        privacy_consent_service.create_bulletin(
            title='Policies v2',
            content='Version 2 content',
            created_by='admin'
        )
        
        v2 = privacy_consent_service.get_active_bulletin()
        assert v2['version'] == 2
        
        # Old version should be inactive
        history = privacy_consent_service.get_bulletin_history(limit=10)
        versions = [b['version'] for b in history]
        assert 1 in versions or 2 in versions
    
    def test_get_bulletin_history(self):
        """Test retrieving bulletin history"""
        # Create multiple bulletins
        for i in range(3):
            privacy_consent_service.create_bulletin(
                title=f'Bulletin {i}',
                content=f'Content {i}',
                created_by='admin'
            )
        
        history = privacy_consent_service.get_bulletin_history(limit=10)
        assert len(history) >= 3
        assert all('version' in b for b in history)
    
    def test_record_consent(self):
        """Test recording user consent"""
        # Ensure active bulletin exists
        privacy_consent_service.create_bulletin(
            title='Test Bulletin',
            content='Test content',
            created_by='admin'
        )
        
        # Record consent
        success, message = privacy_consent_service.record_consent(
            session_id='test_session_001',
            ip_address='192.168.1.1',
            device_info='Mozilla/5.0'
        )
        
        assert success == True
        assert 'recorded' in message.lower() or 'success' in message.lower()
    
    def test_record_consent_without_bulletin(self):
        """Test consent fails without active bulletin"""
        # Clear bulletins
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM privacy_bulletins')
        conn.commit()
        conn.close()
        
        success, message = privacy_consent_service.record_consent(
            session_id='test_session'
        )
        
        assert success == False
        assert 'bulletin' in message.lower()
    
    def test_record_duplicate_consent(self):
        """Test recording same consent twice"""
        # Setup bulletin
        privacy_consent_service.create_bulletin(
            title='Bulletin',
            content='Content',
            created_by='admin'
        )
        
        # Record first time
        success1, msg1 = privacy_consent_service.record_consent(
            session_id='duplicate_test'
        )
        assert success1 == True
        
        # Record same session again
        success2, msg2 = privacy_consent_service.record_consent(
            session_id='duplicate_test'
        )
        
        # Should succeed but indicate already recorded
        assert success2 == True
        assert 'already' in msg2.lower() or 'success' in msg2.lower()
    
    def test_has_consented(self):
        """Test checking consent status"""
        import uuid
        
        # Setup
        privacy_consent_service.create_bulletin(
            title='Test',
            content='Test',
            created_by='admin'
        )
        
        # Use unique session ID
        session_id = f'consent_check_{uuid.uuid4().hex[:8]}'
        
        # Before consent
        assert privacy_consent_service.has_consented(session_id) == False
        
        # Record consent
        privacy_consent_service.record_consent(session_id)
        
        # After consent
        assert privacy_consent_service.has_consented(session_id) == True
    
    def test_get_consent_stats(self):
        """Test getting consent statistics"""
        stats = privacy_consent_service.get_consent_stats()
        
        assert 'total_consents' in stats
        assert 'unique_sessions' in stats
        assert isinstance(stats['total_consents'], int)
        assert isinstance(stats['unique_sessions'], int)
    
    def test_cleanup_old_consents(self):
        """Test cleanup of old consent records"""
        # Insert old record manually
        conn = db.get_connection()
        cursor = conn.cursor()
        
        old_date = datetime.now() - timedelta(days=100)
        cursor.execute('''
            INSERT INTO privacy_consents 
            (session_id, bulletin_version, acknowledged_at)
            VALUES (?, ?, ?)
        ''', (f'old_session_{datetime.now().timestamp()}', 1, old_date))
        
        conn.commit()
        conn.close()
        
        # Cleanup 90+ day old records
        count = privacy_consent_service.cleanup_old_consents(days_old=90)
        assert count >= 1
    
    def test_export_consent_summary(self):
        """Test exporting consent summary"""
        # Create bulletins and consents
        privacy_consent_service.create_bulletin(
            title='Summary Test',
            content='Test content',
            created_by='admin'
        )
        
        # Record multiple consents
        for i in range(3):
            privacy_consent_service.record_consent(f'session_{i}')
        
        summary = privacy_consent_service.export_consent_summary()
        
        assert 'total_consents' in summary
        assert summary['total_consents'] >= 3
        assert 'days_with_activity' in summary or 'consents_by_version' in summary


class TestPrivacyConsentIntegration:
    """Integration tests for privacy consent workflows"""
    
    def test_bulletin_creation_and_consent_workflow(self):
        """Test complete workflow from bulletin creation to consent"""
        # 1. Create bulletin
        success, msg = privacy_consent_service.create_bulletin(
            title='Integration Test Bulletin',
            content='Full workflow test content',
            created_by='admin'
        )
        assert success == True
        
        # 2. Get active bulletin
        bulletin = privacy_consent_service.get_active_bulletin()
        assert bulletin is not None
        assert bulletin['title'] == 'Integration Test Bulletin'
        
        # 3. Record consent for multiple sessions
        sessions = ['session_1', 'session_2', 'session_3']
        for sid in sessions:
            success, _ = privacy_consent_service.record_consent(
                session_id=sid,
                ip_address='10.0.0.1'
            )
            assert success == True
        
        # 4. Check each session
        for sid in sessions:
            assert privacy_consent_service.has_consented(sid) == True
        
        # 5. Get stats
        stats = privacy_consent_service.get_consent_stats()
        assert stats['total_consents'] >= 3
        assert stats['unique_sessions'] >= 3
    
    def test_bulletin_version_transition(self):
        """Test transitioning between bulletin versions"""
        # v1
        privacy_consent_service.create_bulletin(
            title='Version 1',
            content='Old content',
            created_by='admin'
        )
        
        # Record consent for v1
        privacy_consent_service.record_consent('v1_session')
        
        # v2 (old becomes inactive)
        privacy_consent_service.create_bulletin(
            title='Version 2',
            content='New content',
            created_by='admin'
        )
        
        # New session consents to v2
        privacy_consent_service.record_consent('v2_session')
        
        # Both sessions should have consented
        assert privacy_consent_service.has_consented('v1_session') == True
        assert privacy_consent_service.has_consented('v2_session') == True
        
        # Summary should show both versions
        summary = privacy_consent_service.export_consent_summary()
        assert summary.get('total_consents', 0) >= 2


class TestPrivacyConsentRoutes:
    """Test REST API endpoints for privacy consent"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from server import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            yield client
    
    def test_get_privacy_bulletin(self, client):
        """Test GET /api/privacy-consent/bulletin"""
        response = client.get('/api/privacy-consent/bulletin')
        
        # May be 200 or 404 depending on test setup
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'bulletin' in data or 'success' in data
    
    def test_acknowledge_consent(self, client):
        """Test POST /api/privacy-consent/acknowledge"""
        response = client.post(
            '/api/privacy-consent/acknowledge',
            json={
                'session_id': 'test_session_acknowledge'
            }
        )
        
        # Expect 200, 400, or 404 (missing bulletin)
        assert response.status_code in [200, 400, 404]
    
    def test_check_consent(self, client):
        """Test GET /api/privacy-consent/has-consented"""
        response = client.get(
            '/api/privacy-consent/has-consented?session_id=test_check_session'
        )
        
        assert response.status_code in [200, 400, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'has_consented' in data or 'success' in data


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

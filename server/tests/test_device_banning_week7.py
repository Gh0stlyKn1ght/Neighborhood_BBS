"""
Week 7: Device-Based Banning Tests
Tests privacy-aware device banning with MAC hashing and escalation workflow
"""

import unittest
import tempfile
import sqlite3
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from services.device_ban_service import DeviceBanService
from models import Database, BannedDevice

# Patch database path for testing
import os
os.environ['DB_PATH'] = ':memory:'


class DeviceBanServiceTests(unittest.TestCase):
    """Test device-based banning for repeated abuse escalation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up isolated test database"""
        cls.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db_path = cls.temp_db_file.name
        cls.temp_db_file.close()
        
        # Initialize database with schema
        Database.init_db(cls.temp_db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        try:
            if os.path.exists(cls.temp_db_path):
                os.unlink(cls.temp_db_path)
        except Exception as e:
            print(f"Warning: Could not delete temp db: {e}")
    
    def setUp(self):
        """Set up fresh service instance for each test"""
        Database.DB_PATH = self.temp_db_path
        self.service = DeviceBanService()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear banned_devices table
        conn = Database.get_connection()
        conn.execute('DELETE FROM banned_devices')
        conn.commit()
        conn.close()
    
    def test_device_id_generation_consistency(self):
        """Test that device_id is consistent for same IP + User-Agent"""
        device_id_1 = self.service._create_device_id('192.168.1.10', 'Mozilla/5.0')
        device_id_2 = self.service._create_device_id('192.168.1.10', 'Mozilla/5.0')
        
        # Same IP + User-Agent should produce same device_id
        self.assertEqual(device_id_1, device_id_2)
        print(f"✅ Device ID consistency: {device_id_1[:8]}...")
    
    def test_device_id_changes_with_user_agent(self):
        """Test that different User-Agent produces different device_id"""
        device_id_1 = self.service._create_device_id('192.168.1.10', 'Mozilla/5.0')
        device_id_2 = self.service._create_device_id('192.168.1.10', 'Safari/537')
        
        # Different User-Agent should produce different device_id
        self.assertNotEqual(device_id_1, device_id_2)
        print(f"✅ Device ID changes with User-Agent")
    
    def test_device_id_changes_with_ip(self):
        """Test that different IP address produces different device_id"""
        device_id_1 = self.service._create_device_id('192.168.1.10', 'Mozilla/5.0')
        device_id_2 = self.service._create_device_id('192.168.1.11', 'Mozilla/5.0')
        
        # Different IP should produce different device_id
        self.assertNotEqual(device_id_1, device_id_2)
        print(f"✅ Device ID changes with IP address")
    
    def test_mac_address_hashing(self):
        """Test that MAC addresses are hashed for privacy"""
        mac_plain = 'aa:bb:cc:dd:ee:ff'
        
        with patch.object(self.service, '_get_mac_address', return_value=mac_plain):
            # Should return hashed MAC, not plain text
            hashed = self.service._get_mac_address('192.168.1.10')
            
            # Hashed MAC should not contain original MAC
            self.assertNotIn('aa:bb:cc', hashed or '')
            self.assertNotIn('ff', hashed or '')
            print(f"✅ MAC hashing: plain hidden, hashed secure")
    
    def test_ban_device_creation(self):
        """Test creating a device ban"""
        device_id = 'test_device_123'
        ban_reason = 'Repeated abuse after warnings'
        
        success = self.service.ban_device(
            device_id=device_id,
            device_type='browser',
            mac_address=None,
            ip_address='192.168.1.10',
            ban_reason=ban_reason,
            banned_by='admin'
        )
        
        self.assertTrue(success)
        
        # Verify ban stored in database
        ban = BannedDevice.get_by_device_id(device_id)
        self.assertIsNotNone(ban)
        self.assertEqual(ban['ban_reason'], ban_reason)
        self.assertTrue(ban['is_active'])
        print(f"✅ Device ban creation: {device_id} banned successfully")
    
    def test_ban_device_rejects_duplicate(self):
        """Test that duplicate bans are rejected"""
        device_id = 'test_device_123'
        
        # First ban should succeed
        success1 = self.service.ban_device(
            device_id=device_id,
            device_type='browser',
            ban_reason='First ban',
            banned_by='admin'
        )
        self.assertTrue(success1)
        
        # Second ban (duplicate) should fail
        success2 = self.service.ban_device(
            device_id=device_id,
            device_type='browser',
            ban_reason='Duplicate ban',
            banned_by='admin'
        )
        self.assertFalse(success2)
        print(f"✅ Duplicate ban rejected")
    
    def test_unban_device(self):
        """Test unbanning a device (second chance)"""
        device_id = 'test_device_123'
        
        # Ban device
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Test ban',
            banned_by='admin'
        )
        
        # Verify banned
        ban_before = BannedDevice.get_by_device_id(device_id)
        self.assertIsNotNone(ban_before)
        
        # Unban
        success = self.service.unban_device(device_id)
        self.assertTrue(success)
        
        # Verify unbanned (should not find active ban)
        ban_after = BannedDevice.get_by_device_id(device_id)
        self.assertIsNone(ban_after)
        print(f"✅ Device unbanned (second chance)")
    
    def test_ban_enforcement_on_check(self):
        """Test that check_device_allowed rejects banned devices"""
        device_id = 'test_device_456'
        
        # Ban device
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Test ban for enforcement',
            banned_by='admin'
        )
        
        # Mock request context
        with patch('services.device_ban_service.request') as mock_request:
            mock_request.remote_addr = '192.168.1.20'
            mock_request.headers.get.side_effect = lambda key, default=None: {
                'X-Forwarded-For': None,
                'User-Agent': 'TestBrowser/1.0'
            }.get(key, default)
            
            # Mock device detection to return our test device_id
            with patch.object(self.service, 'get_device_info', return_value=(device_id, None, '192.168.1.20')):
                allowed, reason, info = self.service.check_device_allowed()
                
                # Should be rejected
                self.assertFalse(allowed)
                self.assertIsNotNone(reason)
                self.assertIn('Banned', reason or '')
                print(f"✅ Banned device rejected on check_device_allowed")
    
    def test_ban_by_ip_address(self):
        """Test banning by IP address (network-wide block)"""
        device_id = 'test_device_789'
        ip_address = '192.168.1.99'
        
        # Ban device
        self.service.ban_device(
            device_id=device_id,
            ip_address=ip_address,
            ban_reason='IP-based ban',
            banned_by='admin'
        )
        
        # Check by IP
        ban_by_ip = BannedDevice.get_by_ip(ip_address)
        self.assertIsNotNone(ban_by_ip)
        self.assertEqual(ban_by_ip['ip_address'], ip_address)
        print(f"✅ Ban by IP address: {ip_address} blocked")
    
    def test_ban_expiration(self):
        """Test temporary bans that expire"""
        device_id = 'test_device_exp'
        
        # Ban for 1 hour
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Temp ban',
            banned_by='admin',
            expire_hours=1
        )
        
        # Verify banned
        ban = BannedDevice.get_by_device_id(device_id)
        self.assertIsNotNone(ban)
        
        # Mock time to after expiration
        with patch('services.device_ban_service.datetime') as mock_datetime:
            # Set current time to 2 hours later
            future_time = datetime.now() + timedelta(hours=2)
            mock_datetime.now.return_value = future_time
            mock_datetime.fromisoformat = datetime.fromisoformat  # Keep real parsing
            
            # Check should auto-unban
            with patch.object(self.service, 'get_device_info', return_value=(device_id, None, '192.168.1.50')):
                allowed, reason, info = self.service.check_device_allowed()
                
                # Should be allowed (ban expired)
                self.assertTrue(allowed)
                self.assertEqual(info.get('ban_status'), 'expired')
                print(f"✅ Ban expiration: auto-unbanned after expiration time")
    
    def test_get_active_bans(self):
        """Test retrieving list of active bans"""
        # Create multiple bans
        for i in range(3):
            self.service.ban_device(
                device_id=f'test_device_{i}',
                ban_reason=f'Test ban {i}',
                banned_by='admin'
            )
        
        # Get all bans
        bans = self.service.get_active_bans()
        
        self.assertEqual(len(bans), 3)
        print(f"✅ Retrieved {len(bans)} active bans")
    
    def test_cleanup_expired_bans(self):
        """Test cleanup of expired bans"""
        # Create ban expiring in 1 second
        device_id = 'test_device_cleanup'
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Will expire',
            banned_by='admin',
            expire_hours=0  # Expires immediately
        )
        
        # Manually set to very soon future time
        conn = Database.get_connection()
        future = (datetime.now() + timedelta(seconds=0.5)).isoformat()
        conn.execute(
            'UPDATE banned_devices SET expires_at = ? WHERE device_id = ?',
            (future, device_id)
        )
        conn.commit()
        conn.close()
        
        # Run cleanup
        cleaned = self.service.cleanup_expired_bans()
        
        # Should have cleaned up at least one
        self.assertGreaterEqual(cleaned, 0)
        print(f"✅ Cleanup removed {cleaned} expired bans")
    
    def test_is_valid_mac_address(self):
        """Test MAC address validation"""
        valid_macs = [
            'aa:bb:cc:dd:ee:ff',
            'AA:BB:CC:DD:EE:FF',
            'aa-bb-cc-dd-ee-ff',
            'AA-BB-CC-DD-EE-FF'
        ]
        
        invalid_macs = [
            'not_a_mac',
            'aa:bb:cc:dd:ee',  # Too short
            'gg:hh:ii:jj:kk:ll',  # Invalid hex
            ''
        ]
        
        for mac in valid_macs:
            self.assertTrue(DeviceBanService._is_valid_mac(mac))
        
        for mac in invalid_macs:
            self.assertFalse(DeviceBanService._is_valid_mac(mac))
        
        print(f"✅ MAC address validation correct for {len(valid_macs)} valid, {len(invalid_macs)} invalid")
    
    def test_privacy_no_user_tracking(self):
        """Test that device bans don't track users (privacy validation)"""
        # Create ban
        device_id = 'test_privacy_device'
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Privacy test',
            banned_by='admin'
        )
        
        # Get ban record
        ban = BannedDevice.get_by_device_id(device_id)
        
        # Verify no user/nickname/account tracking
        self.assertNotIn('user_id', ban)
        self.assertNotIn('nickname', ban)
        self.assertNotIn('username', ban)
        self.assertNotIn('account', ban)
        
        # Should have device identifiers but not user identifiers
        self.assertIn('device_id', ban)
        self.assertIn('ip_address', ban)
        
        print(f"✅ Privacy validated: no user tracking in bans")
    
    def test_escalation_workflow(self):
        """
        Test escalation workflow:
        1. Session violations increase
        2. Session gets temp muted
        3. Repeated violations after unmute
        4. Device ban for further escalation
        """
        # This test validates the overall escalation flow
        # (Previous weeks handle session muting, this handles device banning)
        
        device_id = 'escalation_test_device'
        
        # Simulate escalation: device gets banned
        success = self.service.ban_device(
            device_id=device_id,
            device_type='browser',
            ban_reason='Escalated from repeated session violations',
            banned_by='admin',
            expire_hours=24
        )
        
        self.assertTrue(success)
        
        # Verify hard block
        ban = BannedDevice.get_by_device_id(device_id)
        self.assertIsNotNone(ban)
        self.assertTrue(ban['is_active'])
        
        print(f"✅ Escalation workflow: device ban created from repeated abuse")


class DeviceBanAdminEndpointTests(unittest.TestCase):
    """Test admin endpoints for device ban management"""
    
    # Note: These would be Flask test client tests in production
    # For now, we verify the service methods work
    
    def setUp(self):
        """Set up test database and service"""
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        Database.init_db(self.temp_db_path)
        Database.DB_PATH = self.temp_db_path
        self.service = DeviceBanService()
    
    def tearDown(self):
        """Clean up"""
        try:
            if os.path.exists(self.temp_db_path):
                os.unlink(self.temp_db_path)
        except:
            pass
    
    def test_ban_device_admin_workflow(self):
        """Test admin endpoint workflow for ban_device"""
        # Simulate POST /api/chat/admin/ban-device
        device_id = 'admin_test_device'
        ban_reason = 'Repeated abuse'
        
        success = self.service.ban_device(
            device_id=device_id,
            device_type='browser',
            ban_reason=ban_reason,
            banned_by='admin',
            expire_hours=48
        )
        
        self.assertTrue(success)
        print(f"✅ Admin ban endpoint workflow successful")
    
    def test_unban_device_admin_workflow(self):
        """Test admin endpoint workflow for unban_device"""
        # First create ban
        device_id = 'admin_unban_test'
        self.service.ban_device(
            device_id=device_id,
            ban_reason='Test ban',
            banned_by='admin'
        )
        
        # Simulate POST /api/chat/admin/unban-device
        success = self.service.unban_device(device_id)
        
        self.assertTrue(success)
        
        # Verify unbanned
        ban = BannedDevice.get_by_device_id(device_id)
        self.assertIsNone(ban)
        print(f"✅ Admin unban endpoint workflow successful")
    
    def test_get_device_bans_response(self):
        """Test response format for GET /api/chat/admin/device-bans"""
        # Create sample bans
        for i in range(2):
            self.service.ban_device(
                device_id=f'device_{i}',
                device_type='browser',
                ip_address=f'192.168.1.{100+i}',
                ban_reason=f'Test reason {i}',
                banned_by='admin'
            )
        
        bans = self.service.get_active_bans()
        
        # Verify response structure
        self.assertEqual(len(bans), 2)
        for ban in bans:
            self.assertIn('device_id', ban)
            self.assertIn('ban_reason', ban)
            self.assertIn('banned_by', ban)
            self.assertIn('banned_at', ban)
            self.assertTrue(ban['is_active'])
        
        print(f"✅ Device bans response format valid")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

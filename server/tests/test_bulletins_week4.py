"""
Integration tests for bulletins system (PHASE 1 Week 4)
Tests admin announcements, WebSocket broadcasts, and privacy-mode independence
"""

import unittest
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from server import create_app, socketio
from models import Database
from bulletins.service import BullletinService


class BulletinsAPITests(unittest.TestCase):
    """Test bulletins REST API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test app and database"""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.socketio_client = socketio.test_client(cls.app, flask_test_client=cls.client)
        
        # Initialize test database with temp file-based database
        import tempfile
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db_file.name
        temp_db_file.close()
        
        cls.db = Database(Path(temp_db_path))
        cls.db.init_db()
        cls.bulletin_service = BullletinService(cls.db)
        cls.temp_db_path = temp_db_path
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        import os
        import time
        # Close socketio client
        try:
            cls.socketio_client.disconnect()
        except:
            pass
        
        # Close app context
        try:
            cls.app.app_context().pop()
        except:
            pass
        
        # Wait a moment for resources to be freed
        time.sleep(0.1)
        
        # Try to remove the database file
        if os.path.exists(cls.temp_db_path):
            try:
                os.unlink(cls.temp_db_path)
            except PermissionError:
                # If still locked, try a few more times
                for _ in range(3):
                    time.sleep(0.2)
                    try:
                        os.unlink(cls.temp_db_path)
                        break
                    except:
                        continue
    
    def setUp(self):
        """Clear bulletins before each test"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bulletins')
        conn.commit()
        conn.close()
    
    # ========================================================================
    # CREATE TESTS
    # ========================================================================
    
    def test_create_bulletin_success(self):
        """Test successful bulletin creation"""
        data = {
            'title': 'System Maintenance',
            'content': 'Scheduled maintenance on Saturday 2-4 PM',
            'category': 'maintenance',
            'is_pinned': True,
            'created_by': 'admin'
        }
        
        bulletin = self.bulletin_service.create_bulletin(**data)
        
        self.assertNotIn('error', bulletin)
        self.assertEqual(bulletin['title'], data['title'])
        self.assertEqual(bulletin['content'], data['content'])
        self.assertEqual(bulletin['category'], data['category'])
        self.assertTrue(bulletin['is_pinned'])
        self.assertIsNotNone(bulletin['id'])
        self.assertIsNotNone(bulletin['created_at'])
    
    def test_create_bulletin_with_expiration(self):
        """Test creating bulletin with expiration timestamp"""
        expires_at = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        data = {
            'title': 'Tonight Event',
            'content': 'Community meeting tonight at 7 PM',
            'category': 'general',
            'expires_at': expires_at,
            'created_by': 'admin'
        }
        
        bulletin = self.bulletin_service.create_bulletin(**data)
        
        self.assertNotIn('error', bulletin)
        self.assertEqual(bulletin['expires_at'], expires_at)
    
    def test_create_bulletin_defaults(self):
        """Test bulletin creation with default values"""
        data = {
            'title': 'Announcement',
            'content': 'This is a notice',
            'created_by': 'admin'
        }
        
        bulletin = self.bulletin_service.create_bulletin(**data)
        
        self.assertEqual(bulletin['category'], 'general')
        self.assertFalse(bulletin['is_pinned'])
        self.assertTrue(bulletin['is_active'])
        self.assertIsNone(bulletin['expires_at'])
    
    # ========================================================================
    # READ TESTS
    # ========================================================================
    
    def test_get_bulletin_success(self):
        """Test retrieving single bulletin"""
        created = self.bulletin_service.create_bulletin(
            title='Test',
            content='Test content',
            created_by='admin'
        )
        
        retrieved = self.bulletin_service.get_bulletin(created['id'])
        
        self.assertEqual(retrieved['id'], created['id'])
        self.assertEqual(retrieved['title'], created['title'])
        self.assertEqual(retrieved['content'], created['content'])
    
    def test_get_bulletin_not_found(self):
        """Test getting non-existent bulletin"""
        result = self.bulletin_service.get_bulletin(9999)
        
        self.assertIn('error', result)
        self.assertEqual(result['status'], 404)
    
    def test_list_bulletins_empty(self):
        """Test listing bulletins when none exist"""
        bulletins = self.bulletin_service.list_bulletins()
        
        self.assertEqual(len(bulletins), 0)
    
    def test_list_bulletins_multiple(self):
        """Test listing multiple bulletins"""
        # Create 3 bulletins
        for i in range(3):
            self.bulletin_service.create_bulletin(
                title=f'Bulletin {i}',
                content=f'Content {i}',
                created_by='admin'
            )
        
        bulletins = self.bulletin_service.list_bulletins()
        
        self.assertEqual(len(bulletins), 3)
    
    def test_list_bulletins_ordered_by_pinned(self):
        """Test bulletins ordered with pinned first"""
        # Create unpinned bulletin
        b1 = self.bulletin_service.create_bulletin(
            title='First',
            content='Regular bulletin',
            created_by='admin',
            is_pinned=False
        )
        
        # Create pinned bulletin
        b2 = self.bulletin_service.create_bulletin(
            title='Second',
            content='Pinned bulletin',
            created_by='admin',
            is_pinned=True
        )
        
        bulletins = self.bulletin_service.list_bulletins()
        
        # Pinned should be first
        self.assertEqual(bulletins[0]['id'], b2['id'])
        self.assertEqual(bulletins[1]['id'], b1['id'])
    
    def test_list_bulletins_excludes_inactive(self):
        """Test list doesn't include inactive bulletins"""
        b1 = self.bulletin_service.create_bulletin(
            title='Active',
            content='This is active',
            created_by='admin'
        )
        
        b2 = self.bulletin_service.create_bulletin(
            title='Inactive',
            content='This will be deleted',
            created_by='admin'
        )
        
        # Soft delete b2
        self.bulletin_service.delete_bulletin(b2['id'])
        
        bulletins = self.bulletin_service.list_bulletins(active_only=True)
        
        self.assertEqual(len(bulletins), 1)
        self.assertEqual(bulletins[0]['id'], b1['id'])
    
    def test_list_bulletins_excludes_expired(self):
        """Test list doesn't include expired bulletins"""
        # Create expired bulletin
        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        b1 = self.bulletin_service.create_bulletin(
            title='Expired',
            content='This is expired',
            created_by='admin',
            expires_at=past_time
        )
        
        # Create active bulletin
        b2 = self.bulletin_service.create_bulletin(
            title='Active',
            content='This is active',
            created_by='admin'
        )
        
        # Don't include expired
        bulletins = self.bulletin_service.list_bulletins(include_expired=False)
        
        self.assertEqual(len(bulletins), 1)
        self.assertEqual(bulletins[0]['id'], b2['id'])
    
    def test_get_active_bulletins(self):
        """Test get_active_bulletins convenience method"""
        # Create mix of bulletins
        past = (datetime.utcnow() - timedelta(days=1)).isoformat()
        future = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        expired = self.bulletin_service.create_bulletin(
            title='Expired', content='Old', created_by='admin', expires_at=past
        )
        active = self.bulletin_service.create_bulletin(
            title='Active', content='Current', created_by='admin', expires_at=future
        )
        
        bulletins = self.bulletin_service.get_active_bulletins()
        
        self.assertEqual(len(bulletins), 1)
        self.assertEqual(bulletins[0]['id'], active['id'])
    
    # ========================================================================
    # UPDATE TESTS
    # ========================================================================
    
    def test_update_bulletin_title(self):
        """Test updating bulletin title"""
        b = self.bulletin_service.create_bulletin(
            title='Old Title',
            content='Content',
            created_by='admin'
        )
        
        updated = self.bulletin_service.update_bulletin(b['id'], title='New Title')
        
        self.assertEqual(updated['title'], 'New Title')
        self.assertEqual(updated['content'], 'Content')  # Unchanged
        self.assertNotEqual(updated['updated_at'], b['created_at'])
    
    def test_update_bulletin_multiple_fields(self):
        """Test updating multiple bulletin fields"""
        b = self.bulletin_service.create_bulletin(
            title='Original',
            content='Original content',
            category='general',
            is_pinned=False,
            created_by='admin'
        )
        
        updated = self.bulletin_service.update_bulletin(
            b['id'],
            title='Modified',
            category='maintenance',
            is_pinned=True
        )
        
        self.assertEqual(updated['title'], 'Modified')
        self.assertEqual(updated['category'], 'maintenance')
        self.assertTrue(updated['is_pinned'])
        self.assertEqual(updated['content'], 'Original content')  # Unchanged
    
    def test_update_bulletin_not_found(self):
        """Test updating non-existent bulletin"""
        result = self.bulletin_service.update_bulletin(9999, title='New')
        
        self.assertIn('error', result)
        self.assertEqual(result['status'], 404)
    
    def test_update_bulletin_no_fields(self):
        """Test update with no fields returns error"""
        b = self.bulletin_service.create_bulletin(
            title='Test',
            content='Test',
            created_by='admin'
        )
        
        result = self.bulletin_service.update_bulletin(b['id'])
        
        self.assertIn('error', result)
        self.assertEqual(result['status'], 400)
    
    # ========================================================================
    # DELETE TESTS
    # ========================================================================
    
    def test_delete_bulletin_success(self):
        """Test soft deleting bulletin"""
        b = self.bulletin_service.create_bulletin(
            title='To Delete',
            content='Content',
            created_by='admin'
        )
        
        result = self.bulletin_service.delete_bulletin(b['id'])
        
        self.assertNotIn('error', result)
        self.assertTrue(result['success'])
        
        # Verify it's marked inactive
        retrieved = self.bulletin_service.get_bulletin(b['id'])
        self.assertFalse(retrieved['is_active'])
    
    def test_delete_bulletin_not_found(self):
        """Test deleting non-existent bulletin"""
        result = self.bulletin_service.delete_bulletin(9999)
        
        self.assertIn('error', result)
        self.assertEqual(result['status'], 404)
    
    # ========================================================================
    # PIN/UNPIN TESTS
    # ========================================================================
    
    def test_pin_bulletin(self):
        """Test pinning a bulletin"""
        b = self.bulletin_service.create_bulletin(
            title='Test',
            content='Content',
            created_by='admin',
            is_pinned=False
        )
        
        pinned = self.bulletin_service.pin_bulletin(b['id'])
        
        self.assertTrue(pinned['is_pinned'])
    
    def test_unpin_bulletin(self):
        """Test unpinning a bulletin"""
        b = self.bulletin_service.create_bulletin(
            title='Test',
            content='Content',
            created_by='admin',
            is_pinned=True
        )
        
        unpinned = self.bulletin_service.unpin_bulletin(b['id'])
        
        self.assertFalse(unpinned['is_pinned'])
    
    # ========================================================================
    # EDGE CASES
    # ========================================================================
    
    def test_concurrent_access(self):
        """Test that concurrent bulletin operations work correctly"""
        import threading
        
        results = []
        
        def create_bulletin():
            b = self.bulletin_service.create_bulletin(
                title=f'Bulletin {len(results)}',
                content='Concurrent test',
                created_by='admin'
            )
            results.append(b['id'])
        
        threads = [threading.Thread(target=create_bulletin) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(results), 5)
        
        # Verify all were created
        bulletins = self.bulletin_service.list_bulletins()
        self.assertEqual(len(bulletins), 5)
    
    def test_very_long_content(self):
        """Test handling of long bulletin content"""
        long_content = 'X' * 4999  # Just under max
        
        b = self.bulletin_service.create_bulletin(
            title='Long Content',
            content=long_content,
            created_by='admin'
        )
        
        self.assertNotIn('error', b)
        self.assertEqual(len(b['content']), 4999)
    
    def test_special_characters_in_content(self):
        """Test handling of special characters"""
        content = 'Hello! @test #hashtag "quotes" \\backslash \n newline'
        
        b = self.bulletin_service.create_bulletin(
            title='Special Chars',
            content=content,
            created_by='admin'
        )
        
        self.assertNotIn('error', b)
        retrieved = self.bulletin_service.get_bulletin(b['id'])
        self.assertEqual(retrieved['content'], content)


class BulletinsWebSocketTests(unittest.TestCase):
    """Test WebSocket bulletin events"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test app"""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
    
    def setUp(self):
        """Create socket client for each test"""
        self.client = self.app.test_client()
        self.sio = socketio.test_client(self.app, flask_test_client=self.client)
    
    def tearDown(self):
        """Disconnect socket"""
        if self.sio.is_connected():
            self.sio.disconnect()
    
    def test_join_bulletins_event(self):
        """Test joining bulletins broadcast room"""
        self.sio.emit('join_bulletins')
        
        # Should receive bulletins_list event
        received = self.sio.get_received()
        self.assertTrue(any(msg['args'][0] == 'bulletins_list' for msg in received))
    
    def test_get_bulletins_event(self):
        """Test getting bulletins via WebSocket"""
        self.sio.emit('get_bulletins')
        
        received = self.sio.get_received()
        # Should receive bulletins_list event
        self.assertTrue(any(msg['args'][0] == 'bulletins_list' for msg in received))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

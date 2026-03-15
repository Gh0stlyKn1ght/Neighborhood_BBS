"""
Comprehensive tests for Neighborhood BBS
"""

import pytest


# ============ Basic Tests ============

def test_app_creation(app):
    """Test that app is created successfully"""
    assert app is not None


def test_app_testing_config(client):
    """Test app is in testing config"""
    assert client.application is not None


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['app'] == 'Neighborhood BBS'


def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert 'error' in response.get_json()


# ============ Chat Room Tests ============

def test_chat_get_rooms(client):
    """Test getting chat rooms"""
    response = client.get('/api/chat/rooms')
    assert response.status_code == 200
    data = response.get_json()
    assert 'rooms' in data


def test_create_chat_room(client):
    """Test creating a new chat room"""
    import time
    response = client.post('/api/chat/rooms', json={
        'name': f'test-room-{int(time.time())}',
        'description': 'A test room'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'room_id' in data


def test_create_room_missing_name(client):
    """Test creating room without name fails"""
    response = client.post('/api/chat/rooms', json={
        'description': 'No name room'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_create_room_duplicate(client):
    """Test duplicate room names are rejected"""
    client.post('/api/chat/rooms', json={'name': 'dup-room'})
    response = client.post('/api/chat/rooms', json={'name': 'dup-room'})
    assert response.status_code == 409
    assert 'already exists' in response.get_json()['error']


def test_create_room_sanitizes_html(client):
    """Test room names are sanitized of HTML"""
    import time
    response = client.post('/api/chat/rooms', json={
        'name': f'<script>alert("xss")</script>room-{int(time.time())}'
    })
    assert response.status_code == 201
    # Verify the room was created without HTML
    rooms_response = client.get('/api/chat/rooms')
    rooms = rooms_response.get_json()['rooms']
    created = next((r for r in rooms if 'alert' not in r['name']), None)
    assert created is not None


# ============ Chat Message Tests ============

def test_send_message(client):
    """Test sending a message"""
    import time
    # Create room first with unique name
    room = client.post('/api/chat/rooms', json={'name': f'msg-room-{int(time.time()*1000)}'}).get_json()
    room_id = room['room_id']

    response = client.post('/api/chat/send', json={
        'room_id': room_id,
        'author': 'TestUser',
        'content': 'Hello world'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'message_id' in data


def test_send_message_missing_content(client):
    """Test sending message without content fails"""
    import time
    room = client.post('/api/chat/rooms', json={'name': f'msg-room-{int(time.time()*1000)}'}).get_json()
    response = client.post('/api/chat/send', json={
        'room_id': room['room_id'],
        'author': 'User'
    })
    assert response.status_code == 400


def test_send_message_sanitizes_html(client):
    """Test message content is sanitized"""
    import time
    room = client.post('/api/chat/rooms', json={'name': f'msg-room-{int(time.time()*1000)}'}).get_json()
    response = client.post('/api/chat/send', json={
        'room_id': room['room_id'],
        'author': 'User',
        'content': '<img src=x onerror=alert(1)>test'
    })
    assert response.status_code == 201


def test_get_chat_history(client):
    """Test getting chat history"""
    import time
    room = client.post('/api/chat/rooms', json={'name': f'hist-room-{int(time.time()*1000)}'}).get_json()
    room_id = room['room_id']

    # Send a message
    client.post('/api/chat/send', json={
        'room_id': room_id,
        'author': 'User',
        'content': 'Test message'
    })

    response = client.get(f'/api/chat/history/{room_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'messages' in data
    assert len(data['messages']) > 0


def test_chat_history_pagination(client):
    """Test chat history pagination"""
    import time
    room = client.post('/api/chat/rooms', json={'name': f'pag-room-{int(time.time()*1000)}'}).get_json()
    room_id = room['room_id']

    # Send multiple messages
    for i in range(5):
        client.post('/api/chat/send', json={
            'room_id': room_id,
            'author': 'User',
            'content': f'Message {i}'
        })

    response = client.get(f'/api/chat/history/{room_id}?limit=2&offset=0')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['messages']) <= 2


# ============ Board Post Tests ============

def test_board_get_posts(client):
    """Test getting board posts"""
    response = client.get('/api/board/posts')
    assert response.status_code == 200
    data = response.get_json()
    assert 'posts' in data


def test_create_post(client):
    """Test creating a new post"""
    response = client.post('/api/board/posts', json={
        'title': 'Test Post',
        'content': 'This is a test post',
        'author': 'TestUser',
        'category': 'general'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'post_id' in data


def test_create_post_missing_fields(client):
    """Test creating post without required fields fails"""
    response = client.post('/api/board/posts', json={
        'title': 'Only Title'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_create_post_invalid_category(client):
    """Test invalid category is converted to default"""
    response = client.post('/api/board/posts', json={
        'title': 'Categorized Post',
        'content': 'Content here',
        'category': 'invalid-category'
    })
    assert response.status_code == 201
    # Should default to 'general'


def test_create_post_sanitizes_html(client):
    """Test post content is sanitized"""
    response = client.post('/api/board/posts', json={
        'title': '<script>alert(1)</script>Title',
        'content': '<img src=x onerror=alert(1)>Content',
        'author': 'User'
    })
    assert response.status_code == 201


def test_get_post(client):
    """Test getting a specific post"""
    # Create post
    create_response = client.post('/api/board/posts', json={
        'title': 'Specific Post',
        'content': 'Get this post',
        'author': 'User'
    })
    post_id = create_response.get_json()['post_id']

    # Get post
    response = client.get(f'/api/board/posts/{post_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'post' in data
    assert data['post']['id'] == post_id


def test_get_post_not_found(client):
    """Test getting nonexistent post returns 404"""
    response = client.get('/api/board/posts/99999')
    assert response.status_code == 404


# ============ Post Reply Tests ============

def test_add_reply_to_post(client):
    """Test adding a reply to a post"""
    # Create post
    post_response = client.post('/api/board/posts', json={
        'title': 'Reply Post',
        'content': 'Reply to this',
        'author': 'User'
    })
    post_id = post_response.get_json()['post_id']

    # Add reply
    response = client.post(f'/api/board/posts/{post_id}/replies', json={
        'author': 'Replier',
        'content': 'Great post!'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'reply_id' in data


def test_add_reply_to_nonexistent_post(client):
    """Test adding reply to nonexistent post returns 404"""
    response = client.post('/api/board/posts/99999/replies', json={
        'author': 'User',
        'content': 'Reply'
    })
    assert response.status_code == 404


def test_add_reply_missing_content(client):
    """Test reply without content fails"""
    post_response = client.post('/api/board/posts', json={
        'title': 'Reply Post 2',
        'content': 'Content',
        'author': 'User'
    })
    post_id = post_response.get_json()['post_id']

    response = client.post(f'/api/board/posts/{post_id}/replies', json={
        'author': 'User'
    })
    assert response.status_code == 400


def test_get_post_with_replies(client):
    """Test getting post includes replies"""
    # Create post
    post_response = client.post('/api/board/posts', json={
        'title': 'Post with Replies',
        'content': 'Content',
        'author': 'User'
    })
    post_id = post_response.get_json()['post_id']

    # Add reply
    client.post(f'/api/board/posts/{post_id}/replies', json={
        'author': 'Replier',
        'content': 'Reply 1'
    })

    # Get post
    response = client.get(f'/api/board/posts/{post_id}')
    data = response.get_json()
    assert 'replies' in data['post']
    assert len(data['post']['replies']) > 0

"""
Basic tests for Neighborhood BBS
"""

import pytest


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


def test_chat_get_rooms(client):
    """Test getting chat rooms"""
    response = client.get('/api/chat/rooms')
    assert response.status_code == 200
    data = response.get_json()
    assert 'rooms' in data


def test_board_get_posts(client):
    """Test getting board posts"""
    response = client.get('/api/board/posts')
    assert response.status_code == 200
    data = response.get_json()
    assert 'posts' in data


def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404

"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def app():
    """Create and configure a test app."""
    from server import create_app
    from models import db

    app = create_app()
    app.config['TESTING'] = True

    # Initialize database for testing
    db.init_db()

    return app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app's CLI commands."""
    return app.test_cli_runner()

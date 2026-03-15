"""
Neighborhood BBS - Main Application Entry Point
A community board and chatroom for neighborhoods
"""

import sys
from pathlib import Path

# Add parent directory to path for development
# This allows imports to work both in development and when installed
sys.path.insert(0, str(Path(__file__).parent))

from server import create_app, socketio
from models import db, ChatRoom
import logging
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def init_default_rooms():
    """Initialize default chat rooms"""
    default_rooms = [
        ('general', 'General neighborhood discussion'),
        ('announcements', 'Important community announcements'),
        ('events', 'Local events and gatherings'),
        ('help', 'Ask for and offer help'),
        ('marketplace', 'Buy, sell, and trade items'),
    ]
    
    logger.info("Initializing default chat rooms...")
    for name, description in default_rooms:
        room_id = ChatRoom.create(name, description)
        if room_id:
            logger.info(f"Created chat room: {name}")


def main():
    """Main entry point for the application"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Neighborhood BBS')
    parser.add_argument('--host', default=None, help='Host to bind to (default: from .env)')
    parser.add_argument('--port', type=int, default=None, help='Port to listen on (default: from .env)')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    args = parser.parse_args()
    
    logger.info("Starting Neighborhood BBS...")
    
    # Initialize database
    logger.info("Initializing database...")
    db.init_db()
    init_default_rooms()
    
    # Create Flask app
    app = create_app()
    
    # Get configuration (CLI args override config file)
    host = args.host or app.config.get('HOST', '127.0.0.1')
    port = args.port or app.config.get('PORT', 8080)
    debug = not args.no_debug and app.config.get('DEBUG', True)
    
    logger.info(f"Server running on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 50)
    logger.info("Visit http://localhost:8080 in your browser")
    logger.info("=" * 50)
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

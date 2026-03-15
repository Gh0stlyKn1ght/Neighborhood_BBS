"""
Neighborhood BBS - Main Application Entry Point
A community board and chatroom for neighborhoods
"""

from server import create_app, socketio
from models import db, ChatRoom
import logging
from pathlib import Path
import sys

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
    logger.info("Starting Neighborhood BBS...")
    
    # Initialize database
    logger.info("Initializing database...")
    db.init_db()
    init_default_rooms()
    
    # Create Flask app
    app = create_app()
    
    # Get configuration
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8080)
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Server running on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 50)
    logger.info("Visit http://localhost:8080 in your browser")
    logger.info("=" * 50)
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

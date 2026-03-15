"""
Neighborhood BBS - Main Application Entry Point
A community board and chatroom for neighborhoods
"""

from server import create_app, socketio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application"""
    logger.info("Starting Neighborhood BBS...")
    
    app = create_app()
    
    # Get configuration
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8080)
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Server running on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

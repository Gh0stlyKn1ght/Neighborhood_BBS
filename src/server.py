"""
Flask application factory and configuration
"""

from flask import Flask
from flask_socketio import SocketIO
import os
from pathlib import Path

socketio = SocketIO(cors_allowed_origins="*")


def create_app(config_file=None):
    """
    Application factory for Flask app
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['HOST'] = os.environ.get('HOST', '0.0.0.0')
    app.config['PORT'] = int(os.environ.get('PORT', 8080))
    app.config['DEBUG'] = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.config['JSON_SORT_KEYS'] = False
    
    # Max connections
    app.config['MAX_CONNECTIONS'] = int(os.environ.get('MAX_CONNECTIONS', 100))
    
    # Initialize extensions
    socketio.init_app(app)
    
    # Register blueprints
    from chat.routes import chat_bp
    from board.routes import board_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(board_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'app': 'Neighborhood BBS'}
    
    return app

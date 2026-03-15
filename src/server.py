"""
Flask application factory and configuration
"""

from flask import Flask, render_template, send_from_directory
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
    # Get the path to the web directory
    base_path = Path(__file__).parent.parent
    template_path = base_path / 'web' / 'templates'
    static_path = base_path / 'web' / 'static'
    
    app = Flask(
        __name__,
        template_folder=str(template_path),
        static_folder=str(static_path),
        static_url_path='/static'
    )
    
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
    
    # Home page
    @app.route('/')
    def index():
        """Render home page"""
        try:
            return render_template('index.html')
        except Exception as e:
            return {'error': 'Could not load home page', 'detail': str(e)}, 500
    
    # Static files
    @app.route('/static/<path:path>')
    def static_files(path):
        """Serve static files"""
        return send_from_directory(app.static_folder, path)
    
    return app

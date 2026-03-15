"""
Flask application factory and configuration
"""

from flask import Flask, render_template, send_from_directory, request, jsonify, redirect
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from pathlib import Path

# Configure CORS origins from environment
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:8080').split(',')
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

socketio = SocketIO(cors_allowed_origins=cors_origins)
limiter = Limiter(key_func=get_remote_address)


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
    
    # Session configuration for admin panel
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('ADMIN_SESSION_TIMEOUT', 3600))
    
    # Max connections
    app.config['MAX_CONNECTIONS'] = int(os.environ.get('MAX_CONNECTIONS', 100))
    
    # Initialize extensions
    socketio.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from chat.routes import chat_bp
    from board.routes import board_bp
    from admin.routes import admin_bp
    from setup.routes import setup_bp
    from privacy.routes import privacy_bp
    from user.routes import user_bp
    from moderation.routes import moderation_bp
    from access.routes import access_bp
    from privacy_consent.routes import privacy_consent_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(privacy_consent_bp)
    
    # Setup check middleware
    @app.before_request
    def check_setup_required():
        """Redirect to setup if not complete"""
        from setup_config import SetupConfig
        
        # Allow these paths without setup
        allowed_paths = [
            '/api/setup',
            '/api/privacy',
            '/api/user',
            '/setup',
            '/static',
            '/api/health'
        ]
        
        # Check if path is allowed without setup
        for allowed in allowed_paths:
            if request.path.startswith(allowed):
                return
        
        # Check if setup is complete
        if not SetupConfig.is_setup_complete():
            return redirect('/setup')
    
    # Route to setup wizard page
    @app.route('/setup')
    def setup_page():
        """Serve setup wizard"""
        from setup_config import SetupConfig
        
        # If setup is already complete, redirect to home
        if SetupConfig.is_setup_complete():
            return redirect('/')
        
        return render_template('setup-wizard.html')

    # Middleware for device ban checking
    @app.before_request
    def check_device_ban():
        """Check if requesting device is banned"""
        from models import BannedDevice
        
        # Skip ban check for admin routes and static files
        if request.path.startswith('/api/admin') or request.path.startswith('/static') or request.path.startswith('/admin'):
            return
        
        # Get device identifier from request
        device_id = request.headers.get('X-Device-ID', request.args.get('device_id'))
        ip_address = get_remote_address()
        
        # Check if device is banned
        if device_id:
            ban = BannedDevice.get_by_device_id(device_id)
            if ban:
                return jsonify({'error': 'Device banned', 'reason': ban.get('ban_reason')}), 403
        
        # Check if IP is banned
        ban = BannedDevice.get_by_ip(ip_address)
        if ban:
            return jsonify({'error': 'IP banned', 'reason': ban.get('ban_reason')}), 403

    # Initialize chat log cleanup scheduler
    def init_chat_log_scheduler():
        """Initialize chat log cleanup scheduler on app startup"""
        try:
            from utils.chat_log_manager import schedule_daily_chat_log_cleanup, get_chat_log_retention_config
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Get retention setting from config
            retention_days = get_chat_log_retention_config()
            
            # Schedule cleanup
            schedule_daily_chat_log_cleanup(retention_days)
            logger.info(f"Chat log cleanup scheduled: daily deletion of logs older than {retention_days} days")
        
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize chat log scheduler: {e}")
    
    # Schedule chat log cleanup on app startup
    with app.app_context():
        init_chat_log_scheduler()

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # NOTE: 'unsafe-inline' is necessary for inline CSS animations and styles in retro terminal interface
        # This is acceptable because: (1) All user input is sanitized with bleach, (2) No user content in style attrs
        # For production with external CSS, use nonce-based CSP: "script-src 'nonce-{random}'"
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {'error': 'Rate limit exceeded'}, 429
    
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
    
    # Admin panel pages
    @app.route('/admin-login.html')
    def admin_login_page():
        """Render admin login page"""
        try:
            return render_template('admin-login.html')
        except Exception as e:
            return {'error': 'Could not load admin login', 'detail': str(e)}, 500
    
    @app.route('/admin/dashboard.html')
    def admin_dashboard_page():
        """Render admin dashboard page"""
        try:
            return render_template('admin-dashboard.html')
        except Exception as e:
            return {'error': 'Could not load admin dashboard', 'detail': str(e)}, 500
    
    # Static files
    @app.route('/static/<path:path>')
    def static_files(path):
        """Serve static files"""
        return send_from_directory(app.static_folder, path)
    
    return app

"""
Flask application factory and configuration
"""

from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, session
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import hmac
import secrets
from pathlib import Path

socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)

# Cache: set True once setup is complete to avoid a DB query on every request
_setup_complete_cache = False

_INSECURE_DEFAULTS = {
    'dev-secret-key-change-in-production',
    'change-me',
    'secret',
}

_CSRF_SESSION_KEY = '_csrf_token'


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
    
    # --- Secrets: fail hard if missing or using known-insecure defaults ---
    is_production = os.environ.get('FLASK_ENV', 'production').lower() != 'development'
    secret_key = os.environ.get('SECRET_KEY')
    if is_production:
        if not secret_key or secret_key in _INSECURE_DEFAULTS:
            raise RuntimeError(
                "SECRET_KEY env var must be set to a cryptographically random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
    else:
        secret_key = secret_key or 'dev-only-not-for-production'

    # Configure CORS origins inside factory so env is fully resolved
    cors_origins = [
        o.strip()
        for o in os.environ.get('CORS_ORIGINS', 'http://localhost:8080').split(',')
        if o.strip()
    ]

    # Default configuration
    app.config['SECRET_KEY'] = secret_key
    app.config['HOST'] = os.environ.get('HOST', '127.0.0.1')
    app.config['PORT'] = int(os.environ.get('PORT', 8080))
    app.config['DEBUG'] = os.environ.get('FLASK_ENV', 'production').lower() == 'development'
    app.config['JSON_SORT_KEYS'] = False

    # Session configuration for admin panel
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('ADMIN_SESSION_TIMEOUT', 3600))
    def _get_or_create_csrf_token():
        token = session.get(_CSRF_SESSION_KEY)
        if not token:
            token = secrets.token_urlsafe(32)
            session[_CSRF_SESSION_KEY] = token
        return token

    def _is_csrf_exempt(path):
        exempt_exact = {
            '/health',
            '/api/health',
            '/api/csrf/token',
            '/api/auth/join',
            '/api/auth/admin-login',
            '/api/user/join',
            '/api/user/register',
            '/api/user/login',
            '/api/auth/validate-passcode',
            '/api/auth/open-join',
            '/api/auth/request-approval',
            '/api/auth/create-approved-session',
            '/api/access/register',
            '/api/access/verify-token',
            '/api/admin/login',
            '/api/admin-management/login',
            '/api/admin-management/validate-token',
        }
        exempt_prefixes = (
            '/static/',
            '/api/setup/',
        )
        return path in exempt_exact or path.startswith(exempt_prefixes)

    # Max connections
    app.config['MAX_CONNECTIONS'] = int(os.environ.get('MAX_CONNECTIONS', 100))

    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins=cors_origins)
    limiter.init_app(app)

    # Register blueprints
    from chat.routes import chat_bp
    from board.routes import board_bp
    from admin.routes import admin_bp
    from admin.admin_management import admin_management_bp
    from auth.routes import auth_bp
    from setup.routes import setup_bp
    from privacy.routes import privacy_bp
    from user.routes import user_bp
    from moderation.routes import moderation_bp
    from access.routes import access_bp
    from privacy_consent.routes import privacy_consent_bp
    from bulletins.routes import bulletins_bp
    from admin.audit.routes import audit_bp
    from admin.analytics.routes import analytics_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_management_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(privacy_consent_bp)
    app.register_blueprint(bulletins_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(analytics_bp)
    
    # Setup check middleware
    @app.before_request
    def check_setup_required():
        """Redirect to setup if not complete. Cached after first successful check."""
        global _setup_complete_cache
        if _setup_complete_cache:
            return

        from setup_config import SetupConfig

        # Exact-match or prefix-match paths allowed before setup completes
        allowed_exact = {'/setup', '/api/health'}
        allowed_prefixes = ('/api/setup/', '/api/privacy/', '/api/user/', '/static/')

        if request.path in allowed_exact or request.path.startswith(allowed_prefixes):
            return

        # Check if setup is complete; cache the result once true
        if SetupConfig.is_setup_complete():
            _setup_complete_cache = True
            return

        return redirect('/setup')

    @app.before_request
    def csrf_protect():
        """Enforce CSRF token checks for state-changing HTTP requests."""
        _get_or_create_csrf_token()

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return

        if _is_csrf_exempt(request.path):
            return

        expected = session.get(_CSRF_SESSION_KEY)
        provided = request.headers.get('X-CSRF-Token', '')
        if not expected or not provided or not hmac.compare_digest(expected, provided):
            return jsonify({'error': 'CSRF validation failed'}), 403

    @app.route('/api/csrf/token', methods=['GET'])
    def get_csrf_token():
        """Return a CSRF token clients must echo in X-CSRF-Token for mutating requests."""
        return jsonify({'csrf_token': _get_or_create_csrf_token()}), 200
    
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
        
        # Client-supplied device ID is supplemental only — do NOT use query params
        device_id = request.headers.get('X-Device-ID')
        ip_address = get_remote_address()

        # Check if device is banned
        if device_id:
            ban = BannedDevice.get_by_device_id(device_id)
            if ban:
                return jsonify({'error': 'Access denied'}), 403

        # Check if IP is banned
        ban = BannedDevice.get_by_ip(ip_address)
        if ban:
            return jsonify({'error': 'Access denied'}), 403

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
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # X-XSS-Protection intentionally omitted — deprecated and harmful in IE; modern browsers ignore it
        if os.environ.get('FLASK_ENV', 'production').lower() != 'development':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # TODO: Replace unsafe-inline with nonce-based CSP for script-src
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'"
        )
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
            app.logger.error(f"Could not load home page: {e}", exc_info=True)
            return {'error': 'Internal server error'}, 500
    
    # Admin panel pages
    @app.route('/admin-login.html')
    def admin_login_page():
        """Render admin login page"""
        try:
            return render_template('admin-login.html')
        except Exception as e:
            app.logger.error(f"Could not load admin login: {e}", exc_info=True)
            return {'error': 'Internal server error'}, 500
    
    @app.route('/admin/dashboard.html')
    def admin_dashboard_page():
        """Render admin dashboard page"""
        try:
            return render_template('admin-dashboard.html')
        except Exception as e:
            app.logger.error(f"Could not load admin dashboard: {e}", exc_info=True)
            return {'error': 'Internal server error'}, 500
    
    # Static files
    @app.route('/static/<path:path>')
    def static_files(path):
        """Serve static files"""
        return send_from_directory(app.static_folder, path)
    
    return app

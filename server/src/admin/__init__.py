"""
Admin panel module - Management and configuration
"""

from .routes import admin_bp
from .admin_management import admin_management_bp

__all__ = ['admin_bp', 'admin_management_bp']

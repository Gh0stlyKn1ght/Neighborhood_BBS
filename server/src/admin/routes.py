"""
Admin panel routes - Device banning, network configuration, themes
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import logging
from models import AdminUser, BannedDevice, NetworkConfig, ThemeSettings
from .auth import admin_required, admin_role_required, hash_password, verify_password
from server import limiter

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ==================== AUTHENTICATION ====================

@admin_bp.route('/login', methods=['POST'])
@limiter.limit("5/minute")
def admin_login():
    """Authenticate admin user"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'error': 'Username and password required'}), 400
        
        # Get admin user
        admin_user = AdminUser.get_by_username(username)
        if not admin_user or not admin_user.get('is_active'):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(password, admin_user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create session
        session.permanent = True
        session['admin_id'] = admin_user['id']
        session['admin_username'] = admin_user['username']
        session['admin_role'] = admin_user['role']
        
        # Update last login
        AdminUser.update_last_login(admin_user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'admin': {
                'id': admin_user['id'],
                'username': admin_user['username'],
                'role': admin_user['role'],
                'email': admin_user['email']
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Admin login error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    """Logout admin user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


@admin_bp.route('/me', methods=['GET'])
@admin_required
def get_current_admin():
    """Get current admin info"""
    try:
        admin_user = AdminUser.get_by_username(session.get('admin_username'))
        if not admin_user:
            return jsonify({'error': 'Admin not found'}), 404
        
        return jsonify({
            'id': admin_user['id'],
            'username': admin_user['username'],
            'email': admin_user['email'],
            'role': admin_user['role'],
            'is_active': admin_user['is_active'],
            'created_at': admin_user['created_at'],
            'last_login': admin_user['last_login']
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching admin info: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ==================== DEVICE BAN MANAGEMENT ====================

@admin_bp.route('/devices/ban', methods=['POST'])
@admin_required
def ban_device():
    """Ban a device"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        device_id = data.get('device_id')
        device_type = data.get('device_type', 'unknown')
        mac_address = data.get('mac_address')
        ip_address = data.get('ip_address')
        ban_reason = data.get('ban_reason', 'No reason provided')
        expire_hours = data.get('expire_hours')  # Optional: ban duration in hours
        
        if not device_id:
            return jsonify({'error': 'Device ID required'}), 400
        
        expires_at = None
        if expire_hours:
            expires_at = (datetime.now() + timedelta(hours=int(expire_hours))).isoformat()
        
        # Ban the device
        ban_id = BannedDevice.ban_device(
            device_id=device_id,
            device_type=device_type,
            mac_address=mac_address,
            ip_address=ip_address,
            ban_reason=ban_reason,
            banned_by=session.get('admin_username'),
            expires_at=expires_at
        )
        
        if not ban_id:
            return jsonify({'error': 'Device already banned or database error'}), 400
        
        logger.info(f"Device {device_id} banned by {session.get('admin_username')}")
        return jsonify({
            'message': 'Device banned successfully',
            'ban_id': ban_id,
            'device_id': device_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error banning device: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/devices/bans', methods=['GET'])
@admin_required
def get_banned_devices():
    """Get list of banned devices"""
    try:
        active_only = request.args.get('active', 'true').lower() == 'true'
        bans = BannedDevice.get_all_bans(active_only=active_only)
        
        return jsonify({
            'total': len(bans),
            'bans': bans
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching banned devices: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/devices/check/<device_id>', methods=['GET'])
@admin_required
@limiter.limit("30/minute")
def check_device_ban(device_id):
    """Check if device is banned"""
    try:
        ban = BannedDevice.get_by_device_id(device_id)
        
        if ban:
            return jsonify({
                'is_banned': True,
                'ban_reason': ban.get('ban_reason'),
                'expires_at': ban.get('expires_at'),
                'banned_at': ban.get('banned_at')
            }), 200
        
        return jsonify({'is_banned': False}), 200
    
    except Exception as e:
        logger.error(f"Error checking device ban: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/devices/check-ip/<ip_address>', methods=['GET'])
@admin_required
@limiter.limit("30/minute")
def check_ip_ban(ip_address):
    """Check if IP address is banned"""
    try:
        ban = BannedDevice.get_by_ip(ip_address)
        
        if ban:
            return jsonify({
                'is_banned': True,
                'ban_reason': ban.get('ban_reason'),
                'device_id': ban.get('device_id'),
                'device_type': ban.get('device_type'),
                'expires_at': ban.get('expires_at')
            }), 200
        
        return jsonify({'is_banned': False}), 200
    
    except Exception as e:
        logger.error(f"Error checking IP ban: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/devices/unban/<device_id>', methods=['POST'])
@admin_required
def unban_device(device_id):
    """Unban a device"""
    try:
        BannedDevice.unban_device(device_id)
        
        logger.info(f"Device {device_id} unbanned by {session.get('admin_username')}")
        return jsonify({
            'message': 'Device unbanned successfully',
            'device_id': device_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error unbanning device: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ==================== NETWORK CONFIGURATION ====================

@admin_bp.route('/network/config', methods=['GET'])
@admin_required
def get_network_configs():
    """Get all network configurations"""
    try:
        configs = NetworkConfig.get_all_configs()
        
        return jsonify({
            'total': len(configs),
            'configs': configs
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching network configs: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/network/config/<setting_name>', methods=['GET'])
@admin_required
def get_network_config(setting_name):
    """Get specific network configuration"""
    try:
        config = NetworkConfig.get_config(setting_name)
        
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        return jsonify(config), 200
    
    except Exception as e:
        logger.error(f"Error fetching network config: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/network/config', methods=['POST'])
@admin_required
@admin_role_required('admin')
def set_network_config():
    """Set network configuration"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        setting_name = data.get('setting_name')
        setting_value = data.get('setting_value')
        setting_type = data.get('setting_type', 'string')
        description = data.get('description', '')
        
        if not all([setting_name, setting_value]):
            return jsonify({'error': 'Setting name and value required'}), 400
        
        # Validate setting types
        allowed_types = ['string', 'integer', 'boolean', 'json']
        if setting_type not in allowed_types:
            return jsonify({'error': f'Invalid setting type. Allowed: {allowed_types}'}), 400
        
        success = NetworkConfig.set_config(
            setting_name=setting_name,
            setting_value=str(setting_value),
            setting_type=setting_type,
            description=description,
            updated_by=session.get('admin_username')
        )
        
        if not success:
            return jsonify({'error': 'Failed to set configuration'}), 500
        
        logger.info(f"Network config '{setting_name}' updated by {session.get('admin_username')}")
        return jsonify({
            'message': 'Configuration updated successfully',
            'setting_name': setting_name
        }), 200
    
    except Exception as e:
        logger.error(f"Error setting network config: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== THEME MANAGEMENT ====================

@admin_bp.route('/themes', methods=['GET'])
def get_themes():
    """Get all themes"""
    try:
        themes = ThemeSettings.get_all_themes()
        active_theme = ThemeSettings.get_active_theme()
        
        return jsonify({
            'total': len(themes),
            'themes': themes,
            'active_theme': active_theme
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching themes: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/themes/active', methods=['GET'])
def get_active_theme():
    """Get the active theme"""
    try:
        theme = ThemeSettings.get_active_theme()
        
        if not theme:
            return jsonify({'error': 'No active theme'}), 404
        
        return jsonify(theme), 200
    
    except Exception as e:
        logger.error(f"Error fetching active theme: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/themes', methods=['POST'])
@admin_required
def create_theme():
    """Create a new theme"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        theme_name = data.get('theme_name')
        primary_color = data.get('primary_color', '#007bff')
        secondary_color = data.get('secondary_color', '#6c757d')
        background_color = data.get('background_color', '#ffffff')
        text_color = data.get('text_color', '#000000')
        font_family = data.get('font_family', 'Arial, sans-serif')
        
        if not theme_name:
            return jsonify({'error': 'Theme name required'}), 400
        
        theme_id = ThemeSettings.create_theme(
            theme_name=theme_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
            background_color=background_color,
            text_color=text_color,
            font_family=font_family
        )
        
        if not theme_id:
            return jsonify({'error': 'Theme already exists'}), 400
        
        logger.info(f"Theme '{theme_name}' created by {session.get('admin_username')}")
        return jsonify({
            'message': 'Theme created successfully',
            'theme_id': theme_id,
            'theme_name': theme_name
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/themes/<int:theme_id>/activate', methods=['POST'])
@admin_required
def activate_theme(theme_id):
    """Activate a theme"""
    try:
        ThemeSettings.set_active_theme(theme_id)
        
        logger.info(f"Theme {theme_id} activated by {session.get('admin_username')}")
        return jsonify({
            'message': 'Theme activated successfully',
            'theme_id': theme_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error activating theme: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/themes/<int:theme_id>', methods=['PUT'])
@admin_required
def update_theme(theme_id):
    """Update theme settings"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        
        # Extract only updateable fields
        updates = {}
        for field in ['primary_color', 'secondary_color', 'background_color', 'text_color', 'font_family']:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        ThemeSettings.update_theme(theme_id, **updates)
        
        logger.info(f"Theme {theme_id} updated by {session.get('admin_username')}")
        return jsonify({
            'message': 'Theme updated successfully',
            'theme_id': theme_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/themes/<int:theme_id>', methods=['DELETE'])
@admin_required
@admin_role_required('admin')
def delete_theme(theme_id):
    """Delete a theme"""
    try:
        ThemeSettings.delete_theme(theme_id)
        
        logger.info(f"Theme {theme_id} deleted by {session.get('admin_username')}")
        return jsonify({
            'message': 'Theme deleted successfully',
            'theme_id': theme_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting theme: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== ADMIN DASHBOARD ====================

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Get admin dashboard overview"""
    try:
        # Get statistics
        banned_devices = BannedDevice.get_all_bans(active_only=True)
        network_configs = NetworkConfig.get_all_configs()
        themes = ThemeSettings.get_all_themes()
        
        return jsonify({
            'stats': {
                'banned_devices_count': len(banned_devices),
                'network_configs_count': len(network_configs),
                'themes_count': len(themes)
            },
            'admin': {
                'username': session.get('admin_username'),
                'role': session.get('admin_role')
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== CHAT LOG MANAGEMENT ====================

@admin_bp.route('/chat-logs/retention', methods=['GET'])
@admin_required
def get_chat_log_retention():
    """Get chat log retention settings"""
    try:
        from utils.chat_log_manager import get_chat_log_retention_config, get_message_stats
        
        retention_days = get_chat_log_retention_config()
        stats = get_message_stats()
        
        return jsonify({
            'retention_days': retention_days,
            'message_stats': stats,
            'description': f'Chat logs older than {retention_days} days are deleted daily at 00:00 UTC'
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching chat log retention: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/chat-logs/retention', methods=['POST'])
@admin_required
@admin_role_required('admin')
def set_chat_log_retention():
    """Set chat log retention period"""
    try:
        from utils.chat_log_manager import set_chat_log_retention
        
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'JSON body required'}), 400
        retention_days = data.get('retention_days', 30)
        
        if not isinstance(retention_days, int) or retention_days < 1 or retention_days > 365:
            return jsonify({'error': 'Retention days must be between 1 and 365'}), 400
        
        success = set_chat_log_retention(retention_days, session.get('admin_username'))
        
        if success:
            logger.info(f"Chat log retention set to {retention_days} days by {session.get('admin_username')}")
            return jsonify({
                'message': f'Chat log retention set to {retention_days} days',
                'retention_days': retention_days
            }), 200
        else:
            return jsonify({'error': 'Failed to set retention'}), 500
    
    except Exception as e:
        logger.error(f"Error setting chat log retention: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/chat-logs/delete-now', methods=['POST'])
@admin_required
@admin_role_required('admin')
def delete_chat_logs_now():
    """Manually trigger chat log deletion"""
    try:
        from utils.chat_log_manager import delete_old_chat_logs, get_chat_log_retention_config
        
        retention_days = get_chat_log_retention_config()
        count = delete_old_chat_logs(retention_days)
        
        logger.info(f"Manual chat log deletion by {session.get('admin_username')}: deleted {count} logs")
        
        return jsonify({
            'message': f'Deleted {count} chat logs older than {retention_days} days',
            'deleted_count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting chat logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/hardware-logs', methods=['GET'])
@admin_required
def get_hardware_logs():
    """Get hardware logs"""
    try:
        from utils.hardware_logger import get_hardware_logs
        
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)  # Max 1000 logs
        
        logs = get_hardware_logs(limit)
        
        return jsonify({
            'total': len(logs),
            'logs': logs
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching hardware logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

"""
Setup wizard routes - 5-step initial configuration
"""

from flask import Blueprint, request, jsonify, render_template
import logging
from setup_config import SetupConfig
from utils.security import hash_password, verify_password
from server import limiter

logger = logging.getLogger(__name__)

setup_bp = Blueprint('setup', __name__, url_prefix='/api/setup')


@setup_bp.route('/status', methods=['GET'])
def get_setup_status():
    """Check if setup wizard is needed"""
    is_complete = SetupConfig.is_setup_complete()
    
    return jsonify({
        'setup_complete': is_complete,
        'next_step': None if is_complete else 1
    }), 200


@setup_bp.route('/wizard/1', methods=['GET'])
def get_step_1():
    """Get step 1 (admin password) info"""
    data = SetupConfig.get_setup_step_1_data()
    
    return jsonify({
        'step': 1,
        'title': 'Set Admin Password',
        'description': 'This is the ONLY password needed. Users do NOT need to login.',
        'fields': [
            {
                'name': 'admin_password',
                'type': 'password',
                'label': 'Admin Password',
                'placeholder': 'Enter strong password',
                'required': True
            },
            {
                'name': 'admin_password_confirm',
                'type': 'password',
                'label': 'Confirm Password',
                'placeholder': 'Confirm password',
                'required': True
            }
        ],
        'tip': 'Use a strong password. Only admins need this.',
        'completed': data['completed']
    }), 200


@setup_bp.route('/wizard/1', methods=['POST'])
@limiter.limit("5/minute")
def save_step_1():
    """Save step 1 (admin password)"""
    try:
        data = request.get_json()
        
        password = data.get('admin_password', '').strip()
        password_confirm = data.get('admin_password_confirm', '').strip()
        
        # Validate
        if not password or not password_confirm:
            return jsonify({'error': 'Password required'}), 400
        
        if password != password_confirm:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Hash and save
        password_hash = hash_password(password)
        if not SetupConfig.save_step_1(password_hash):
            return jsonify({'error': 'Failed to save password'}), 500
        
        return jsonify({
            'status': 'ok',
            'next_step': 2
        }), 200
    
    except Exception as e:
        logger.error(f"Error saving step 1: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/wizard/2', methods=['GET'])
def get_step_2():
    """Get step 2 (privacy mode) info"""
    
    return jsonify({
        'step': 2,
        'title': 'Privacy Settings',
        'description': 'How should we handle chat history?',
        'fields': [
            {
                'name': 'privacy_mode',
                'type': 'radio',
                'label': 'Privacy Mode',
                'options': [
                    {
                        'value': 'full_privacy',
                        'label': 'FULL PRIVACY (Recommended)',
                        'description': 'Messages deleted when user disconnects. No permanent record.',
                        'why': 'True privacy, less liability',
                        'recommended': True
                    },
                    {
                        'value': 'hybrid',
                        'label': 'HYBRID (7-day retention)',
                        'description': 'Messages auto-delete after 7 days. Balance privacy + reference.',
                        'why': 'Best of both worlds',
                        'recommended': False
                    },
                    {
                        'value': 'persistent',
                        'label': 'PERSISTENT (Full history)',
                        'description': 'Messages saved permanently for reference.',
                        'why': 'Useful for Q&A communities',
                        'recommended': False
                    }
                ],
                'required': True
            }
        ]
    }), 200


@setup_bp.route('/wizard/2', methods=['POST'])
def save_step_2():
    """Save step 2 (privacy mode)"""
    try:
        data = request.get_json()
        privacy_mode = data.get('privacy_mode', '').strip()
        
        if privacy_mode not in ['full_privacy', 'hybrid', 'persistent']:
            return jsonify({'error': 'Invalid privacy mode'}), 400
        
        if not SetupConfig.save_step_2(privacy_mode):
            return jsonify({'error': 'Failed to save privacy mode'}), 500
        
        return jsonify({
            'status': 'ok',
            'next_step': 3
        }), 200
    
    except Exception as e:
        logger.error(f"Error saving step 2: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/wizard/3', methods=['GET'])
def get_step_3():
    """Get step 3 (user accounts) info"""
    
    return jsonify({
        'step': 3,
        'title': 'User Accounts',
        'description': 'Do users need accounts to chat?',
        'fields': [
            {
                'name': 'account_system',
                'type': 'radio',
                'label': 'Account System',
                'options': [
                    {
                        'value': 'anonymous',
                        'label': 'ANONYMOUS ONLY',
                        'description': 'No accounts needed. Users pick a nickname.',
                        'pros': ['No login required', 'Lowest friction', 'Most private'],
                        'cons': ['Can\'t ban specific abusers'],
                        'recommended': True
                    },
                    {
                        'value': 'optional',
                        'label': 'OPTIONAL ACCOUNTS',
                        'description': 'Users can register or stay anonymous.',
                        'pros': ['Optional privacy', 'Can ban specific users'],
                        'cons': ['More complex'],
                        'recommended': False
                    }
                ],
                'required': True
            }
        ]
    }), 200


@setup_bp.route('/wizard/3', methods=['POST'])
def save_step_3():
    """Save step 3 (user accounts)"""
    try:
        data = request.get_json()
        account_system = data.get('account_system', '').strip()
        
        if account_system not in ['anonymous', 'optional']:
            return jsonify({'error': 'Invalid account system'}), 400
        
        if not SetupConfig.save_step_3(account_system):
            return jsonify({'error': 'Failed to save account system'}), 500
        
        return jsonify({
            'status': 'ok',
            'next_step': 4
        }), 200
    
    except Exception as e:
        logger.error(f"Error saving step 3: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/wizard/4', methods=['GET'])
def get_step_4():
    """Get step 4 (moderation) info"""
    
    return jsonify({
        'step': 4,
        'title': 'Moderation & Abuse Response',
        'description': 'If someone misbehaves, what can admins do?',
        'fields': [
            {
                'name': 'moderation_levels',
                'type': 'radio',
                'label': 'Moderation Strategy',
                'options': [
                    {
                        'value': 'hybrid',
                        'label': 'HYBRID (Recommended)',
                        'description': 'Start with content filtering, escalate to timeouts, then device ban.',
                        'tiers': [
                            'Tier 1: Auto-filter offensive content',
                            'Tier 2: 24-hour session timeout for repeat offenders',
                            'Tier 3: Device MAC address ban (last resort)'
                        ],
                        'why': 'Balances privacy with effective moderation',
                        'recommended': True
                    },
                    {
                        'value': 'content_only',
                        'label': 'CONTENT FILTERING ONLY',
                        'description': 'Only auto-filter bad content, no user/device tracking.',
                        'tiers': [
                            'Only: Ban content patterns automatically'
                        ],
                        'why': 'Maximum privacy, but less effective against persistent abusers',
                        'recommended': False
                    }
                ],
                'required': True
            }
        ]
    }), 200


@setup_bp.route('/wizard/4', methods=['POST'])
def save_step_4():
    """Save step 4 (moderation)"""
    try:
        data = request.get_json()
        moderation_levels = data.get('moderation_levels', '').strip()
        
        if moderation_levels not in ['content_only', 'hybrid']:
            return jsonify({'error': 'Invalid moderation selection'}), 400
        
        if not SetupConfig.save_step_4(moderation_levels):
            return jsonify({'error': 'Failed to save moderation settings'}), 500
        
        return jsonify({
            'status': 'ok',
            'next_step': 5
        }), 200
    
    except Exception as e:
        logger.error(f"Error saving step 4: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/wizard/5', methods=['GET'])
def get_step_5():
    """Get step 5 (access control) info"""
    
    return jsonify({
        'step': 5,
        'title': 'Access Control',
        'description': 'How should people join your community?',
        'fields': [
            {
                'name': 'access_control',
                'type': 'radio',
                'label': 'Access Control',
                'options': [
                    {
                        'value': 'open',
                        'label': 'OPEN',
                        'description': 'Anyone on WiFi can join.',
                        'pros': ['No barrier to entry'],
                        'cons': ['Strangers can join'],
                        'recommended': False
                    },
                    {
                        'value': 'passcode',
                        'label': 'PASSCODE (Recommended)',
                        'description': 'Must know passcode to join. Easy to share and reset.',
                        'pros': ['Keeps out drive-bys', 'Easy to reset if leaked'],
                        'cons': ['Can be shared'],
                        'recommended': True,
                        'requires_input': 'passcode'
                    },
                    {
                        'value': 'approved',
                        'label': 'ADMIN-APPROVED',
                        'description': 'Admin manually approves each user.',
                        'pros': ['Most control'],
                        'cons': ['Slowest setup'],
                        'recommended': False
                    }
                ],
                'required': True
            }
        ]
    }), 200


@setup_bp.route('/wizard/5', methods=['POST'])
def save_step_5():
    """Save step 5 (access control)"""
    try:
        data = request.get_json()
        access_control = data.get('access_control', '').strip()
        
        if access_control not in ['open', 'passcode', 'approved']:
            return jsonify({'error': 'Invalid access control'}), 400
        
        passcode_hash = None
        if access_control == 'passcode':
            passcode = data.get('passcode', '').strip()
            if not passcode:
                return jsonify({'error': 'Passcode required'}), 400
            if len(passcode) < 4:
                return jsonify({'error': 'Passcode must be at least 4 characters'}), 400
            
            passcode_hash = hash_password(passcode)
        
        if not SetupConfig.save_step_5(access_control, passcode_hash):
            return jsonify({'error': 'Failed to save access control'}), 500
        
        return jsonify({
            'status': 'ok',
            'next_step': 'complete'
        }), 200
    
    except Exception as e:
        logger.error(f"Error saving step 5: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/wizard/complete', methods=['POST'])
def complete_setup():
    """Mark setup as complete"""
    try:
        if not SetupConfig.mark_setup_complete():
            return jsonify({'error': 'Failed to complete setup'}), 500
        
        return jsonify({
            'status': 'ok',
            'message': 'Setup complete!',
            'redirect': '/admin'
        }), 200
    
    except Exception as e:
        logger.error(f"Error completing setup: {e}")
        return jsonify({'error': str(e)}), 500


@setup_bp.route('/summary', methods=['GET'])
def get_setup_summary():
    """Get current setup configuration summary"""
    try:
        config = SetupConfig.get_all_config()
        
        return jsonify({
            'setup_complete': config.get('setup_complete') == 'true',
            'configuration': {
                'privacy_mode': config.get('privacy_mode'),
                'account_system': config.get('account_system'),
                'moderation_levels': config.get('moderation_levels'),
                'access_control': config.get('access_control'),
                'violation_threshold': config.get('violation_threshold'),
                'session_timeout_hours': config.get('session_timeout_hours')
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting setup summary: {e}")
        return jsonify({'error': str(e)}), 500

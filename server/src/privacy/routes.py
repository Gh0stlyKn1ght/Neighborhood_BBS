"""
Privacy API routes - Info about privacy settings and data handling
Users can see what data is/isn't being collected
"""

from flask import Blueprint, jsonify
import logging
from admin_config import AdminConfig
from privacy_handler import PrivacyModeHandler

logger = logging.getLogger(__name__)

privacy_bp = Blueprint('privacy', __name__, url_prefix='/api/privacy')


@privacy_bp.route('/info', methods=['GET'])
def get_privacy_info():
    """
    Get privacy information for users
    Shows what data is collected and how
    """
    try:
        privacy_mode = AdminConfig.get_privacy_mode()
        moderation_levels = AdminConfig.get_moderation_levels()
        account_system = AdminConfig.get_account_system()
        access_control = AdminConfig.get_access_control()
        
        # Build privacy description
        descriptions = {
            'full_privacy': {
                'name': 'FULL PRIVACY',
                'description': 'Messages are ephemeral - deleted when you disconnect',
                'data_collected': [],
                'data_not_collected': [
                    'Chat history',
                    'IP addresses',
                    'Device IDs',
                    'Behavioral tracking',
                    'Personal identification'
                ],
                'message_storage': 'None (RAM only)',
                'message_lifespan': 'Until you disconnect',
                'can_admins_see_history': False
            },
            'hybrid': {
                'name': 'HYBRID (7-day retention)',
                'description': 'Messages auto-delete after 7 days',
                'data_collected': [
                    'Messages (temporary, 7 days)',
                    'Chat timestamps (temporary, 7 days)'
                ],
                'data_not_collected': [
                    'IP addresses',
                    'Device IDs',
                    'Individual user identity tracking',
                    'Personal identification'
                ],
                'message_storage': 'Database (encrypted)',
                'message_lifespan': '7 days, then auto-deleted',
                'can_admins_see_history': True
            },
            'persistent': {
                'name': 'PERSISTENT',
                'description': 'Messages saved permanently',
                'data_collected': [
                    'All messages (permanent)',
                    'Chat history (permanent)',
                    'Chat timestamps (permanent)'
                ],
                'data_not_collected': [
                    'IP addresses',
                    'Device IDs',
                    'Individual user identity tracking'
                ],
                'message_storage': 'Database (encrypted)',
                'message_lifespan': 'Permanent (unless deleted)',
                'can_admins_see_history': True
            }
        }
        
        privacy_info = descriptions.get(privacy_mode, descriptions['full_privacy'])
        
        return jsonify({
            'privacy_mode': privacy_mode,
            'privacy_info': privacy_info,
            'user_accounts': {
                'type': account_system,
                'requires_login': account_system != 'anonymous',
                'description': 'Anonymous (no login)' if account_system == 'anonymous' else f'{account_system} accounts'
            },
            'access_control': {
                'type': access_control,
                'description': {
                    'open': 'Anyone can join',
                    'passcode': 'Access requires passcode',
                    'approved': 'Admin must approve new users'
                }.get(access_control)
            },
            'moderation': {
                'levels': moderation_levels,
                'tracks_individual_users': AdminConfig.should_track_individual_user(),
                'description': 'Content filtering and escalation (no individual user tracking)' if not AdminConfig.should_track_individual_user() else 'Moderation with optional user identification'
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting privacy info: {e}")
        return jsonify({'error': str(e)}), 500


@privacy_bp.route('/statistics', methods=['GET'])
def get_privacy_statistics():
    """
    Get anonymous statistics about message storage
    Shows aggregate data only (no individual tracking)
    """
    try:
        privacy_handler = PrivacyModeHandler.create_handler_from_config()
        stats = privacy_handler.get_statistics()
        
        return jsonify(stats), 200
    
    except Exception as e:
        logger.error(f"Error getting privacy statistics: {e}")
        return jsonify({'error': str(e)}), 500


@privacy_bp.route('/policy', methods=['GET'])
def get_privacy_policy():
    """
    Get privacy policy for the community
    Built from admin configuration
    """
    try:
        config = AdminConfig.get_all_config()
        
        policy = {
            'title': 'Privacy Policy - Neighborhood BBS',
            'version': '1.0',
            'effective_date': config.get('setup_completed_at', 'Unknown'),
            'privacy_mode': config.get('privacy_mode', 'full_privacy'),
            'policy_text': _get_policy_text(config)
        }
        
        return jsonify(policy), 200
    
    except Exception as e:
        logger.error(f"Error getting privacy policy: {e}")
        return jsonify({'error': str(e)}), 500


def _get_policy_text(config):
    """Generate privacy policy text based on configuration"""
    
    privacy_mode = config.get('privacy_mode', 'full_privacy')
    
    policy = f"""
NEIGHBORHOOD BBS - PRIVACY POLICY

1. DATA COLLECTION
Privacy Mode: {privacy_mode.upper()}

"""
    
    if privacy_mode == 'full_privacy':
        policy += """
Your messages are stored in memory during your session only.
When you disconnect, all your messages are permanently deleted.
No permanent record of conversations is kept.

Data NOT collected:
- IP addresses
- Device identifiers
- Browsing history
- Personal identification
- Behavioral tracking

"""
    
    elif privacy_mode == 'hybrid':
        policy += """
Your messages are stored for 7 days then automatically deleted.
Admins can reference recent conversations but cannot access older messages.
Messages expire and are permanently deleted after 7 days.

Data NOT collected:
- IP addresses
- Device identifiers
- Personal identification
- Individual user tracking

"""
    
    elif privacy_mode == 'persistent':
        policy += """
Your messages are stored permanently in the database.
Admins have full access to message history.
You can request deletion of your messages.

Data NOT collected:
- IP addresses
- Device identifiers
- Personal identification

"""
    
    policy += """
2. MODERATION
Moderation is content-based, not user-based.
We filter content patterns, not track individuals.

3. ADMIN TRANSPARENCY
All admin actions are logged and can be reviewed.
You can appeal any moderation action.

4. DATA REQUESTS
You can request:
- Deletion of your messages (if applicable to your mode)
- Export of your data
- Appeal of moderation actions

5. QUESTIONS
Contact: [Admin Contact Information]
"""
    
    return policy


@privacy_bp.route('/transparency', methods=['GET'])
def get_transparency_report():
    """
    Get transparency report about data handling
    Shows what systems are in place to protect privacy
    """
    try:
        from utils.message_scheduler import MessageCleanupScheduler
        
        cleanup_stats = MessageCleanupScheduler.get_cleanup_stats()
        
        return jsonify({
            'transparency': {
                'privacy_first': True,
                'no_tracking': 'Individual users not tracked in full_privacy mode',
                'data_minimization': 'Only necessary data collected',
                'audit_transparency': 'All admin actions logged',
                'user_control': 'Users can request data deletion (where applicable)',
                'technical_measures': [
                    'End-to-end encrypted data at rest',
                    'No IP logging',
                    'No device fingerprinting',
                    'Automatic message cleanup (hybrid mode)',
                    'Rate limiting on all endpoints',
                    'No external analytics',
                    'No third-party data sharing'
                ]
            },
            'storage_info': cleanup_stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting transparency report: {e}")
        return jsonify({'error': str(e)}), 500

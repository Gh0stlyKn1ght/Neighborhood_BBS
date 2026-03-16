"""
Approval-based access control service
Handles user approval requests and admin approval management
Phase 3 Week 9 Implementation
"""

import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Tuple
from models import Database
from admin_config import AdminConfig

logger = logging.getLogger(__name__)

# Global instance
_approval_service_instance = None
_instance_lock = Lock()


class ApprovalAccessService:
    """
    Approval-based access control for restricted communities.
    
    Design Principles:
    - Optional feature: Only active if admin chose 'approved' mode at setup
    - Users submit nickname + optional message requesting access
    - Admin reviews pending requests and approves/rejects
    - Approved users can join immediately
    - Rejected users can request again later
    - Audit trail of all approval decisions
    - Works alongside privacy modes (independent)
    
    Architecture:
    - Check access mode from AdminConfig (open/passcode/approved)
    - If approved mode: require approval before session creation
    - Store approval requests and decisions in user_registrations table
    - Support admin batch approvals
    - Support user re-requests after rejection
    
    Database Tables Used:
    - user_registrations: Pending and approved user records
      * nickname (TEXT)
      * request_reason (TEXT, optional)
      * status (TEXT) - 'pending', 'approved', 'rejected'
      * approved_by (TEXT)
      * approved_at (TIMESTAMP)
    """
    
    def __init__(self):
        """Initialize ApprovalAccessService"""
        self._request_cache = {}  # Cache nickname → {status, created_at}
        self._cache_lock = Lock()
    
    def is_approval_required(self) -> bool:
        """
        Check if approval is required for joining.
        
        Returns:
            True if access_control mode is 'approved', False otherwise
        """
        try:
            access_mode = AdminConfig.get_access_control()
            return access_mode == 'approved'
        except Exception as e:
            logger.error(f"Error checking if approval required: {e}")
            return False
    
    def request_approval(self, nickname: str, request_reason: str = '') -> Tuple[bool, str]:
        """
        Submit approval request to join community.
        
        Args:
            nickname: User's requested nickname
            request_reason: Optional message to admin (e.g., "I live on Elm Street")
            
        Returns:
            Tuple of (success, message)
            success: True if request submitted
            message: Status message
            
        Design:
            - Check nickname doesn't already exist (approved or pending)
            - Check nickname is 2-50 characters
            - Create user_registrations record with status='pending'
            - Log creation timestamp
            - Return message with expected wait time
        """
        try:
            # Validate nickname
            if not nickname or len(nickname) < 2 or len(nickname) > 50:
                return False, "Nickname must be 2-50 characters"
            
            # Check for invalid characters
            if not self._is_valid_nickname(nickname):
                return False, "Nickname contains invalid characters"
            
            # Check if nickname already exists (approved or pending)
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, status FROM user_registrations
                WHERE nickname = ?
            ''', (nickname,))
            
            existing = cursor.fetchone()
            conn.close()
            
            if existing:
                existing_status = existing[1]
                if existing_status == 'approved':
                    return False, "This nickname is already approved"
                elif existing_status == 'pending':
                    return False, "Request already pending. Please wait for admin review."
                elif existing_status == 'rejected':
                    # Allow re-request after rejection
                    pass
            
            # Validate request reason
            if request_reason and len(request_reason) > 500:
                return False, "Request reason too long (max 500 characters)"
            
            # Create approval request
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_registrations
                    (nickname, request_reason, status, requires_approval, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    nickname,
                    request_reason or None,
                    'pending',
                    True,
                    datetime.now()
                ))
                
                conn.commit()
                
                logger.info(f"Approval request created for nickname: {nickname}")
                
                return True, "Request submitted! Admin will review shortly. Check back soon."
                
            except Exception as e:
                logger.warning(f"Error inserting approval request: {e}")
                return False, "Failed to submit request"
            finally:
                conn.close()
            
        except Exception as e:
            logger.error(f"Error in request_approval: {e}")
            return False, "System error during request submission"
    
    def check_approval_status(self, nickname: str) -> Tuple[str, Optional[str]]:
        """
        Check if user is approved to join.
        
        Args:
            nickname: Nickname to check
            
        Returns:
            Tuple of (status, message)
            status: 'approved', 'pending', 'rejected', or 'not_requested'
            message: Human-readable status message
            
        Design:
            - Query user_registrations for nickname
            - Return status and relevant message
            - For pending: show request ID and expected wait
            - For rejected: suggest re-requesting
            - For not_requested: suggest submitting request
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, created_at, approved_at, approved_by
                FROM user_registrations
                WHERE nickname = ?
            ''', (nickname,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return 'not_requested', 'No approval request found. Submit a request to join.'
            
            status = result[0]
            created_at = result[1]
            approved_at = result[2]
            approved_by = result[3]
            
            if status == 'approved':
                return 'approved', f'Approved by {approved_by} on {approved_at}. You can now join!'
            
            elif status == 'pending':
                # Calculate days waiting
                created = datetime.fromisoformat(created_at)
                days_waiting = (datetime.now() - created).days
                return 'pending', f'Request pending ({days_waiting} days). Admin will review soon.'
            
            elif status == 'rejected':
                return 'rejected', 'Your previous request was rejected. You can submit again.'
            
            else:
                return status, f'Status: {status}'
            
        except Exception as e:
            logger.error(f"Error checking approval status: {e}")
            return 'unknown', 'Could not check approval status'
    
    def approve_user(self, nickname: str, admin_username: str = 'admin') -> Tuple[bool, str]:
        """
        Approve a user (admin action).
        
        Args:
            nickname: User to approve
            admin_username: Admin performing approval
            
        Returns:
            Tuple of (success, message)
            
        Design:
            - Find pending request for nickname
            - Update status to 'approved'
            - Record approved_by and approved_at timestamps
            - Log approval action
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if request exists and is pending
            cursor.execute('''
                SELECT id, status FROM user_registrations
                WHERE nickname = ?
            ''', (nickname,))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, f"No request found for {nickname}"
            
            if result[1] != 'pending':
                conn.close()
                return False, f"User not in pending status (current: {result[1]})"
            
            # Update to approved
            cursor.execute('''
                UPDATE user_registrations
                SET status = ?, approved_by = ?, approved_at = ?
                WHERE nickname = ?
            ''', (
                'approved',
                admin_username,
                datetime.now(),
                nickname
            ))
            
            conn.commit()
            
            logger.info(f"User {nickname} approved by {admin_username}")
            
            return True, f"User {nickname} approved successfully"
            
        except Exception as e:
            logger.error(f"Error approving user: {e}")
            return False, "System error during approval"
        finally:
            conn.close()
    
    def reject_user(self, nickname: str, rejection_reason: str = '', admin_username: str = 'admin') -> Tuple[bool, str]:
        """
        Reject a user's approval request (admin action).
        
        Args:
            nickname: User to reject
            rejection_reason: Reason for rejection
            admin_username: Admin performing rejection
            
        Returns:
            Tuple of (success, message)
            
        Design:
            - Find pending request for nickname
            - Update status to 'rejected'
            - Store rejection_reason
            - User can request again later
            - Log rejection action
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if request exists and is pending
            cursor.execute('''
                SELECT id, status FROM user_registrations
                WHERE nickname = ?
            ''', (nickname,))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, f"No request found for {nickname}"
            
            if result[1] != 'pending':
                conn.close()
                return False, f"User not in pending status (current: {result[1]})"
            
            # Update to rejected
            cursor.execute('''
                UPDATE user_registrations
                SET status = ?, approved_by = ?, approved_at = ?
                WHERE nickname = ?
            ''', (
                'rejected',
                admin_username,
                datetime.now(),
                nickname
            ))
            
            conn.commit()
            
            logger.info(f"User {nickname} rejected by {admin_username}: {rejection_reason}")
            
            return True, f"User {nickname} rejected"
            
        except Exception as e:
            logger.error(f"Error rejecting user: {e}")
            return False, "System error during rejection"
        finally:
            conn.close()
    
    def get_pending_requests(self, limit: int = 100) -> List[Dict]:
        """
        Get list of pending approval requests (admin view).
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of pending request records with:
            - id, nickname, request_reason
            - created_at (when request was made)
            - days_pending (how long waiting)
            
        Design:
            - Query all pending requests
            - Sort by created_at (oldest first)
            - Include request reason in review
            - Include time waiting (helps admin prioritize)
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nickname, request_reason, created_at
                FROM user_registrations
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))
            
            requests = []
            for row in cursor.fetchall():
                created = datetime.fromisoformat(row[3])
                days_pending = (datetime.now() - created).days
                
                requests.append({
                    'id': row[0],
                    'nickname': row[1],
                    'request_reason': row[2],
                    'created_at': row[3],
                    'days_pending': days_pending
                })
            
            conn.close()
            return requests
            
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    def get_approval_history(self, limit: int = 50) -> List[Dict]:
        """
        Get approval history (approved and rejected users).
        
        Args:
            limit: Maximum records to return
            
        Returns:
            List of approval records with:
            - nickname, status, approved_by, approved_at
            
        Design:
            - Query non-pending requests
            - Sort by approved_at (newest first)
            - Include admin who approved/rejected
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nickname, status, approved_by, approved_at
                FROM user_registrations
                WHERE status IN ('approved', 'rejected')
                ORDER BY approved_at DESC
                LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'nickname': row[0],
                    'status': row[1],
                    'approved_by': row[2],
                    'approved_at': row[3]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"Error getting approval history: {e}")
            return []
    
    def get_approval_statistics(self) -> Dict:
        """
        Get approval system statistics (admin dashboard).
        
        Returns:
            Dict with:
            - pending_count: Number of pending requests
            - approved_count: Total approved users
            - rejected_count: Total rejected requests
            - oldest_pending: How long oldest request has waited
            
        Design:
            - Aggregated statistics only (no PII)
            - Helps admin understand queue
            - Shows system health
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get counts by status
            cursor.execute('''
                SELECT status, COUNT(*) FROM user_registrations
                GROUP BY status
            ''')
            
            stats = {
                'pending_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }
            
            for row in cursor.fetchall():
                status = row[0]
                count = row[1]
                if status == 'pending':
                    stats['pending_count'] = count
                elif status == 'approved':
                    stats['approved_count'] = count
                elif status == 'rejected':
                    stats['rejected_count'] = count
            
            # Get oldest pending
            cursor.execute('''
                SELECT MIN(created_at) FROM user_registrations
                WHERE status = 'pending'
            ''')
            
            oldest_result = cursor.fetchone()
            if oldest_result and oldest_result[0]:
                oldest = datetime.fromisoformat(oldest_result[0])
                stats['oldest_pending_hours'] = int((datetime.now() - oldest).total_seconds() / 3600)
            else:
                stats['oldest_pending_hours'] = 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting approval statistics: {e}")
            return {'error': str(e)}
    
    # ========== PRIVATE METHODS ==========
    
    @staticmethod
    def _is_valid_nickname(nickname: str) -> bool:
        """
        Validate nickname format.
        
        Rules:
        - Alphanumeric, spaces, hyphens, underscores only
        - No special characters
        """
        import re
        # Allow letters, numbers, spaces, hyphens, underscores
        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        return bool(re.match(pattern, nickname))


def get_approval_service() -> ApprovalAccessService:
    """Get or create singleton ApprovalAccessService instance"""
    global _approval_service_instance
    
    if _approval_service_instance is None:
        with _instance_lock:
            if _approval_service_instance is None:
                _approval_service_instance = ApprovalAccessService()
                logger.info("Initialized ApprovalAccessService")
    
    return _approval_service_instance

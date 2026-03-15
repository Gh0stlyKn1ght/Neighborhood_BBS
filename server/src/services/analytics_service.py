"""
Analytics Service - PHASE 4 Week 12

Aggregate-only analytics providing community health metrics:
- User engagement metrics (connected count, messages today)
- Message statistics (avg length, total sent)
- Content filtering metrics (most filtered patterns)
- System health indicators

PRIVACY-FIRST: Only aggregate metrics, NO individual user tracking

Author: AI Assistant
Date: 2026
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import json

from models import db

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Admin analytics service for Neighborhood BBS.
    
    Provides aggregate-only metrics about community activity,
    maintaining strict privacy by never tracking individuals.
    
    Philosophy:
    - Community health > User surveillance
    - Aggregate metrics only
    - No user identification possible
    - Focused on system performance and safety
    """
    
    def __init__(self):
        """Initialize the analytics service"""
        self.db = db
    
    def get_connected_users_count(self) -> int:
        """Get current number of connected users"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Count active sessions (last heartbeat within last 5 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) as count
                FROM connected_users
                WHERE last_heartbeat > ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting connected users count: {e}")
            return 0
    
    def get_messages_today_count(self) -> int:
        """Get total messages sent today (aggregate only)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM chat_messages
                WHERE timestamp >= ?
            ''', (today_start,))
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting messages today count: {e}")
            return 0
    
    def get_average_message_length(self) -> float:
        """Get average length of messages sent today"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute('''
                SELECT AVG(LENGTH(content)) as avg_length
                FROM chat_messages
                WHERE timestamp >= ?
            ''', (today_start,))
            
            result = cursor.fetchone()
            avg_length = float(result[0]) if result and result[0] else 0.0
            conn.close()
            
            return round(avg_length, 2)
        except Exception as e:
            logger.error(f"Error getting average message length: {e}")
            return 0.0
    
    def get_most_filtered_patterns(self, limit: int = 10) -> List[Dict]:
        """
        Get most frequently filtered patterns.
        Aggregate metric - NO user identification.
        
        Args:
            limit: Number of top patterns to return
            
        Returns:
            List of {pattern, count, percentage} dicts
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get total violations
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM moderation_violations
            ''')
            
            total_result = cursor.fetchone()
            total_violations = total_result[0] if total_result else 1
            
            # Get top patterns by violation count
            cursor.execute('''
                SELECT pattern, COUNT(*) as count
                FROM moderation_violations
                GROUP BY pattern
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))
            
            patterns = []
            for row in cursor.fetchall():
                pattern = row[0]
                count = row[1]
                percentage = round((count / total_violations) * 100, 2)
                
                patterns.append({
                    'pattern': pattern,
                    'count': count,
                    'percentage': percentage
                })
            
            conn.close()
            return patterns
        except Exception as e:
            logger.error(f"Error getting filtered patterns: {e}")
            return []
    
    def get_messages_by_hour_today(self) -> List[Dict]:
        """Get message distribution by hour for today"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as count
                FROM chat_messages
                WHERE timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            ''', (today_start,))
            
            hourly_data = []
            for row in cursor.fetchall():
                hour = row[0]
                count = row[1]
                
                hourly_data.append({
                    'hour': f"{hour}:00",
                    'messages': count
                })
            
            conn.close()
            return hourly_data
        except Exception as e:
            logger.error(f"Error getting hourly message distribution: {e}")
            return []
    
    def get_active_users_trend(self, days: int = 7) -> List[Dict]:
        """Get trend of active users over last N days"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            trend = []
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).date()
                date_start = datetime.combine(date, datetime.min.time())
                date_end = datetime.combine(date, datetime.max.time())
                
                cursor.execute('''
                    SELECT COUNT(DISTINCT session_id) as users
                    FROM connected_users
                    WHERE last_heartbeat BETWEEN ? AND ?
                ''', (date_start, date_end))
                
                result = cursor.fetchone()
                user_count = result[0] if result else 0
                
                trend.append({
                    'date': str(date),
                    'active_users': user_count
                })
            
            conn.close()
            return list(reversed(trend))
        except Exception as e:
            logger.error(f"Error getting active users trend: {e}")
            return []
    
    def get_moderation_stats(self) -> Dict:
        """Get aggregate moderation statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total violations today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM moderation_violations
                WHERE timestamp >= ?
            ''', (today_start,))
            
            result = cursor.fetchone()
            stats['violations_today'] = result[0] if result else 0
            
            # Violations by severity
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM moderation_violations
                WHERE timestamp >= ?
                GROUP BY severity
            ''', (today_start,))
            
            severity_breakdown = {}
            for row in cursor.fetchall():
                severity_breakdown[row[0]] = row[1]
            
            stats['by_severity'] = severity_breakdown
            
            # Users affected today (aggregate - count changed, not who)
            cursor.execute('''
                SELECT COUNT(DISTINCT target_user) as users
                FROM moderation_violations
                WHERE timestamp >= ?
            ''', (today_start,))
            
            result = cursor.fetchone()
            stats['users_with_violations'] = result[0] if result else 0
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting moderation stats: {e}")
            return {}
    
    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        try:
            health = {}
            
            # Connected users
            health['connected_users'] = self.get_connected_users_count()
            
            # Messages today
            health['messages_today'] = self.get_messages_today_count()
            
            # Average message length
            health['avg_message_length'] = self.get_average_message_length()
            
            # Most filtered patterns
            health['top_patterns'] = self.get_most_filtered_patterns(5)
            
            # Moderation stats
            health['moderation'] = self.get_moderation_stats()
            
            # System timestamp
            health['timestamp'] = datetime.utcnow().isoformat()
            
            return health
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        try:
            dashboard = {
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'connected_users': self.get_connected_users_count(),
                    'messages_today': self.get_messages_today_count(),
                    'avg_message_length': self.get_average_message_length(),
                },
                'top_patterns': self.get_most_filtered_patterns(10),
                'hourly_distribution': self.get_messages_by_hour_today(),
                'user_trend': self.get_active_users_trend(7),
                'moderation': self.get_moderation_stats(),
            }
            
            return dashboard
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def get_analytics_report(self, time_range: str = 'today') -> Dict:
        """
        Generate a detailed analytics report.
        
        Args:
            time_range: 'today', 'week', 'month'
            
        Returns:
            Comprehensive analytics report
        """
        try:
            # Determine date range
            if time_range == 'today':
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == 'week':
                start_date = datetime.utcnow() - timedelta(days=7)
            elif time_range == 'month':
                start_date = datetime.utcnow() - timedelta(days=30)
            else:
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            report = {
                'time_range': time_range,
                'period_start': start_date.isoformat(),
                'period_end': datetime.utcnow().isoformat(),
            }
            
            # Message stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    AVG(LENGTH(content)) as avg_length,
                    MIN(LENGTH(content)) as min_length,
                    MAX(LENGTH(content)) as max_length
                FROM chat_messages
                WHERE timestamp >= ?
            ''', (start_date,))
            
            row = cursor.fetchone()
            if row:
                report['messages'] = {
                    'total': row[0],
                    'avg_length': round(float(row[1]) if row[1] else 0, 2),
                    'min_length': row[2],
                    'max_length': row[3],
                }
            
            # Violations stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT target_user) as affected_users
                FROM moderation_violations
                WHERE timestamp >= ?
            ''', (start_date,))
            
            row = cursor.fetchone()
            if row:
                report['violations'] = {
                    'total': row[0],
                    'unique_users_affected': row[1],
                }
            
            # Top patterns
            cursor.execute('''
                SELECT pattern, COUNT(*) as count
                FROM moderation_violations
                WHERE timestamp >= ?
                GROUP BY pattern
                ORDER BY count DESC
                LIMIT 10
            ''', (start_date,))
            
            report['top_patterns'] = [
                {'pattern': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return report
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            return {}


# Service instance
analytics_service = AnalyticsService()

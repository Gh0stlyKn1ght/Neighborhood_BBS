"""
Utility functions for Neighborhood BBS
"""

import re
from datetime import datetime
import bleach


def validate_username(username):
    """Validate username format"""
    if not username or len(username) < 2 or len(username) > 30:
        return False
    return re.match(r'^[a-zA-Z0-9_-]+$', username) is not None


def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Optional field
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_input(text, max_length=1000):
    """Sanitize user input - remove HTML tags and limit length (XSS prevention)
    
    Uses bleach library for robust HTML sanitization, superior to regex-based approach.
    Removes all HTML tags and entities to prevent XSS attacks.
    """
    if not text:
        return ""
    # Use bleach for robust HTML sanitization (removes ALL HTML/entities safely)
    text = bleach.clean(text, tags=[], strip=True)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Limit length
    return text[:max_length]


def format_timestamp(dt):
    """Format datetime for display"""
    if isinstance(dt, str):
        return dt
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'Unknown'


def get_read_time(text):
    """Estimate reading time in minutes"""
    words = len(text.split())
    minutes = max(1, words // 200)
    return minutes


def paginate(items, page=1, per_page=20):
    """Paginate items"""
    total = len(items)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }

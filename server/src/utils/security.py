"""
Security utilities - Password hashing and verification
"""

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    """Hash a password for secure storage"""
    return generate_password_hash(password)


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)

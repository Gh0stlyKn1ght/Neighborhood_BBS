#!/usr/bin/env python3
"""
Database initialization script for Neighborhood BBS
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models import db, ChatRoom

def init_database():
    """Initialize the database"""
    print("Initializing Neighborhood BBS database...")
    
    # Initialize database schema
    db.init_db()
    print("✓ Database schema created")
    
    # Create default chat rooms
    default_rooms = [
        ('general', 'General neighborhood discussion'),
        ('announcements', 'Important community announcements'),
        ('events', 'Local events and gatherings'),
        ('help', 'Ask for and offer help'),
        ('marketplace', 'Buy, sell, and trade items'),
    ]
    
    for name, description in default_rooms:
        room_id = ChatRoom.create(name, description)
        if room_id:
            print(f"✓ Created chat room: {name}")
        else:
            print(f"  (Room '{name}' already exists)")
    
    print("\n✅ Database initialized successfully!")
    print("Ready to start the application.")

if __name__ == '__main__':
    init_database()

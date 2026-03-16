"""
Bulletins module for admin announcements and notifications
- Persistent admin bulletins (independent of message storage privacy mode)
- Real-time broadcasts via WebSocket
- Category support (general, maintenance, important, etc.)
- Expiration and pinning support
"""

from .service import BullletinService
from . import websocket_events  # Register WebSocket event handlers

__all__ = ['BullletinService']

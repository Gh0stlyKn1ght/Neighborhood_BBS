"""
Bulletins WebSocket events
Real-time bulletin updates and broadcasts
"""

from flask_socketio import emit, join_room, leave_room
from server import socketio
from bulletins.service import BullletinService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bulletin_service = BullletinService()


# WebSocket room for all bulletin subscribers
BULLETINS_ROOM = 'bulletins_broadcast'


@socketio.on('join_bulletins')
def on_join_bulletins(data):
    """
    User subscribes to bulletin updates
    Joins the bulletins broadcast room and gets current bulletins
    """
    try:
        # Join the broadcaster room
        join_room(BULLETINS_ROOM)
        
        # Send current bulletins on join
        bulletins = bulletin_service.get_active_bulletins()
        
        emit('bulletins_list', {
            'bulletins': bulletins,
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(bulletins)
        })
        
        logger.info("Client joined bulletins broadcast room")
    
    except Exception as e:
        logger.error(f"Error in join_bulletins: {e}")
        emit('error', {'message': str(e)})


@socketio.on('leave_bulletins')
def on_leave_bulletins(data):
    """User unsubscribes from bulletin updates"""
    try:
        leave_room(BULLETINS_ROOM)
        logger.info("Client left bulletins broadcast room")
    
    except Exception as e:
        logger.error(f"Error in leave_bulletins: {e}")


@socketio.on('get_bulletins')
def on_get_bulletins(data):
    """
    Client requests current bulletins
    Emits: bulletins_list event with all active bulletins
    """
    try:
        include_expired = data.get('include_expired', False) if data else False
        
        bulletins = bulletin_service.list_bulletins(
            active_only=True,
            include_expired=include_expired
        )
        
        emit('bulletins_list', {
            'bulletins': bulletins,
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(bulletins)
        })
        
        logger.debug(f"Sent {len(bulletins)} bulletins to client")
    
    except Exception as e:
        logger.error(f"Error in get_bulletins: {e}")
        emit('error', {'message': str(e)})


# ============================================================================
# SERVER-SIDE BROADCAST FUNCTIONS (called from admin routes)
# Use these when creating/updating/deleting bulletins to broadcast to all clients
# ============================================================================

def broadcast_bulletin_created(bulletin):
    """
    Broadcast new bulletin to all connected clients
    Called from bulletins routes when POST /api/bulletins
    """
    try:
        socketio.emit('bulletin_created', {
            'bulletin': bulletin,
            'timestamp': datetime.utcnow().isoformat()
        }, room=BULLETINS_ROOM)
        
        logger.info(f"Broadcast: bulletin created (id={bulletin['id']})")
    
    except Exception as e:
        logger.error(f"Error broadcasting bulletin_created: {e}")


def broadcast_bulletin_updated(bulletin):
    """
    Broadcast bulletin update to all connected clients
    Called from bulletins routes when PUT /api/bulletins/<id>
    """
    try:
        socketio.emit('bulletin_updated', {
            'bulletin': bulletin,
            'timestamp': datetime.utcnow().isoformat()
        }, room=BULLETINS_ROOM)
        
        logger.info(f"Broadcast: bulletin updated (id={bulletin['id']})")
    
    except Exception as e:
        logger.error(f"Error broadcasting bulletin_updated: {e}")


def broadcast_bulletin_deleted(bulletin_id):
    """
    Broadcast bulletin deletion to all connected clients
    Called from bulletins routes when DELETE /api/bulletins/<id>
    """
    try:
        socketio.emit('bulletin_deleted', {
            'id': bulletin_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=BULLETINS_ROOM)
        
        logger.info(f"Broadcast: bulletin deleted (id={bulletin_id})")
    
    except Exception as e:
        logger.error(f"Error broadcasting bulletin_deleted: {e}")


def broadcast_bulletin_pinned(bulletin):
    """
    Broadcast bulletin pin status change to all connected clients
    Called from bulletins routes when POST /api/bulletins/<id>/pin or /unpin
    """
    try:
        action = 'pinned' if bulletin.get('is_pinned') else 'unpinned'
        
        socketio.emit('bulletin_status_changed', {
            'bulletin': bulletin,
            'action': action,
            'timestamp': datetime.utcnow().isoformat()
        }, room=BULLETINS_ROOM)
        
        logger.info(f"Broadcast: bulletin {action} (id={bulletin['id']})")
    
    except Exception as e:
        logger.error(f"Error broadcasting bulletin status change: {e}")

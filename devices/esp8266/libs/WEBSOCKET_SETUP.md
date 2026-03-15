# WebSocket Setup for ESP8266 Neighborhood BBS

This file explains how to add real-time WebSocket support to the ESP8266 client.

## Overview

The current implementation uses **HTTP polling** for maximum compatibility. This guide adds **WebSocket support** for real-time, bidirectional communication with the server.

## Benefits of WebSocket

- **Real-time updates** - Instant message delivery without polling
- **Lower latency** - Direct connection to server
- **Reduced bandwidth** - Single persistent connection instead of repeated HTTP requests
- **Better battery life** - Device wakes less frequently

## Requirements

1. **MicroPython v1.23+** (with WebSocket capability)
2. **micropython-websockets** library
3. **Space:** ~25KB RAM for WebSocket library
4. **Server support:** Server must expose WebSocket endpoint at `/ws`

## Installation

### 1. Get the WebSocket Library

```bash
git clone https://github.com/aaugustin/websockets.git
cd websockets/python-embedded/microwython
```

Or download directly:
- https://github.com/aaugustin/websockets/tree/main/python-embedded/micropython

### 2. Upload to Device

```bash
# Install ampy if needed
pip install adafruit-ampy

# Upload WebSocket library
ampy --port COM3 put websocket.py /

# Or using rshell
rshell
> cp websocket.py /pyboard/
```

### 3. Create WebSocket Wrapper

Create `websocket_client.py` in `libs/`:

```python
# libs/websocket_client.py
"""WebSocket client for Neighborhood BBS (Optional real-time support)"""

import asyncio
import json
import websocket

class WebSocketBBSClient:
    """Real-time WebSocket client for Neighborhood BBS"""
    
    def __init__(self, server_host, server_port, use_ssl=False):
        self.host = server_host
        self.port = server_port
        self.use_ssl = use_ssl
        self.ws = None
        self.connected = False
        self.message_callbacks = []
    
    def _build_url(self):
        protocol = "wss" if self.use_ssl else "ws"
        return f"{protocol}://{self.host}:{self.port}/ws"
    
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            url = self._build_url()
            print(f"Connecting to WebSocket: {url}")
            self.ws = websocket.connect(url)
            self.connected = True
            print("WebSocket connected!")
            return True
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            self.connected = False
            return False
    
    async def send_message(self, room_id, message, author):
        """Send message via WebSocket"""
        if not self.connected:
            print("Error: WebSocket not connected")
            return False
        
        try:
            data = {
                "type": "message",
                "room_id": room_id,
                "content": message,
                "author": author
            }
            await self.ws.send(json.dumps(data))
            print(f"Message sent to room {room_id}")
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    async def listen(self):
        """Listen for incoming messages"""
        if not self.connected:
            print("Error: WebSocket not connected")
            return
        
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                # Trigger callbacks
                for callback in self.message_callbacks:
                    await callback(data)
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.connected = False
    
    def on_message(self, callback):
        """Register message callback"""
        self.message_callbacks.append(callback)
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print("WebSocket disconnected")
```

### 4. Hybrid Implementation (HTTP + WebSocket)

For maximum flexibility, use HTTP polling as fallback:

```python
# main.py (modified)
import network
import json
import time
import asyncio

# Import both clients
from main import NeighborhoodBBSClient  # HTTP fallback
# from libs.websocket_client import WebSocketBBSClient  # WebSocket (optional)

class HybridBBSClient:
    """Uses WebSocket when available, falls back to HTTP polling"""
    
    def __init__(self, config):
        self.config = config
        self.use_websocket = config.get("use_websocket", False)
        self.http_client = NeighborhoodBBSClient(config)
        self.ws_client = None
        
        if self.use_websocket:
            from libs.websocket_client import WebSocketBBSClient
            self.ws_client = WebSocketBBSClient(
                config.get("server_host"),
                config.get("server_port"),
                use_ssl=config.get("use_https", False)
            )
    
    async def send_message(self, room_id, message, author=None):
        """Send via WebSocket or HTTP"""
        if self.use_websocket and self.ws_client and self.ws_client.connected:
            return await self.ws_client.send_message(room_id, message, author)
        else:
            # Fall back to HTTP
            return self.http_client.send_message(room_id, message, author)
    
    async def listen_messages(self):
        """Listen for real-time messages via WebSocket"""
        if self.use_websocket and self.ws_client:
            await self.ws_client.listen()
```

## Configuration

Update `config.json` to enable WebSocket:

```json
{
  "ssid": "Your_WiFi_SSID",
  "password": "Your_WiFi_Password",
  "server_host": "192.168.1.100",
  "server_port": 8080,
  "use_https": false,
  "use_websocket": true,
  "device_name": "ESP8266_Neighborhood_1"
}
```

## Server Requirements

Your Neighborhood BBS server must expose a WebSocket endpoint:

```python
# server/src/routes/websocket_routes.py (example)
from flask_socketio import emit, on

@socketio.on('connect')
def handle_connect():
    emit('response', {'data': 'Connected'})

@socketio.on('message')
def handle_message(data):
    room_id = data.get('room_id')
    message = data.get('content')
    author = data.get('author')
    
    # Save and broadcast message
    emit('new_message', {
        'room_id': room_id,
        'content': message,
        'author': author
    }, broadcast=True)
```

## Testing

### Test with REPL

```python
import asyncio
from libs.websocket_client import WebSocketBBSClient

async def test():
    client = WebSocketBBSClient("192.168.1.100", 8080)
    await client.connect()
    await client.send_message("general", "Hello from ESP8266!", "esp-device-1")
    await client.disconnect()

asyncio.run(test())
```

### Monitor Connection

Enable debug output:

```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### "Module not found: websocket"
```bash
ampy --port COM3 put websocket.py /
```

### "Connection refused"
- Verify server is running: `python server/src/main.py`
- Check server supports WebSocket endpoint
- Verify firewall allows port 8080

### Memory errors
- WebSocket library too large for device
- Use HTTP polling instead (default)
- Or use minimal WebSocket library

### Connection drops
- Check WiFi signal strength
- Add reconnection logic with exponential backoff
- Reduce message frequency

## References

- **MicroPython WebSockets:** https://github.com/aaugustin/websockets
- **Socket.IO Support:** https://github.com/miguelgrinberg/python-socketio
- **Alternative (simpler):** https://github.com/danni/micropython-websockets

## When to Use WebSocket vs HTTP

| Scenario | Recommended |
|----------|-------------|
| Mobile devices (limited bandwidth) | **WebSocket** |
| Battery-powered IoT devices | **HTTP Polling** (wakes less) |
| Real-time collaboration needed | **WebSocket** |
| No server WebSocket support | **HTTP Polling** |
| Limited device RAM (<100KB free) | **HTTP Polling** |
| High-frequency updates needed | **WebSocket** |

## Current Status

✅ **HTTP Polling:** Fully implemented and tested  
⚠️ **WebSocket:** Optional, not included by default  
✅ **Hybrid:** Can implement both with fallback logic

The default HTTP polling implementation provides the best balance of:
- Compatibility across all MicroPython versions
- Memory efficiency
- Reliability and error recovery
- Battery-friendly operation (periodic polling)

Add WebSocket support if you need real-time updates for your use case.

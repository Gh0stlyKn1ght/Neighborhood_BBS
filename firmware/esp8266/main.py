# Neighborhood BBS - ESP8266 Main Application
# MicroPython implementation for ESP8266
#
# Configuration: Create config.json file with:
# {
#   "ssid": "Your_WiFi_SSID",
#   "password": "Your_WiFi_Password",
#   "server_host": "192.168.1.100",
#   "server_port": 8080,
#   "use_https": false,
#   "device_name": "ESP8266_Neighborhood_1",
#   "reconnect_interval": 300
# }

import network
import urequests
import json
import time
import os

# Load configuration from file
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "ssid": "Your_WiFi_SSID",
    "password": "Your_WiFi_Password",
    "server_host": "192.168.1.100",
    "server_port": 8080,
    "use_https": False,
    "device_name": "ESP8266_Neighborhood_1",
    "reconnect_interval": 300,
    "timeout": 10
}

class ConfigManager:
    """Load and manage configuration from file"""
    @staticmethod
    def load():
        """Load configuration from file or use defaults"""
        try:
            if CONFIG_FILE in os.listdir():
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

    @staticmethod
    def save(config):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            print("Config saved")
        except Exception as e:
            print(f"Error saving config: {e}")

class NeighborhoodBBSClient:
    """ESP8266 client for Neighborhood BBS"""

    def __init__(self, config):
        self.config = config
        self.device_name = config.get("device_name", "ESP8266_Device")
        self.wifi_connected = False
        self.server_connected = False
        self.wifi = network.WLAN(network.STA_IF)
        self.request_count = 0
        self.last_heartbeat = 0

    def _build_url(self, path):
        """Build full URL with protocol"""
        protocol = "https" if self.config.get("use_https") else "http"
        host = self.config.get("server_host", "localhost")
        port = self.config.get("server_port", 8080)
        return f"{protocol}://{host}:{port}{path}"

    def connect_wifi(self):
        """Connect to WiFi with retry logic"""
        ssid = self.config.get("ssid")
        password = self.config.get("password")
        timeout = self.config.get("timeout", 10)

        print(f"Connecting to WiFi: {ssid}")
        self.wifi.active(True)
        self.wifi.connect(ssid, password)

        retry_count = 0
        max_retries = timeout

        while retry_count < max_retries:
            if self.wifi.isconnected():
                ip = self.wifi.ifconfig()[0]
                print(f"WiFi connected! IP: {ip}")
                self.wifi_connected = True
                return True

            retry_count += 1
            time.sleep(1)
            print(".", end="")

        print("\nFailed to connect to WiFi after {} seconds".format(timeout))
        self.wifi_connected = False
        return False

    def send_message(self, room_id, message, author=None):
        """Send a message to a chat room"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return False

        if not message or len(message) > 1000:
            print("Error: Message invalid (empty or too long)")
            return False

        try:
            author = author or self.device_name
            url = self._build_url("/api/chat/send")

            data = {
                "room_id": room_id,
                "author": author,
                "content": message
            }
            headers = {"Content-Type": "application/json"}

            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            # Check for 201 (Created) - correct status for POST
            if response.status_code == 201:
                print(f"Message sent to room {room_id}")
                self.request_count += 1
                response.close()
                return True
            elif response.status_code == 429:
                print("Error: Rate limit exceeded. Wait before sending more messages.")
                response.close()
                return False
            else:
                print(f"Error: Server returned {response.status_code}")
                response.close()
                return False

        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def get_messages(self, room_id, limit=10):
        """Get recent messages from a room"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []

        # Enforce API limits (max 100)
        limit = min(limit, 100)

        try:
            url = self._build_url(f"/api/chat/history/{room_id}?limit={limit}")
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                response.close()
                return messages
            else:
                print(f"Error getting messages: {response.status_code}")
                response.close()
                return []

        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    def get_rooms(self):
        """Get list of available chat rooms"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []

        try:
            url = self._build_url("/api/chat/rooms")
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                data = response.json()
                rooms = data.get("rooms", [])
                response.close()
                return rooms
            else:
                print(f"Error getting rooms: {response.status_code}")
                response.close()
                return []

        except Exception as e:
            print(f"Error getting rooms: {e}")
            return []

    def heartbeat(self):
        """Send periodic heartbeat to server"""
        if not self.wifi_connected:
            return False

        try:
            url = self._build_url("/health")
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            success = response.status_code == 200
            response.close()

            if success:
                self.server_connected = True
            else:
                self.server_connected = False

            return success

        except Exception as e:
            print(f"Heartbeat error: {e}")
            self.server_connected = False
            return False

    def get_status(self):
        """Get current client status"""
        return {
            "device": self.device_name,
            "wifi": "connected" if self.wifi_connected else "disconnected",
            "server": "connected" if self.server_connected else "disconnected",
            "requests": self.request_count,
            "uptime": time.time()
        }

def main():
    """Main application entry point"""
    print("\n" + "="*50)
    print("Neighborhood BBS - ESP8266 Client")
    print("="*50 + "\n")

    # Load configuration
    print("Loading configuration...")
    config = ConfigManager.load()

    # Initialize client
    client = NeighborhoodBBSClient(config)

    # Connect to WiFi
    if not client.connect_wifi():
        print("Cannot proceed without WiFi connection")
        print("Please check your network and config.json")
        return

    # Test server connection
    print(f"\nTesting server connection...")
    print(f"Server: {config.get('server_host')}:{config.get('server_port')}")

    if client.heartbeat():
        print("Server is online!")
        client.server_connected = True
    else:
        print("Warning: Cannot reach server")
        print("Make sure the server is running and reachable")

    # Get available rooms
    print("\nFetching available rooms...")
    rooms = client.get_rooms()
    if rooms:
        print(f"Found {len(rooms)} room(s):")
        for room in rooms:
            print(f"  - Room {room.get('id')}: {room.get('name')}")
    else:
        print("No rooms available")

    # Send test message
    print("\nSending test message...")
    if client.send_message(1, "Hello from ESP8266 - Testing connection!"):
        print("Test message sent successfully!")
    else:
        print("Failed to send test message")

    # Get recent messages
    print("\nFetching recent messages...")
    messages = client.get_messages(1, limit=5)
    if messages:
        print(f"Recent messages ({len(messages)}):")
        for msg in messages:
            author = msg.get('author', 'Unknown')
            content = msg.get('content', '')
            print(f"  [{author}] {content}")
    else:
        print("No messages available")

    # Main loop
    print("\n" + "="*50)
    print("Client running. Sending heartbeat every {} seconds.".format(
        config.get("reconnect_interval", 300)
    ))
    print("Press Ctrl+C to stop.")
    print("="*50 + "\n")

    heartbeat_interval = config.get("reconnect_interval", 300)

    try:
        while True:
            time.sleep(heartbeat_interval)

            if client.heartbeat():
                print("[OK] Heartbeat successful")
            else:
                print("[!] Server unreachable, attempting reconnect...")
                if client.connect_wifi() and client.heartbeat():
                    print("[OK] Reconnected to server")
                else:
                    print("[!] Reconnect failed")

    except KeyboardInterrupt:
        print("\n\nShutdown requested")
        status = client.get_status()
        print("Final status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()

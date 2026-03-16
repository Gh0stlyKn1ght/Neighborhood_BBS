# Neighborhood BBS - ESP8266 Main Application
# MicroPython implementation for ESP8266 with User Authentication
#
# Configuration: Create config.json file with:
# {
#   "ssid": "Your_WiFi_SSID",
#   "password": "Your_WiFi_Password",
#   "server_host": "192.168.1.100",
#   "server_port": 8080,
#   "use_https": false,
#   "device_name": "ESP8266_Neighborhood_1",
#   "reconnect_interval": 300,
#   "timeout": 10,
#   "auth_mode": "user",
#   "username": "esp_device",
#   "user_password": "YourPassword123"
# }
#
# Auth modes: "anonymous" (old style) or "user" (JWT authenticated)

import network
import urequests
import json
import time
import os

# Load configuration from file
CONFIG_FILE = "config.json"
TOKEN_FILE = "token.json"
DEFAULT_CONFIG = {
    "ssid": "Your_WiFi_SSID",
    "password": "Your_WiFi_Password",
    "server_host": "192.168.1.100",
    "server_port": 8080,
    "use_https": False,
    "device_name": "ESP8266_Neighborhood_1",
    "reconnect_interval": 300,
    "timeout": 10,
    "auth_mode": "user",
    "username": "esp_device",
    "user_password": "YourPassword123"
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
    """ESP8266 client for Neighborhood BBS with optional user authentication"""

    def __init__(self, config):
        self.config = config
        self.device_name = config.get("device_name", "ESP8266_Device")
        self.wifi_connected = False
        self.server_connected = False
        self.auth_token = None
        self.auth_mode = config.get("auth_mode", "user")  # "user" or "anonymous"
        self.username = config.get("username", "")
        self.wifi = network.WLAN(network.STA_IF)
        self.request_count = 0
        self.last_heartbeat = 0
        
        # Load token from file if using user auth
        if self.auth_mode == "user":
            self._load_token()

    def _build_url(self, path):
        """Build full URL with protocol"""
        protocol = "https" if self.config.get("use_https") else "http"
        host = self.config.get("server_host", "localhost")
        port = self.config.get("server_port", 8080)
        return f"{protocol}://{host}:{port}{path}"

    def _save_token(self):
        """Save authentication token to file"""
        try:
            token_data = {
                "token": self.auth_token,
                "username": self.username,
                "timestamp": time.time()
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f)
            print("Token saved to {}".format(TOKEN_FILE))
        except Exception as e:
            print(f"Error saving token: {e}")

    def _load_token(self):
        """Load authentication token from file"""
        try:
            if TOKEN_FILE in os.listdir():
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                    self.auth_token = token_data.get("token")
                    self.username = token_data.get("username", self.username)
                    print("Token loaded from {}".format(TOKEN_FILE))
                    return True
        except Exception as e:
            print(f"Error loading token: {e}")
        return False

    def _get_auth_headers(self):
        """Get headers with JWT token if authenticated"""
        headers = {"Content-Type": "application/json"}
        if self.auth_mode == "user" and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def login(self):
        """Login with username and password to get JWT token"""
        if self.auth_mode != "user":
            print("Login: Auth mode is not 'user'")
            return False

        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return False

        username = self.config.get("username", "")
        password = self.config.get("user_password", "")

        if not username or not password:
            print("Error: Username and password required in config")
            return False

        try:
            url = self._build_url("/api/user/login")
            data = {
                "username_or_email": username,
                "password": password
            }
            headers = {"Content-Type": "application/json"}

            print("Attempting login as: {}".format(username))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("token")
                self.username = result.get("username")
                response.close()

                # Save token
                self._save_token()
                print("Login successful! Token received.")
                return True
            else:
                error = "Unknown error"
                try:
                    data = response.json()
                    error = data.get("error", error)
                except:
                    pass
                print("Login failed: {} (Status: {})".format(error, response.status_code))
                response.close()
                return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def register(self):
        """Register new user account"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return False

        username = self.config.get("username", "")
        password = self.config.get("user_password", "")
        email = self.config.get("email", "")

        if not username or not password or not email:
            print("Error: Username, password, and email required in config")
            return False

        try:
            url = self._build_url("/api/user/register")
            data = {
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password
            }
            headers = {"Content-Type": "application/json"}

            print("Attempting to register: {}".format(username))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 201:
                result = response.json()
                self.auth_token = result.get("token")
                self.username = result.get("username")
                response.close()

                # Save token
                self._save_token()
                print("Registration successful! User: {}".format(username))
                return True
            else:
                error = "Unknown error"
                try:
                    data = response.json()
                    error = data.get("error", error)
                except:
                    pass
                print("Registration failed: {} (Status: {})".format(error, response.status_code))
                response.close()
                return False

        except Exception as e:
            print(f"Registration error: {e}")
            return False

    def verify_token(self):
        """Verify current authentication token"""
        if self.auth_mode != "user" or not self.auth_token:
            return False

        try:
            url = self._build_url("/api/user/verify-token")
            headers = self._get_auth_headers()

            response = urequests.get(
                url,
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                response.close()
                return is_valid
            else:
                response.close()
                return False

        except Exception as e:
            print(f"Token verification error: {e}")
            return False

    def connect_wifi(self):
        """Connect to WiFi with retry logic"""
        ssid = self.config.get("ssid")
        password = self.config.get("password")
        timeout = self.config.get("timeout", 10)

        print("Connecting to WiFi: {}".format(ssid))
        self.wifi.active(True)
        self.wifi.connect(ssid, password)

        retry_count = 0
        max_retries = timeout

        while retry_count < max_retries:
            if self.wifi.isconnected():
                ip = self.wifi.ifconfig()[0]
                print("WiFi connected! IP: {}".format(ip))
                self.wifi_connected = True
                return True

            retry_count += 1
            time.sleep(1)
            print(".", end="")

        print("\nFailed to connect to WiFi after {} seconds".format(timeout))
        self.wifi_connected = False
        return False

    def send_message(self, room_id, message, author=None):
        """Send a message to a chat room (authenticated or anonymous)"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return False

        if not message or len(message) > 5000:
            print("Error: Message invalid (empty or too long)")
            return False

        try:
            # Use authenticated endpoint if user mode and token available
            if self.auth_mode == "user" and self.auth_token:
                return self._send_message_authenticated(room_id, message)
            else:
                return self._send_message_anonymous(room_id, message, author)

        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def _send_message_authenticated(self, room_id, message):
        """Send message using authenticated endpoint"""
        try:
            url = self._build_url("/api/chat/send-message-auth")

            data = {
                "room_id": room_id,
                "text": message
            }
            headers = self._get_auth_headers()

            print("Sending authenticated message to room {}...".format(room_id))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 201:
                result = response.json()
                print("Message sent as {} (ID: {})".format(
                    result.get("username"),
                    result.get("message_id")
                ))
                self.request_count += 1
                response.close()
                return True
            elif response.status_code == 401:
                print("Error: Token expired or invalid. Re-authenticating...")
                response.close()
                # Try to refresh token
                if self.login():
                    return self._send_message_authenticated(room_id, message)
                return False
            elif response.status_code == 429:
                print("Error: Rate limit exceeded. Wait before sending more messages.")
                response.close()
                return False
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return False

        except Exception as e:
            print(f"Error sending authenticated message: {e}")
            return False

    def _send_message_anonymous(self, room_id, message, author=None):
        """Send message using anonymous endpoint"""
        try:
            author = author or self.device_name
            url = self._build_url("/api/chat/send-message")

            data = {
                "room_id": room_id,
                "author": author,
                "content": message
            }
            headers = {"Content-Type": "application/json"}

            print("Sending anonymous message to room {}...".format(room_id))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 201:
                print("Message sent from {}".format(author))
                self.request_count += 1
                response.close()
                return True
            elif response.status_code == 429:
                print("Error: Rate limit exceeded. Wait before sending more messages.")
                response.close()
                return False
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return False

        except Exception as e:
            print(f"Error sending anonymous message: {e}")
            return False

    def get_messages(self, room_id, limit=50):
        """Get recent messages from a chat room (authenticated or anonymous)"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []

        # Enforce API limits (max 100)
        limit = min(limit, 100)

        try:
            # Use authenticated endpoint if user mode and token available
            if self.auth_mode == "user" and self.auth_token:
                return self._get_messages_authenticated(room_id, limit)
            else:
                return self._get_messages_anonymous(room_id, limit)

        except Exception as e:
            print("Error getting messages: {}".format(e))
            return []

    def _get_messages_authenticated(self, room_id, limit=50):
        """Get messages using authenticated endpoint"""
        try:
            url = self._build_url("/api/chat/rooms/{}/messages-auth?limit={}".format(
                room_id, limit
            ))
            headers = self._get_auth_headers()

            print("Fetching authenticated messages from room {}...".format(room_id))
            response = urequests.get(
                url,
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                self.request_count += 1
                response.close()
                return messages
            elif response.status_code == 401:
                print("Error: Token expired or invalid. Re-authenticating...")
                response.close()
                # Try to refresh token
                if self.login():
                    return self._get_messages_authenticated(room_id, limit)
                return []
            elif response.status_code == 404:
                print("Error: Room {} not found".format(room_id))
                response.close()
                return []
            elif response.status_code == 429:
                print("Error: Rate limit exceeded. Wait before requesting more messages.")
                response.close()
                return []
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return []

        except Exception as e:
            print("Error getting authenticated messages: {}".format(e))
            return []

    def _get_messages_anonymous(self, room_id, limit=50):
        """Get messages using anonymous endpoint"""
        try:
            url = self._build_url("/api/chat/history/{}?limit={}".format(
                room_id, limit
            ))

            print("Fetching anonymous messages from room {}...".format(room_id))
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                self.request_count += 1
                response.close()
                return messages
            elif response.status_code == 404:
                print("Error: Room {} not found".format(room_id))
                response.close()
                return []
            elif response.status_code == 429:
                print("Error: Rate limit exceeded. Wait before requesting more messages.")
                response.close()
                return []
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return []

        except Exception as e:
            print("Error getting anonymous messages: {}".format(e))
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
                print("Error getting rooms: {}".format(response.status_code))
                response.close()
                return []

        except Exception as e:
            print("Error getting rooms: {}".format(e))
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
            print("Heartbeat error: {}".format(e))
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

    # Handle user authentication if configured
    auth_mode = config.get("auth_mode", "anonymous")
    if auth_mode == "user":
        print("\nAuthentication mode: USER")
        print("Attempting to authenticate as registered user...")
        
        # Try to load existing token
        if client._load_token():
            print("Loaded existing authentication token")
            
            # Verify token is still valid
            if client.verify_token():
                print("Token is valid! Authenticated as: {}".format(client.username))
            else:
                print("Token expired or invalid. Re-authenticating...")
                # Try to login with config credentials
                if client.login():
                    print("Successfully re-authenticated")
                else:
                    print("Re-authentication failed. Falling back to anonymous mode...")
                    client.auth_mode = "anonymous"
        else:
            # No token found, try to login
            print("No existing token found. Attempting login...")
            if client.login():
                print("Successfully authenticated as: {}".format(client.username))
            else:
                print("Login failed. Attempting to register new account...")
                if client.register():
                    print("Successfully registered and authenticated as: {}".format(client.username))
                else:
                    print("Registration failed. Falling back to anonymous mode...")
                    client.auth_mode = "anonymous"
    else:
        print("\nAuthentication mode: ANONYMOUS")

    # Test server connection
    print("\nTesting server connection...")
    server_host = config.get("server_host")
    server_port = config.get("server_port")
    print("Server: {}:{}".format(server_host, server_port))

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
        print("Found {} room(s):".format(len(rooms)))
        for room in rooms:
            room_id = room.get("id")
            room_name = room.get("name")
            print("  - Room {}: {}".format(room_id, room_name))
    else:
        print("No rooms available")

    # Send test message
    print("\nSending test message...")
    auth_marker = " (as {})".format(client.username) if client.auth_mode == "user" else " (anonymous)"
    test_msg = "Hello from ESP8266 - Testing connection!{}".format(auth_marker)
    if client.send_message(1, test_msg):
        print("Test message sent successfully!")
    else:
        print("Failed to send test message")

    # Get recent messages
    print("\nFetching recent messages...")
    messages = client.get_messages(1, limit=5)
    if messages:
        print("Recent messages ({}):".format(len(messages)))
        for msg in messages:
            author = msg.get("author") or msg.get("username", "Unknown")
            content = msg.get("content") or msg.get("text", "")
            timestamp = msg.get("created_at", "")
            print("  [{}] {}: {}".format(timestamp, author, content))
    else:
        print("No messages available")

    # Main loop
    print("\n" + "="*50)
    reconnect_interval = config.get("reconnect_interval", 300)
    print("Client running. Sending heartbeat every {} seconds.".format(reconnect_interval))
    if client.auth_mode == "user":
        print("Authenticated as: {}".format(client.username))
    print("Press Ctrl+C to stop.")
    print("="*50 + "\n")

    try:
        while True:
            time.sleep(reconnect_interval)

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
            print("  {}: {}".format(key, value))

if __name__ == "__main__":
    main()

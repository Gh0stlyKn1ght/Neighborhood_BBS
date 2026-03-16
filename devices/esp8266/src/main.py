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
import re

# Load configuration from file
CONFIG_FILE = "config.json"
TOKEN_FILE = "token.json"

# Security constraints
MAX_MESSAGE_LENGTH = 5000
MAX_DEVICE_NAME_LENGTH = 64
MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_LENGTH = 255
MAX_EMAIL_LENGTH = 255
MAX_TIMEOUT = 60
MIN_TIMEOUT = 1
MAX_RECONNECT_INTERVAL = 3600
MIN_RECONNECT_INTERVAL = 10
MAX_RESPONSE_SIZE = 50000  # Prevent buffer overflow (in bytes)
MAX_RECURSION_DEPTH = 3

# Pagination & Performance
DEFAULT_PAGE_SIZE = 10  # Messages per page (memory efficient)
MAX_PAGE_SIZE = 50      # Server-side limit
DEFAULT_RETRY_ATTEMPTS = 3  # Network retry attempts
RETRY_BACKOFF = 2  # Exponential backoff multiplier

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

class SecurityValidator:
    """Validate and sanitize inputs for security"""
    
    @staticmethod
    def validate_room_id(room_id):
        """Validate room_id is a positive integer"""
        if not isinstance(room_id, int) or room_id <= 0:
            raise ValueError("Room ID must be positive integer")
        if room_id > 65535:
            raise ValueError("Room ID too large")
        return room_id
    
    @staticmethod
    def validate_message(message):
        """Validate message content and sanitize for XSS"""
        if not isinstance(message, str):
            raise TypeError("Message must be string")
        if not message or len(message) == 0:
            raise ValueError("Message cannot be empty")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError("Message too long (max {})".format(MAX_MESSAGE_LENGTH))
        # Basic HTML entity encoding to prevent XSS
        sanitized = SecurityValidator._html_encode(message)
        return sanitized
    
    @staticmethod
    def validate_device_name(name):
        """Validate device name"""
        if not isinstance(name, str) or not name:
            raise ValueError("Device name must be non-empty string")
        if len(name) > MAX_DEVICE_NAME_LENGTH:
            raise ValueError("Device name too long")
        # Allow alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Device name contains invalid characters")
        return name
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not isinstance(username, str) or not username:
            raise ValueError("Username must be non-empty string")
        if len(username) < 3 or len(username) > MAX_USERNAME_LENGTH:
            raise ValueError("Username length must be 3-{}".format(MAX_USERNAME_LENGTH))
        # Allow alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username contains invalid characters")
        return username
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not isinstance(password, str) or not password:
            raise ValueError("Password must be non-empty string")
        if len(password) < 8 or len(password) > MAX_PASSWORD_LENGTH:
            raise ValueError("Password length must be 8-{}".format(MAX_PASSWORD_LENGTH))
        return password
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not isinstance(email, str) or not email:
            raise ValueError("Email must be non-empty string")
        if len(email) > MAX_EMAIL_LENGTH:
            raise ValueError("Email too long")
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        return email
    
    @staticmethod
    def validate_timeout(timeout):
        """Validate timeout value"""
        if not isinstance(timeout, (int, float)):
            raise TypeError("Timeout must be number")
        if timeout < MIN_TIMEOUT or timeout > MAX_TIMEOUT:
            raise ValueError("Timeout must be {}-{}".format(MIN_TIMEOUT, MAX_TIMEOUT))
        return int(timeout)
    
    @staticmethod
    def validate_reconnect_interval(interval):
        """Validate reconnect interval"""
        if not isinstance(interval, (int, float)):
            raise TypeError("Reconnect interval must be number")
        if interval < MIN_RECONNECT_INTERVAL or interval > MAX_RECONNECT_INTERVAL:
            raise ValueError("Reconnect interval must be {}-{}".format(
                MIN_RECONNECT_INTERVAL, MAX_RECONNECT_INTERVAL))
        return int(interval)
    
    @staticmethod
    def validate_limit(limit):
        """Validate message limit parameter"""
        if not isinstance(limit, int):
            raise TypeError("Limit must be integer")
        if limit <= 0 or limit > 100:
            raise ValueError("Limit must be 1-100")
        return limit
    
    @staticmethod
    def _html_encode(text):
        """Basic HTML entity encoding for XSS prevention"""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        result = text
        for char, entity in replacements.items():
            result = result.replace(char, entity)
        return result

class MessagePageIterator:
    """Memory-efficient pagination for message fetching"""
    
    def __init__(self, client, room_id, page_size=DEFAULT_PAGE_SIZE):
        self.client = client
        self.room_id = room_id
        self.page_size = min(page_size, MAX_PAGE_SIZE)  # Cap at server limit
        self.offset = 0
        self.has_more = True
        self.total_fetched = 0
    
    def fetch_next_page(self):
        """Fetch next page of messages, returns list or None on error"""
        if not self.has_more:
            return None
        
        messages = self.client.get_messages(self.room_id, self.page_size)
        
        if not messages:
            self.has_more = False
            return None
        
        self.offset += len(messages)
        self.total_fetched += len(messages)
        
        # If we got fewer messages than requested, no more pages
        if len(messages) < self.page_size:
            self.has_more = False
        
        return messages
    
    def fetch_all(self, max_messages=100):
        """Fetch all messages up to max_messages, returns complete list"""
        all_messages = []
        while self.has_more and self.total_fetched < max_messages:
            page = self.fetch_next_page()
            if page:
                all_messages.extend(page)
            else:
                break
        return all_messages

class RateLimiter:
    """Handle exponential backoff for rate limiting"""
    
    def __init__(self, max_backoff=300):
        self.last_rate_limit = 0
        self.backoff_time = 1
        self.max_backoff = max_backoff
    
    def on_rate_limit(self):
        """Record rate limit hit and calculate backoff time"""
        self.last_rate_limit = time.time()
        print("Rate limited. Waiting {}s before retry...".format(self.backoff_time))
        return self.backoff_time
    
    def should_retry(self):
        """Check if enough time has passed since last rate limit"""
        if self.last_rate_limit == 0:
            return True
        elapsed = time.time() - self.last_rate_limit
        if elapsed >= self.backoff_time:
            # Exponential backoff: double the wait time, cap at max
            self.backoff_time = min(self.backoff_time * 2, self.max_backoff)
            self.last_rate_limit = 0
            return True
        return False
    
    def reset(self):
        """Reset rate limiter after success"""
        self.last_rate_limit = 0
        self.backoff_time = 1

class ConfigManager:
    """Load and manage configuration from file"""
    
    @staticmethod
    def load():
        """Load configuration from file or use defaults with validation"""
        try:
            if CONFIG_FILE in os.listdir():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Validate all config values
                    return ConfigManager._validate_config(config)
        except Exception as e:
            print("Error loading config: {}".format(e))
        return DEFAULT_CONFIG

    @staticmethod
    def _validate_config(config):
        """Validate all configuration parameters"""
        try:
            # Validate device name
            if "device_name" in config:
                config["device_name"] = SecurityValidator.validate_device_name(
                    config["device_name"])
            
            # Validate timeout
            if "timeout" in config:
                config["timeout"] = SecurityValidator.validate_timeout(
                    config["timeout"])
            
            # Validate reconnect interval
            if "reconnect_interval" in config:
                config["reconnect_interval"] = SecurityValidator.validate_reconnect_interval(
                    config["reconnect_interval"])
            
            # Validate auth fields
            if "username" in config and config["username"]:
                config["username"] = SecurityValidator.validate_username(
                    config["username"])
            
            if "user_password" in config and config["user_password"]:
                config["user_password"] = SecurityValidator.validate_password(
                    config["user_password"])
            
            if "email" in config and config["email"]:
                config["email"] = SecurityValidator.validate_email(
                    config["email"])
            
            # Ensure port is valid
            if "server_port" in config:
                port = config["server_port"]
                if not isinstance(port, int) or port <= 0 or port > 65535:
                    raise ValueError("Invalid server port")
            
            return config
        except Exception as e:
            print("Config validation error: {}. Using defaults.".format(e))
            return DEFAULT_CONFIG

    @staticmethod
    def save(config):
        """Save configuration to file"""
        try:
            # Validate before saving
            config = ConfigManager._validate_config(config)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            print("Config saved")
        except Exception as e:
            print("Error saving config: {}".format(e))

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
        self.rate_limiter = RateLimiter()
        self._auth_retry_count = 0  # Prevent infinite recursion on auth failure
        
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
            print("ERROR: Auth mode is not 'user'. Set auth_mode='user' in config")
            return False

        if not self.wifi_connected:
            print("ERROR: Cannot login while offline. Connect to WiFi first")
            return False

        username = self.config.get("username", "")
        password = self.config.get("user_password", "")

        if not username:
            print("ERROR: Username not found in config. Add 'username' field")
            return False
        if not password:
            print("ERROR: Password not found in config. Add 'user_password' field")
            return False

        try:
            # Validate credentials format
            username = SecurityValidator.validate_username(username)
            password = SecurityValidator.validate_password(password)
        except (ValueError, TypeError) as e:
            print("ERROR: Invalid username/password format: {}".format(e))
            return False

        try:
            url = self._build_url("/api/user/login")
            data = {
                "username_or_email": username,
                "password": password
            }
            headers = {"Content-Type": "application/json"}

            print(">> Logging in as: {}".format(username))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                # Buffer overflow protection
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("ERROR: Server response too large (possible attack)")
                    response.close()
                    return False
                
                result = response.json()
                self.auth_token = result.get("token")
                self.username = result.get("username")
                response.close()

                # Save token
                self._save_token()
                print("SUCCESS: Login successful! Welcome {}".format(self.username))
                return True
            elif response.status_code == 401:
                print("ERROR: Invalid username or password. Check credentials and try again")
                response.close()
                return False
            elif response.status_code == 404:
                print("ERROR: User account not found. Please register first")
                response.close()
                return False
            elif response.status_code == 429:
                print("ERROR: Too many login attempts. Wait before retrying")
                response.close()
                return False
            else:
                error = "Unknown error"
                try:
                    data = response.json()
                    error = data.get("error", error)
                except:
                    pass
                print("ERROR: Login failed - {} (HTTP {})".format(error, response.status_code))
                response.close()
                return False

        except Exception as e:
            print("ERROR: Login failed - {}".format(e))
            return False

    def register(self):
        """Register new user account"""
        if not self.wifi_connected:
            print("ERROR: Cannot register while offline. Connect to WiFi first")
            return False

        username = self.config.get("username", "")
        password = self.config.get("user_password", "")
        email = self.config.get("email", "")

        if not username:
            print("ERROR: Username not found in config. Add 'username' field")
            return False
        if not password:
            print("ERROR: Password not found in config. Add 'user_password' field")
            return False
        if not email:
            print("ERROR: Email not found in config. Add 'email' field")
            return False

        try:
            # Validate credentials and email
            username = SecurityValidator.validate_username(username)
            password = SecurityValidator.validate_password(password)
            email = SecurityValidator.validate_email(email)
        except (ValueError, TypeError) as e:
            print("ERROR: Invalid input - {}".format(e))
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

            print(">> Registering new account: {}".format(username))
            response = urequests.post(
                url,
                data=json.dumps(data),
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 201:
                # Buffer overflow protection
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("ERROR: Server response too large (possible attack)")
                    response.close()
                    return False
                
                result = response.json()
                self.auth_token = result.get("token")
                self.username = result.get("username")
                response.close()

                # Save token
                self._save_token()
                print("SUCCESS: Registration complete! Welcome {}".format(username))
                print("INFO: User email: {}".format(email))
                return True
            elif response.status_code == 409:
                print("ERROR: Username or email already taken. Choose different credentials")
                response.close()
                return False
            elif response.status_code == 400:
                try:
                    data = response.json()
                    error = data.get("error", "Invalid registration data")
                except:
                    error = "Invalid registration data"
                print("ERROR: Registration failed - {}".format(error))
                response.close()
                return False
            elif response.status_code == 429:
                print("ERROR: Too many registration attempts. Wait before retrying")
                response.close()
                return False
            else:
                error = "Unknown error"
                try:
                    data = response.json()
                    error = data.get("error", error)
                except:
                    pass
                print("ERROR: Registration failed - {} (HTTP {})".format(error, response.status_code))
                response.close()
                return False

        except Exception as e:
            print("ERROR: Registration failed - {}".format(e))
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

        try:
            # Validate input parameters
            room_id = SecurityValidator.validate_room_id(room_id)
            message = SecurityValidator.validate_message(message)
        except (ValueError, TypeError) as e:
            print("Input validation error: {}".format(e))
            return False

        # Check rate limiter
        if not self.rate_limiter.should_retry():
            print("Rate limited. Skipping message send.")
            return False

        try:
            # Use authenticated endpoint if user mode and token available
            if self.auth_mode == "user" and self.auth_token:
                return self._send_message_authenticated(room_id, message)
            else:
                return self._send_message_anonymous(room_id, message, author)

        except Exception as e:
            print("Error sending message: {}".format(e))
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
                self.rate_limiter.reset()  # Success: reset rate limiter
                response.close()
                return True
            elif response.status_code == 401:
                print("Error: Token expired or invalid. Re-authenticating...")
                response.close()
                # Prevent infinite recursion on auth failure
                if self._auth_retry_count >= MAX_RECURSION_DEPTH:
                    print("Max re-authentication attempts reached")
                    return False
                # Try to refresh token
                self._auth_retry_count += 1
                if self.login():
                    self._auth_retry_count = 0
                    return self._send_message_authenticated(room_id, message)
                self._auth_retry_count = 0
                return False
            elif response.status_code == 429:
                # Rate limit: use exponential backoff
                backoff = self.rate_limiter.on_rate_limit()
                response.close()
                return False
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return False

        except Exception as e:
            print("Error sending authenticated message: {}".format(e))
            return False

    def _send_message_anonymous(self, room_id, message, author=None):
        """Send message using anonymous endpoint"""
        try:
            author = author or self.device_name
            # Validate author name
            author = SecurityValidator.validate_device_name(author)
            
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
                self.rate_limiter.reset()  # Success: reset rate limiter
                response.close()
                return True
            elif response.status_code == 429:
                # Rate limit: use exponential backoff
                backoff = self.rate_limiter.on_rate_limit()
                response.close()
                return False
            else:
                print("Error: Server returned {}".format(response.status_code))
                response.close()
                return False

        except (ValueError, TypeError) as e:
            print("Input validation error: {}".format(e))
            return False
        except Exception as e:
            print("Error sending anonymous message: {}".format(e))
            return False

    def get_messages(self, room_id, limit=50):
        """Get recent messages from a chat room (authenticated or anonymous)"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []

        try:
            # Validate input parameters
            room_id = SecurityValidator.validate_room_id(room_id)
            limit = SecurityValidator.validate_limit(limit)
        except (ValueError, TypeError) as e:
            print("Input validation error: {}".format(e))
            return []

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

            print("Fetching {} authenticated messages from room {}...".format(limit, room_id))
            response = urequests.get(
                url,
                headers=headers,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                # Buffer overflow protection: check response size
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("Error: Response too large ({} bytes, max {})".format(
                        response_size, MAX_RESPONSE_SIZE))
                    response.close()
                    return []
                
                # Robust response parsing
                try:
                    data = response.json()
                except (ValueError, KeyError) as e:
                    print("Error parsing response JSON: {}".format(e))
                    response.close()
                    return []
                
                messages = data.get("messages", [])
                if not isinstance(messages, list):
                    print("Error: Response messages not a list")
                    response.close()
                    return []
                
                self.request_count += 1
                self.rate_limiter.reset()
                response.close()
                print("Fetched {} messages".format(len(messages)))
                return messages
            elif response.status_code == 401:
                print("Error: Token expired or invalid (401). Re-authenticating...")
                response.close()
                # Prevent infinite recursion
                if self._auth_retry_count >= MAX_RECURSION_DEPTH:
                    print("Max re-authentication attempts ({}) reached".format(
                        MAX_RECURSION_DEPTH))
                    return []
                # Try to refresh token
                self._auth_retry_count += 1
                if self.login():
                    self._auth_retry_count = 0
                    return self._get_messages_authenticated(room_id, limit)
                self._auth_retry_count = 0
                return []
            elif response.status_code == 404:
                print("Error: Room {} not found (404)".format(room_id))
                response.close()
                return []
            elif response.status_code == 429:
                backoff = self.rate_limiter.on_rate_limit()
                response.close()
                return []
            elif response.status_code == 500:
                print("Error: Server error (500). Check server logs.".format())
                response.close()
                return []
            else:
                print("Error: Unexpected status {} from server".format(response.status_code))
                response.close()
                return []

        except Exception as e:
            print("Error fetching authenticated messages: {}".format(e))
            return []

    def _get_messages_anonymous(self, room_id, limit=50):
        """Get messages using anonymous endpoint"""
        try:
            url = self._build_url("/api/chat/history/{}?limit={}".format(
                room_id, limit
            ))

            print("Fetching {} anonymous messages from room {}...".format(limit, room_id))
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                # Buffer overflow protection: check response size
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("Error: Response too large ({} bytes, max {})".format(
                        response_size, MAX_RESPONSE_SIZE))
                    response.close()
                    return []
                
                # Robust response parsing
                try:
                    data = response.json()
                except (ValueError, KeyError) as e:
                    print("Error parsing response JSON: {}".format(e))
                    response.close()
                    return []
                
                messages = data.get("messages", [])
                if not isinstance(messages, list):
                    print("Error: Response messages not a list")
                    response.close()
                    return []
                
                self.request_count += 1
                self.rate_limiter.reset()
                response.close()
                print("Fetched {} messages".format(len(messages)))
                return messages
            elif response.status_code == 404:
                print("Error: Room {} not found (404)".format(room_id))
                response.close()
                return []
            elif response.status_code == 429:
                backoff = self.rate_limiter.on_rate_limit()
                response.close()
                return []
            elif response.status_code == 500:
                print("Error: Server error (500). Check server logs.")
                response.close()
                return []
            else:
                print("Error: Unexpected status {} from server".format(response.status_code))
                response.close()
                return []

        except Exception as e:
            print("Error fetching anonymous messages: {}".format(e))
            return []

    def _parse_json_response(self, response, expected_key=None):
        """Safely parse JSON response, returns data or None on error"""
        try:
            if response.status_code == 200:
                # Size check
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("Error: Response too large ({} bytes)".format(response_size))
                    return None
                
                # Parse JSON
                try:
                    data = response.json()
                except (ValueError, KeyError) as e:
                    print("Error: Invalid JSON response: {}".format(e))
                    return None
                
                # Validate structure
                if expected_key and expected_key not in data:
                    print("Error: Missing expected key '{}' in response".format(expected_key))
                    return None
                
                return data
            else:
                return None
        finally:
            response.close()

    def get_paginated_messages(self, room_id, max_messages=100):
        """Get messages with automatic pagination for memory efficiency"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []
        
        try:
            page_iterator = MessagePageIterator(self, room_id, DEFAULT_PAGE_SIZE)
            return page_iterator.fetch_all(max_messages)
        except Exception as e:
            print("Error fetching paginated messages: {}".format(e))
            return []

    def get_rooms(self):
        """Get list of available chat rooms with robust error handling"""
        if not self.wifi_connected:
            print("Error: Not connected to WiFi")
            return []

        try:
            url = self._build_url("/api/chat/rooms")
            print("Fetching available rooms...")
            response = urequests.get(
                url,
                timeout=self.config.get("timeout", 10)
            )

            if response.status_code == 200:
                # Size check
                response_size = len(response.content) if hasattr(response, 'content') else 0
                if response_size > MAX_RESPONSE_SIZE:
                    print("Error: Response too large ({} bytes)".format(response_size))
                    response.close()
                    return []
                
                # Parse JSON
                try:
                    data = response.json()
                except (ValueError, KeyError) as e:
                    print("Error parsing rooms response: {}".format(e))
                    response.close()
                    return []
                
                # Validate structure
                rooms = data.get("rooms", [])
                if not isinstance(rooms, list):
                    print("Error: Rooms response not a list")
                    response.close()
                    return []
                
                response.close()
                print("Found {} available room(s)".format(len(rooms)))
                return rooms
            elif response.status_code == 500:
                print("Error: Server error (500). Check server logs.")
                response.close()
                return []
            else:
                print("Error: Server returned {} when fetching rooms".format(
                    response.status_code))
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

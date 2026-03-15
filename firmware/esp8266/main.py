# Neighborhood BBS - ESP8266 Main Application
# MicroPython implementation

import network
import urequests
import json
import time
from umqtt.simple import MQTTClient

# Configuration
SSID = "Your_WiFi_SSID"
PASSWORD = "Your_WiFi_Password"
SERVER_HOST = "192.168.1.100"
SERVER_PORT = 8080
DEVICE_NAME = "ESP8266_Neighborhood_1"
MQTT_BROKER = "192.168.1.100"
MQTT_PORT = 1883

class NeighborhoodBBSClient:
    def __init__(self):
        self.device_name = DEVICE_NAME
        self.connected = False
        self.wifi = network.WLAN(network.STA_IF)
        self.mqtt_client = None
        
    def connect_wifi(self):
        """Connect to WiFi"""
        print(f"Connecting to WiFi: {SSID}")
        self.wifi.active(True)
        self.wifi.connect(SSID, PASSWORD)
        
        timeout = 20
        while timeout > 0:
            if self.wifi.isconnected():
                print("WiFi connected!")
                print(f"IP: {self.wifi.ifconfig()[0]}")
                self.connected = True
                return True
            timeout -= 1
            time.sleep(1)
            print(".", end="")
        
        print("\nFailed to connect to WiFi")
        return False
    
    def send_message(self, room, message):
        """Send a message to the server"""
        if not self.connected:
            print("Not connected to server")
            return False
        
        try:
            url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/chat/send"
            data = {
                "room_id": room,
                "author": self.device_name,
                "content": message
            }
            headers = {"Content-Type": "application/json"}
            response = urequests.post(url, data=json.dumps(data), headers=headers)
            
            if response.status_code == 200:
                print(f"Message sent to {room}")
                return True
            else:
                print(f"Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def get_messages(self, room, limit=10):
        """Get recent messages from a room"""
        try:
            url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/chat/history/{room}?limit={limit}"
            response = urequests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
            return []
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def heartbeat(self):
        """Send periodic heartbeat to server"""
        try:
            url = f"http://{SERVER_HOST}:{SERVER_PORT}/health"
            response = urequests.get(url)
            return response.status_code == 200
        except:
            return False

def main():
    """Main application entry point"""
    print("Neighborhood BBS - ESP8266 Client")
    print("=" * 40)
    
    # Initialize client
    client = NeighborhoodBBSClient()
    
    # Connect to WiFi
    if not client.connect_wifi():
        print("Cannot proceed without WiFi connection")
        return
    
    # Test server connection
    print(f"Testing server connection: {SERVER_HOST}:{SERVER_PORT}")
    if client.heartbeat():
        print("Server is online!")
    else:
        print("Warning: Cannot reach server")
    
    # Example: Send a message
    print("\nSending test message...")
    client.send_message("general", "Hello from ESP8266!")
    
    # Example: Get messages
    print("\nRecent messages in 'general' room:")
    messages = client.get_messages("general", limit=5)
    for msg in messages:
        print(f"  [{msg.get('author', 'Unknown')}] {msg.get('content', '')}")
    
    # Keep the client running
    print("\nClient running. Press Ctrl+C to stop.")
    while True:
        time.sleep(300)  # Heartbeat every 5 minutes
        if client.heartbeat():
            print("Heartbeat OK")
        else:
            print("Server unreachable, reconnecting...")
            if client.connect_wifi():
                print("Reconnected")

if __name__ == "__main__":
    main()

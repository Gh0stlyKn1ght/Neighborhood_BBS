# ESP8266 Firmware - Complete Implementation Guide
**Neighborhood BBS | Phase 4 Week 15 | Official Documentation**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Quick Start](#quick-start)
4. [Installation by Approach](#installation-by-approach)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Limitations & Roadmap](#limitations--roadmap)
9. [FAQ](#faq)

---

## Overview

**Neighborhood BBS** on ESP8266 provides:
- 📡 **WiFi connectivity** to Neighborhood BBS servers
- 💬 **Real-time chat** functionality
- 📱 **Lightweight footprint** (fits in 4MB ESP8266 flash)
- 🔄 **Auto-reconnect** with exponential backoff
- ⛔ **Rate limiting** to prevent server overload
- 🔐 **HTTPS support** for secure connections

### Two Implementation Paths

| Approach | Language | Use Case | Skill Level |
|----------|----------|----------|-------------|
| **MicroPython** | Python | Prototyping, testing | Beginner → Intermediate |
| **Arduino IDE** | C++ | Production, performance | Intermediate → Advanced |

**Recommendation for beginners:** Start with MicroPython  
**Recommendation for production:** Use Arduino IDE

---

## Hardware Requirements

### ESP8266 Boards
✅ **Supported:**
- NodeMCU 1.0 (ESP-12E) - **RECOMMENDED**
- Wemos D1 Mini
- Generic ESP-12F breakout

⚠️ **Minimal Support:**
- ESP-01 (1MB only, limited RAM)
- Custom boards with <2MB flash

❌ **Not Supported:**
- ESP8266-01 cannot flash MicroPython
- Boards <1MB flash memory

### Power & Connectivity
- **Power:** USB 5V recommended (via micro-USB)
  - Alternative: 3.3V regulated supply, 500mA+
- **WiFi:** 802.11 b/g/n (2.4GHz only)
- **Serial:** USB-to-UART adapter (included on most dev boards)

### Accessories
- USB micro-B cable (for flashing)
- Serial terminal software (PuTTY, miniterm, ArduinoIDE)
- Optional: breadboard, LEDs for debugging

---

## Quick Start

### Absolute Fastest Path (5 minutes)

**Prerequisites:**
```bash
pip install esptool adafruit-ampy
```

**Steps:**

1. **Get MicroPython firmware:**
   ```bash
   # Download (LATEST for 2026)
   curl -O https://micropython.org/resources/firmware/esp8266-20260116-v1.24.bin
   # Save as: micropython.bin
   ```

2. **Flash MicroPython:**
   ```bash
   # Connect ESP8266 via USB
   esptool.py --port COM3 erase_flash
   esptool.py --port COM3 write_flash -z 0x0 micropython.bin
   # Wait for completion, then disconnect
   ```
   > **On Linux/Mac:** Replace `COM3` with `/dev/ttyUSB0` or `/dev/cu.usbserial-*`

3. **Upload Neighborhood BBS code:**
   ```bash
   # Create config.json with your WiFi details (see below)
   ampy --port COM3 put config.json /config.json
   ampy --port COM3 put main.py /main.py
   ```

4. **Run:**
   ```bash
   # Open serial monitor
   # (PuTTY: COM3, 115200 baud)
   # Device will auto-connect and show status
   ```

---

## Installation by Approach

### PATH A: MicroPython (Recommended for beginners)

#### Step 1: Download & Flash MicroPython

```bash
# Download latest ESP8266 MicroPython (2026 edition)
# From: https://micropython.org/download/esp8266/

# Erase existing flash
python -m esptool --chip esp8266 --port COM3 erase_flash

# Flash new firmware
python -m esptool --chip esp8266 --port COM3 write_flash -z 0x0 \
  micropython-esp8266-20260116-v1.24.bin

# Expected output:
# Detected chip id: 0x8266
# Writing at 0x00000000... (100%)
# Wrote 634896 bytes at 0x00000000 in 62.5 seconds
```

#### Step 2: Verify Installation

```bash
# Use pyboard/ampy REPL
python -m ampy --port COM3 run -c "import sys; print(sys.version)"

# Output should show:
# MicroPython v1.24 on 2026-01-16
```

#### Step 3: Create Configuration

Create `config.json`:
```json
{
  "ssid": "YOUR_WIFI_NAME",
  "password": "YOUR_WIFI_PASSWORD",
  "server_host": "192.168.1.100",
  "server_port": 8080,
  "use_https": false,
  "device_name": "esp8266_node_1",
  "reconnect_interval": 300,
  "timeout": 10
}
```

#### Step 4: Upload Code

```bash
# Upload configuration
ampy --port COM3 put config.json /config.json

# Upload main application
ampy --port COM3 put main.py /main.py

# Upload is complete when no errors shown
```

#### Step 5: Run Application

```bash
# Method 1: Via ampy (one-time run)
python -m ampy --port COM3 run main.py

# Method 2: Via REPL (interactive)
python -m ampy --port COM3
# >>> import main
# >>> main.main()

# Method 3: Auto-run on boot (create boot.py)
ampy --port COM3 put main.py /boot.py
# Now auto-runs on every power-up
```

Terminal output:
```
==================================================
Neighborhood BBS - ESP8266 Client
==================================================

Loading configuration...
Connecting to WiFi: YOUR_WIFI_NAME
..................
WiFi connected! IP: 192.168.1.45

Testing server connection...
Server: 192.168.1.100:8080
Server is online!

Fetching available rooms...
Found 3 room(s):
  - Room 1: General Chat
  - Room 2: Tech Support
  - Room 3: Off-Topic

Sending test message...
Message sent to room 1

Fetching recent messages...
Recent messages (5):
  [User123] Hello everyone!
  [esp8266_node_1] Hello from ESP8266
```

---

### PATH B: Arduino IDE (For advanced users & production)

#### Step 1: Install Arduino IDE

1. Download from: https://www.arduino.cc/en/software
2. Install on your computer
3. Launch Arduino IDE

#### Step 2: Add ESP8266 Board Support

1. Open **File → Preferences**
2. Find **"Additional Boards Manager URLs"**
3. Paste:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search **"esp8266"**
7. Install **"esp8266 by ESP8266 Community"** (v3.1.2 or later)
8. Wait for download/installation
9. Restart Arduino IDE

#### Step 3: Install Required Libraries

Go to **Sketch → Include Library → Manage Libraries**

**Library 1: WebSockets**
- Search: `WebSockets`
- Author: `Markus Sattler`
- Version: `2.4.0` (latest recommended)
- Click **Install**

**Library 2: ArduinoJson**
- Search: `ArduinoJson`
- Author: `Benoit Blanchon`
- Version: `7.0` or higher
- Click **Install**

#### Step 4: Configure Board Settings

1. Click **Tools → Board** and select:
   - **ESP8266 Boards (2.7.0+) → NodeMCU 1.0 (ESP-12E Module)**

2. Configure upload parameters in **Tools:**
   - **Port:** COM3 (or your device port)
   - **Upload Speed:** 115200
   - **Flash Size:** 4M (1M SPIFFS)
   - **CPU Frequency:** 80 MHz
   - **Baud Rate:** 115200

#### Step 5: Open & Edit Sketch

1. Open: `devices/esp8266/libs/neighborhood_bbs_chat/neighborhood_bbs_chat.ino`
2. Edit configuration at top of file:
   ```cpp
   const char* SSID = "YOUR_WIFI_NAME";
   const char* PASSWORD = "YOUR_WIFI_PASSWORD";
   const char* SYSOP_NAME = "YOUR_HANDLE";
   ```

#### Step 6: Upload Sketch

1. Click **Sketch → Upload** (or Ctrl+U)
2. Watch the console for upload progress:
   ```
   Compiling sketch...
   Uploading 268048 bytes to flash (code: 249200, RAM: 18848)
   ....... (dots indicate progress)
   Upload complete.
   ```
3. Device should reset automatically

#### Step 7: View Output

1. Open **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. Device will show startup messages and BBS landing page

---

## Configuration

### MicroPython Config (config.json)

```json
{
  "ssid": "MyWiFiNetwork",                    // ← Your WiFi network name
  "password": "MySecurePassword",             // ← WiFi password
  "server_host": "192.168.1.100",            // ← Server IP or hostname
  "server_port": 8080,                        // ← Server port (default 8080)
  "use_https": false,                         // ← HTTPS enabled? (rarely needed)
  "device_name": "esp8266_kitchen",          // ← Your device's display name
  "reconnect_interval": 300,                  // ← Heartbeat seconds (5 minutes)
  "timeout": 10                               // ← Request timeout in seconds
}
```

**Configuration Tips:**

| Setting | Notes |
|---------|-------|
| `ssid` | Case-sensitive. Hidden networks NOT supported. |
| `password` | Must be 8+ characters. ASCII only. |
| `server_host` | Use IP (192.168.x.x) NOT hostname for reliability |
| `server_port` | Default is 8080. Match your server config. |
| `use_https` | Set `true` only if server has valid SSL cert. ESP8266 has no certificate validation. |
| `device_name` | Max 16 chars. Alphanumeric + underscore. |
| `reconnect_interval` | Adjust based on network reliability (60-600 seconds). |
| `timeout` | Lower for fast networks, higher for poor signal. |

### Arduino IDE Configuration (in .ino file)

```cpp
// At top of neighborhood_bbs_chat.ino

const char* SSID = "NEIGHBORHOOD_BBS";           // WiFi AP name
const char* PASSWORD = "neighborhood";           // WiFi AP password
const char* SYSOP_NAME = "MR. GH0STLY";        // Your fancy BBS handle
const uint16_t WS_PORT = 81;                   // WebSocket port
const uint16_t HTTP_PORT = 80;                 // HTTP server port

// Customization
const char* BOARD_NAME = "GH0STL4N";           // ASCII art title
const char* WELCOME_MSG = "Welcome to...";     // Login message
const int MAX_MESSAGES = 20;                   // Chat history size
const int MAX_MESSAGE_LEN = 240;               // Max message length
```

---

## API Reference

### MicroPython Client Methods

```python
# Initialize client
client = NeighborhoodBBSClient(config)

# Connect to WiFi
client.connect_wifi()                          # Returns: True/False

# Check connection status
is_online = client.wifi_connected              # Boolean
is_server_up = client.server_connected         # Boolean

# Send a message
client.send_message(
    room_id=1,
    message="Hello world",
    author="ESP8266_1"
)                                              # Returns: True/False

# Get recent messages
messages = client.get_messages(
    room_id=1,
    limit=10                                   # Max 100
)                                              # Returns: [{}, ...]

# List available rooms
rooms = client.get_rooms()                     # Returns: [{id, name}, ...]

# Health check
client.heartbeat()                             # Returns: True/False

# Get device info
status = client.get_status()
# Returns: {device, wifi, server, requests, uptime}
```

### REST API Endpoints (Server)

These endpoints are called by the ESP8266:

```
GET  /health                      → Health check (no auth)
GET  /api/chat/rooms             → List available rooms
GET  /api/chat/history/{room_id} → Recent messages
POST /api/chat/send              → Send message to room
GET  /api/users/{device_name}    → Device info
```

**Example POST /api/chat/send:**
```json
{
  "room_id": 1,
  "author": "esp8266_node_1",
  "content": "Hello from embedded device"
}
```

**Response (201 Created):**
```json
{
  "status": "ok",
  "message_id": "msg_12345",
  "room_id": 1,
  "timestamp": "2026-03-16T10:30:45Z"
}
```

---

## Troubleshooting

### Issue: Can't find COM port

**Windows:**
1. Connect ESP8266 via USB
2. Open Device Manager (devmgmt.msc)
3. Look for "USB-to-Serial" device
4. Right-click → Properties → Port Settings
5. Note the COM number (e.g., COM3)

**Linux/Mac:**
```bash
# List serial ports
ls /dev/tty.* 

# Or use dmesg
dmesg | grep tty
```

### Issue: Flashing fails with "Failed to connect"

**Solutions (in order):**
1. Try different USB cable (some are charging-only)
2. Hold GPIO0 button while plugging in (resets to flash mode)
3. Decrease baud rate: `--baud 115200` → `--baud 57600`
4. Install CH340 drivers (if device uses those chips)
5. Try different USB port

### Issue: WiFi won't connect

**Checklist:**
- ✅ SSID spelled correctly (case-sensitive)?
- ✅ Password is 8+ characters?
- ✅ WiFi is 2.4GHz (not 5GHz)?
- ✅ Device is within WiFi range?
- ✅ WiFi password has no special characters?

**Debug steps:**
```python
# In REPL:
import network
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.scan()  # See available networks
sta.connect("SSID", "PASSWORD")
sta.ifconfig()  # See IP address
```

### Issue: Can't reach server

**Check:**
1. Server is running: `curl http://192.168.1.100:8080/health`
2. IP address is correct in config.json
3. Firewall allows port 8080
4. Both devices on same WiFi network

**Test connection:**
```python
import urequests
r = urequests.get("http://192.168.1.100:8080/health")
print(r.status_code)  # Should be 200
```

### Issue: Messages not sending

**Check:**
1. Room ID is valid: `client.get_rooms()`
2. Server accepts POST requests
3. Message < 1000 characters
4. Check rate limits (429 response)

### Issue: Out of memory error

**Symptoms:** `MemoryError` on startup or after running

**Causes:**
- Too many messages cached
- Memory leak in connection handling
- Large JSON responses

**Fix:**
```python
# In config.json, reduce polling interval
"reconnect_interval": 600  # Reduce frequency

# Or reduce cache size (Arduino only)
#define MAX_MESSAGES 10  // Instead of 20
```

### Issue: Device keeps rebooting

**Possible causes:**
1. Power supply insufficient (needs 500mA+)
2. Bad USB cable
3. Antenna issues (move away from metal)
4. Corrupt firmware

**Fix:**
```bash
# Full reset
esptool.py --port COM3 erase_flash
esptool.py --port COM3 write_flash 0x0 micropython.bin
```

---

## Limitations & Roadmap

### Current Limitations (v1.0)

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **4MB Flash only** | Limited message history | Clear old messages regularly |
| **No certificate validation** | HTTPS unsafe | Use HTTP on local network |
| **RAM ~50KB** | No large responses | Reduce message limit to 10 |
| **Single WiFi network** | No roaming | Manually update config |
| **No timezone support** | UTC timestamps | Adjust on client side |
| **Polling only (no WebSocket)** | Higher latency | Reduce poll interval to 10s |
| **No persistence** | Messages lost on reset | Archive to server |

### Roadmap (Future Releases)

**v1.1 (Q2 2026):**
- ✅ WebSocket support for real-time updates
- ✅ Better error messages and logging
- ✅ Low-power sleep modes
- ✅ Message compression

**v1.2 (Q3 2026):**
- 🔄 HTTPS certificate validation
- 🔄 User authentication tokens
- 🔄 Message encryption
- 🔄 OTA firmware updates

**v2.0 (Q4 2026):**
- 💡 Mesh networking (device-to-device)
- 💡 Local storage (SPIFFS filesystem)
- 💡 Multiple WiFi networks
- 💡 Custom themes

---

## FAQ

**Q: Can I use this without the Neighborhood BBS server?**  
A: No. The ESP8266 is a client that connects to a server. You need a server running.

**Q: Can I create an ESP8266 that acts as a server?**  
A: Yes, check the Arduino implementation (`neighborhood_bbs_chat.ino`). It creates a WiFi hotspot and HTTP server.

**Q: What's the difference between MicroPython and Arduino?**  
A: MicroPython runs Python code; Arduino runs compiled C++. Arduino is faster and smaller; MicroPython is easier to develop.

**Q: Can I use ESP32 instead?**  
A: ESP32 is more powerful but not officially supported yet. Same code mostly works with minor changes.

**Q: How often should I call heartbeat()?**  
A: Every 5-15 minutes is fine. More frequent = more power usage but quicker detect disconnects.

**Q: What if my WiFi has no password?**  
A: Open WiFi is not secure. Add password to your router.

**Q: Can I run Neighborhood BBS directly on ESP8266 without a server?**  
A: The Arduino implementation (`neighborhood_bbs_chat.ino`) does this! It creates a standalone BBS hotspot.

**Q: How many devices can connect to one ESP8266?**  
A: Arduino version supports ~10 concurrent WebSocket connections (limited by RAM).

**Q: Is my data secure?**  
A: Data is sent over HTTP by default (no encryption). Use HTTPS for sensitive data, but ESP8266 can't validate certificates.

---

## Additional Resources

- **Official MicroPython Docs:** https://docs.micropython.org/
- **Arduino ESP8266 GitHub:** https://github.com/esp8266/Arduino
- **WebSockets Library:** https://github.com/Links2004/arduinoWebsockets
- **ArduinoJson Library:** https://arduinojson.org/
- **Neighborhood BBS Main Repo:** https://github.com/Gh0stlyKn1ght/Neighborhood_BBS

---

## Support

Having issues? Check our:
- **GitHub Issues:** https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues
- **Discord Community:** [link-if-available]
- **Documentation:** This file + README.md in this folder

---

**Last Updated:** March 2026  
**Firmware Version:** 1.0  
**MicroPython Target:** v1.24+  
**Arduino Target:** ESP8266 Board v3.1.2+

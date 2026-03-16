# ESP8266 Firmware for Neighborhood BBS

Run Neighborhood BBS on ESP8266 devices with the retro cyan CRT terminal theme - a portable WiFi-enabled BBS node.

---

## 📚 Complete Documentation

**Start here based on your needs:**

| Document | Purpose | For Whom |
|----------|---------|----------|
| [INSTALLATION.md](INSTALLATION.md) | Complete setup guide (MicroPython or Arduino) | Everyone - START HERE |
| [BUILD_ANALYSIS.md](BUILD_ANALYSIS.md) | Code quality report & production readiness | Developers |
| [DEVICE_SPECS.md](DEVICE_SPECS.md) | Hardware limitations & memory constraints | Technical planners |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Error solutions & diagnostic tools | When things break |
| [README.md](README.md) | This file - Overview & comparison | Quick reference |

**Quick Links:**
- 🚀 **First time?** → [INSTALLATION.md](INSTALLATION.md)
- 🔧 **Having issues?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📊 **Checking quality?** → [BUILD_ANALYSIS.md](BUILD_ANALYSIS.md)
- 💾 **Memory questions?** → [DEVICE_SPECS.md](DEVICE_SPECS.md)

---

## Features

- **Retro Cyan CRT Terminal Interface** - Classic ASCII art aesthetic  
- **WiFi Hotspot Mode** - Creates "NEIGHBORHOOD_BBS" SSID
- **Real-time Chat** - WebSocket-powered messaging
- **Captive Portal** - Auto-redirect for easy access
- **Message Filtering** - Profanity censoring and XSS protection
- **Ring Buffer Chat** - Last 24 messages stored in RAM
- **Local Only** - No internet required, works offline

## Hardware Requirements

- ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
- USB Cable for flashing
- 3.3V USB power supply recommended
- Optional: Heatsink for prolonged use

## Prerequisites

### 1. esptool.py - Flashing Tool

```bash
pip install esptool
```

**Latest Release:** https://github.com/espressif/esptool/releases

### 2. MicroPython Firmware

Get the latest firmware from:
- **Official MicroPython:** https://micropython.org/download/#esp8266
- **MicroPython Latest Release:** https://github.com/micropython/micropython/releases
- **Stable Builds:** https://micropython.org/download/ (Recommended for production)

**Latest ESP8266 Firmware (as of 2026):**
- v1.23+ (Recommended for WebSocket support)
- Download: `micropython-esp8266-*.bin`

### 3. Required MicroPython Libraries

The following are included with standard MicroPython:
- `urequests` - HTTP client (built-in)
- `json` - JSON parsing (built-in)
- `network` - WiFi connectivity (built-in)

### 4. WebSocket Support (Optional)

**Current Implementation:** Uses HTTP polling for maximum compatibility

**For Real-time WebSocket Updates:**
Install WebSocket library on ESP8266:
- **micropython-websockets** - Pure Python implementation
  - GitHub: https://github.com/aaugustin/websockets
  - MicroPython port: https://github.com/danni/micropython-websockets

**Installation:**
```bash
# Via ampy (after uploading main.py)
ampy --port COM3 put micropython_websockets/websocket.py
ampy --port COM3 put micropython_websockets/websocket_common.py
```

Or manually copy WebSocket library files to ESP8266 filesystem.

### 5. Optional: ampy - File Transfer Tool

```bash
pip install adafruit-ampy
```

**Latest:** https://github.com/scientifichacking/ampy

---

## Alternative: Arduino IDE Implementation

Instead of MicroPython, you can also develop for ESP8266 using the Arduino IDE with C++ libraries.

### Arduino IDE Setup

1. **Install Arduino IDE:** https://www.arduino.cc/en/software
2. **Add ESP8266 Board Support:** 
   - File → Preferences → Additional Boards Manager URLs
   - Add: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Tools → Board Manager → Search "ESP8266" → Install

### Required Arduino Libraries

Install via Arduino IDE: **Sketch → Include Library → Manage Libraries**

#### 1. WebSockets by Markus Sattler
- **Purpose:** WebSocket server and client support
- **Search:** "WebSockets"
- **Author:** Markus Sattler
- **Version:** Latest stable (v2.4+)
- **GitHub:** https://github.com/Links2004/arduinoWebsockets
- **Install:** Library Manager search for "WebSockets"

**Usage:**
```cpp
#include <WebSocketsServer.h>

WebSocketsServer webSocket = WebSocketsServer(81);

void setup() {
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  if(type == WStype_TEXT) {
    Serial.printf("got Text: %s\n", payload);
  }
}
```

#### 2. ArduinoJson by Benoit Blanchon
- **Purpose:** JSON serialization and deserialization
- **Search:** "ArduinoJson"
- **Author:** Benoit Blanchon
- **Version:** v7.0+ (latest)
- **GitHub:** https://github.com/bblanchon/ArduinoJson
- **Install:** Library Manager search for "ArduinoJson"

**Usage:**
```cpp
#include <ArduinoJson.h>

StaticJsonDocument<200> doc;
doc["sensor"] = "gps";
doc["message"] = "Hello from ESP8266";

char buffer[256];
serializeJson(doc, buffer);

// Parse JSON
deserializeJson(doc, jsonString);
String value = doc["message"];
```

### Installation Steps

1. Open Arduino IDE
2. Go to **Sketch → Include Library → Manage Libraries**
3. Search for "WebSockets" → Install by Markus Sattler
4. Search for "ArduinoJson" → Install by Benoit Blanchon
5. Restart Arduino IDE
6. Select Board: **Tools → Board → ESP8266 Boards (2.7.0+) → NodeMCU 1.0**
7. Select Port: **Tools → Port → COM#** (your device)

### Arduino vs MicroPython Comparison

| Feature | Arduino IDE | MicroPython |
|---------|------------|------------|
| Language | C++ | Python |
| Learning Curve | Steeper | Gentler |
| Performance | Faster | Slower |
| Memory Usage | Lower | Higher |
| Development Speed | Slower | Faster |
| Debugging | Via Serial | REPL console |
| Libraries | Extensive | Growing |
| **WebSocket** | ✅ Markus Sattler lib | ✅ micropython-websockets |
| **JSON** | ✅ ArduinoJson | ✅ json (built-in) |
| Real-time Chat | Excellent | Good |
| Prototyping | Good | **Excellent** |

### When to Use Each

**Use Arduino IDE when:**
- Performance is critical
- You need industrial-strength code
- Your team knows C++
- Memory is extremely limited
- You need advanced features (ADC, PWM, SPI, I2C)

**Use MicroPython when:**
- Rapid development is priority
- Prototyping and testing
- Your team knows Python
- You prefer REPL debugging
- Memory is adequate (>100KB free)

**Current Implementation:** MicroPython (easier to prototype, Pythonic, good for BBS use case)

## Flashing MicroPython

### 1. Download Firmware

Download the latest ESP8266 MicroPython firmware:

```bash
# Using esptool (automatic download)
python -m esptool --chip esp8266 download_stub
```

Or manually download from: https://micropython.org/download/#esp8266

### 2. Connect Device

Connect your ESP8266 via USB to your computer.

### 3. Flash Firmware

```bash
# Erase flash
esptool.py --port /dev/ttyUSB0 erase_flash  # Linux/Mac
esptool.py --port COM3 erase_flash  # Windows (replace COM3 with your port)

# Flash MicroPython
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_mode dio --flash_size detect 0 micropython-esp8266.bin
```

## Uploading Application Code

### Using ampy

Install ampy:

```bash
pip install adafruit-ampy
```

Upload files:

```bash
ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 put config.json
```

### Using WebREPL

1. Connect to the device REPL
2. Run: `webrepl_setup.py`
3. Upload files via the web interface

## Configuration

Create a `config.json` file on the ESP8266 (same directory as `main.py`):

```json
{
  "ssid": "Your_WiFi_SSID",
  "password": "Your_WiFi_Password",
  "server_host": "192.168.1.100",
  "server_port": 8080,
  "use_https": false,
  "device_name": "ESP8266_Neighborhood_1",
  "reconnect_interval": 300,
  "timeout": 10
}
```

**Note:** If `config.json` is missing, the client will use safe defaults and prompt for configuration. Copy `config.json.example` to `config.json` and edit with your settings.

## Communication Methods

### Current Implementation: HTTP Polling

The ESP8266 client uses **HTTP polling** for compatibility and reliability:

**Advantages:**
- Works with limited ESP8266 RAM (95KB free)
- Compatible with any MicroPython firmware
- Reduced battery drain (polls on interval)
- Simple error recovery

**Methods:**
- `send_message()` - POST to `/api/chat/send`
- `get_messages()` - GET from `/api/chat/history/{room_id}`
- `get_rooms()` - GET from `/api/chat/rooms`
- `heartbeat()` - Health check with server

**Message Polling Interval:** Set by `reconnect_interval` in config (default: 300 seconds = 5 minutes)

### Real-Time WebSocket Support (Optional)

For low-latency real-time messaging, WebSocket can replace HTTP polling:

**Requirements:**
- MicroPython v1.23+
- `micropython-websockets` library (~25KB RAM)

**Benefits:**
- Instant message delivery
- Reduced network overhead
- True real-time collaboration

**Resources:**
- Implementation: [micropython-websockets on GitHub](https://github.com/aaugustin/micropython-websockets)
- Installation: Upload `websocket.py` to device filesystem

**Current Status:** HTTP polling enabled by default for maximum compatibility. Implement WebSocket separately if needed.

## Running the Application

Via REPL:

```python
import main
```

The `main()` function will automatically:
1. Load `config.json` with WiFi and server settings
2. Connect to WiFi
3. Test server connectivity
4. Display available chat rooms
5. Send a test message
6. Enter main loop with periodic heartbeat

---

## Quick Reference: Firmware & Libraries

### MicroPython Firmware Downloads

| Resource | URL | Purpose |
|----------|-----|---------|
| **Official Downloads** | https://micropython.org/download/#esp8266 | Latest stable firmware |
| **GitHub Releases** | https://github.com/micropython/micropython/releases | All versions and pre-releases |
| **Release Notes** | https://micropython.org/resources/docs/en/latest/esp8266/quickstart.html | Setup guide |

**Recommended Firmware:**
- **Stable:** v1.22+ (Proven compatibility)
- **Latest:** v1.23+ (With WebSocket improvements)
- **File:** `micropython-esp8266-*.bin` (Usually ~500KB)

### Required Tools

| Tool | Download | Purpose |
|------|----------|---------|
| **esptool.py** | https://github.com/espressif/esptool/releases | Flash firmware |
| **ampy** | https://github.com/scientifichacking/ampy | Upload files to device |
| **rshell** | https://github.com/dhylands/rshell | File management & REPL |

### WebSocket Libraries (Optional)

| Library | URL | Notes |
|---------|-----|-------|
| **micropython-websockets** | https://github.com/aaugustin/micropython-websockets | Pure Python, ~25KB |
| **MicroPython WebSocket** | https://github.com/danni/micropython-websockets | Alternative implementation |

### Community Resources

- **MicroPython Docs:** https://docs.micropython.org/
- **ESP8266 Pinout:** https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/
- **WebREPL Setup:** https://micropython.org/resources/docs/en/latest/esp8266/tutorial/webrepl.html

---

## Next Steps

1. **Get Latest Firmware:**
   - Download from https://micropython.org/download/#esp8266
   - Flash with esptool.py (see "Flashing MicroPython" section)

2. **Install Required Tools:**
   ```bash
   pip install esptool adafruit-ampy
   ```

3. **Upload Application:**
   ```bash
   ampy --port COM3 put main.py /
   ampy --port COM3 put config.json /
   ```

4. **Test Communication:**
   - Use REPL or WebREPL to run `import main`
   - Watch output for WiFi and server connection status

5. **(Optional) Add WebSocket Support:**
   - Download `websocket.py` from micropython-websockets
   - Upload to device: `ampy --port COM3 put websocket.py /`
   - Modify `main.py` to use WebSocket instead of HTTP polling

## Troubleshooting

### Device Not Detected

```bash
# Check USB connection
ls /dev/ttyUSB*  # Linux/Mac
Get-Content com:  # Windows

# Install USB drivers if needed
```

### WiFi Connection Issues

- Verify SSID and password in `config.json`
- Check WiFi signal strength
- Ensure main server is accessible at the configured `server_host:server_port`
- Test with the REPL to verify configuration loaded:
  ```python
  from src.utils.helpers import ConfigManager
  config = ConfigManager.load()
  print(config)
  ```

### Memory Issues

ESP8266 has limited memory (4MB). Optimize by:
- Using the `--flash_mode dio` option
- Removing unused imports
- Using MicroPython's built-in libraries

## Development

### Main Files

- `main.py` - Application entry point with NeighborhoodBBSClient class
- `config.json` - Runtime configuration (loaded from file)
- `config.json.example` - Configuration template

### Application Classes

**ConfigManager** - Loads/saves `config.json`

- `load()` - Returns config dict, falls back to defaults if file missing
- `save(config)` - Persists configuration to file

**NeighborhoodBBSClient** - Main client implementation

- `connect_wifi()` - Connects to WiFi with retry logic
- `send_message(room_id, message, author)` - Posts message to room
- `get_messages(room_id, limit)` - Retrieves message history
- `get_rooms()` - Lists available chat rooms
- `heartbeat()` - Tests server connectivity
- `get_status()` - Returns connection/uptime status

### Testing

Connect via REPL and test commands:

```python
import main
config = main.ConfigManager.load()
print(f"Config loaded: {config}")

client = main.NeighborhoodBBSClient(config)
client.connect_wifi()
rooms = client.get_rooms()
print(f"Available rooms: {rooms}")
client.send_message(1, "Hello from ESP8266!")
```

## Resources

- MicroPython Docs: https://docs.micropython.org/
- ESP8266 Community: https://github.com/orgs/micropython
- esptool Docs: https://github.com/espressif/esptool

## Next Steps

- [Setup Guide](../../docs/SETUP.md)
- [API Documentation](../../docs/API.md)
- [Development Guide](../../docs/DEVELOPMENT.md)

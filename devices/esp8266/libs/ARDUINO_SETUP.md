# Arduino IDE Setup for ESP8266 - Neighborhood BBS Chat

This guide covers setting up ESP8266 development using Arduino IDE with required libraries for the Neighborhood BBS chat system.

## Required Libraries (For Neighborhood BBS)

Before uploading `neighborhood_bbs_chat.ino`, you MUST install these libraries:

| Library | Author | Minimum Version | Purpose |
|---------|--------|-----------------|---------|
| **WebSockets** | Markus Sattler | 2.4.0 | WebSocket server for real-time chat |
| **ArduinoJson** | Benoit Blanchon | 6.19.0 | JSON encoding/decoding for messages |
| **ESP8266WiFi** | Built-in | - | WiFi AP mode & network |
| **ESP8266WebServer** | Built-in | - | HTTP server for captive portal |
| **DNSServer** | Built-in | - | DNS captive portal redirect |

**Built-in libraries** come with ESP8266 board package and don't need separate installation.

## Installation Summary

### 1. Arduino IDE
Download from https://www.arduino.cc/en/software

### 2. Add ESP8266 Board Support

1. Open Arduino IDE
2. **File → Preferences**
3. Find "Additional Boards Manager URLs"
4. Paste: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
5. Click OK
6. **Tools → Board → Boards Manager**
7. Search "esp8266"
8. Install "esp8266 by ESP8266 Community" (v3.1.2 or latest)
9. Restart Arduino IDE

### 3. Install Required Arduino Libraries

**Sketch → Include Library → Manage Libraries**

#### Library 1: WebSockets (REQUIRED)
```
Search: WebSockets
Author: Markus Sattler
Version: 2.4.0+ (recommended: latest)
Action: Click Install
```
**Installation Check:**
- After install, you should see `#include <WebSocketsServer.h>` in syntax highlighting
- Library location: `Documents/Arduino/libraries/WebSockets/`
- **GitHub**: https://github.com/Links2004/arduinoWebsockets
- **Purpose**: WiFi WebSocket server for real-time chat messaging

#### Library 2: ArduinoJson (REQUIRED)
```
Search: ArduinoJson
Author: Benoit Blanchon
Version: 6.19.0+ (recommended: 7.0+)
Action: Click Install
```
**Installation Check:**
- After install, you should see `#include <ArduinoJson.h>` in syntax highlighting
- Library location: `Documents/Arduino/libraries/ArduinoJson/`
- **GitHub**: https://github.com/bblanchon/ArduinoJson
- **Purpose**: Serialize/deserialize JSON for message protocol

### 4. Select Board & Port

**Tools Menu Configuration:**
- **Board**: `NodeMCU 1.0 (ESP-12E Module)` (or similar ESP8266 variant)
- **Port**: Select your device (COM3, COM4, etc.)
- **Upload Speed**: `115200` baud
- **Flash Size**: `4M (FS:2M OTA:~1019KB)`
- **CPU Frequency**: `80 MHz`
- **Compiler Warnings**: `Default`

## Uploading neighborhood_bbs_chat.ino

### Pre-Upload Checklist
- [ ] Both WebSockets and ArduinoJson libraries installed (see step 3)
- [ ] Board set to "NodeMCU 1.0 (ESP-12E Module)"
- [ ] COM port selected and device visible in Device Manager
- [ ] Upload speed set to 115200
- [ ] sketch_mar15a.ino (or latest) compiled successfully

### Upload Steps

1. Open `neighborhood_bbs_chat.ino` in Arduino IDE
2. Click **Sketch → Verify** (⚠️ Compile first to check for errors)
3. Click **Sketch → Upload** (or Ctrl+U)
4. Wait for upload bar to complete (~15 seconds)
5. Open **Tools → Serial Monitor** (Ctrl+Shift+M)
6. Set baud to `115200`
7. Watch for BBS startup messages

### Expected Serial Output (on success)
```
╔════════════════════════════════════╗
║   NEIGHBORHOOD BBS - ESP8266       ║
║   Booting...
╚════════════════════════════════════╝

✓ WiFi SSID: NEIGHBORHOOD_BBS
✓ IP: 192.168.4.1
✓ DNS Server started
✓ HTTP Server started (port 80)
✓ WebSocket Server started (port 81)

╔════════════════════════════════════╗
║   BBS IS LIVE - READY FOR CHAT    ║
║   http://192.168.4.1              ║
╚════════════════════════════════════╝
```

## Troubleshooting

### "fatal error: WebSocketsServer.h: No such file or directory"
→ **Solution:** Install "WebSockets by Markus Sattler" library
1. Sketch → Include Library → Manage Libraries
2. Search "WebSockets"
3. Click Install (by Markus Sattler)

### "fatal error: ArduinoJson.h: No such file or directory"
→ **Solution:** Install "ArduinoJson by Benoit Blanchon" library
1. Sketch → Include Library → Manage Libraries
2. Search "ArduinoJson"
3. Click Install (by Benoit Blanchon)

### "error: expected unqualified-id before 'return'"
→ **Solution:** Check for syntax errors in the sketch
1. Verify no duplicate lines
2. Check for missing `}` braces
3. Try **Sketch → Verify** before uploading

### Upload fails with "/dev/ttyUSB0 not found" (Linux) or no COM port (Windows)
→ **Solution:** Install ESP8266 drivers
- Windows: CH340 USB driver (search "CH340 driver download")
- Linux: `sudo apt install python3-serial`
- Restart Arduino IDE after driver install

### WebSocket connection fails after upload
→ **Solutions:**
1. Check Serial Monitor for startup messages
2. Ensure device connected to `NEIGHBORHOOD_BBS` WiFi
3. Manually navigate to `http://192.168.4.1`
4. Check firewall isn't blocking ports 80, 81, 53

## Testing Installation

After uploading `neighborhood_bbs_chat.ino`:

1. **Connect to WiFi**: Open your device's WiFi settings
   - SSID: `NEIGHBORHOOD_BBS`
   - No password required (open AP)

2. **Captive Portal**: Browser should auto-open, otherwise:
   - Manually visit `http://192.168.4.1`

3. **Enter Chat**: Click "IRC CHAT" button

4. **Set Nickname**: Type handle, click SET

5. **Send Message**: Type message (max 240 chars), press Ctrl+Enter or SEND

6. **Monitor Serial**: Watch Arduino IDE Serial Monitor (115200 baud) for debug output

## Library Versions Tested

| Library | Version | Date Tested | Status |
|---------|---------|-------------|--------|
| WebSockets | 2.4.0+ | Mar 2026 | ✅ Working |
| ArduinoJson | 6.19.0+ | Mar 2026 | ✅ Working |
| ESP8266 Board | 3.1.2 | Mar 2026 | ✅ Working |

## Community & Support

- **ESP8266 Community**: https://github.com/esp8266/Arduino/issues
- **WebSockets Library**: https://github.com/Links2004/arduinoWebsockets/issues
- **ArduinoJson**: https://github.com/bblanchon/ArduinoJson/issues
- **Neighborhood BBS**: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues

Create a new sketch:

```cpp
#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>

WebSocketsServer webSocket = WebSocketsServer(81);

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin("SSID", "PASSWORD");
  
  // Start WebSocket
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
  
  Serial.println("WebSocket server started on port 81");
}

void loop() {
  webSocket.loop();
  delay(10);
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  if(type == WStype_TEXT) {
    // Parse JSON
    StaticJsonDocument<200> doc;
    deserializeJson(doc, payload);
    
    String message = doc["message"];
    Serial.println("Received: " + message);
    
    // Send response
    doc["response"] = "OK";
    char buffer[256];
    serializeJson(doc, buffer);
    webSocket.sendTXT(num, (uint8_t *)buffer, strlen(buffer));
  }
}
```

## Uploading Code

1. Write your sketch in Arduino IDE
2. **Sketch → Verify** (compile check)
3. **Sketch → Upload** (flash to device)
4. Monitor output: **Tools → Serial Monitor** (115200 baud)

## Common Issues

### "esp8266 by ESP8266 Community" not found
- Make sure you added the board URL in Preferences
- Restart Arduino IDE after adding URL

### Upload fails: "Permission denied"
- Wrong COM port selected
- Missing USB driver (CH340 or FTDI)
- Device disconnected

### "WebSocketsServer.h not found"
- Library not installed via Manage Libraries
- Restart Arduino IDE
- Check Tools → Manage Libraries shows it as installed

### "ArduinoJson.h not found"
- Same as above
- Verify spelling: "ArduinoJson" (capital A and J)

## Useful Resources

### Official Documentation
- ESP8266 Arduino Core: https://github.com/esp8266/Arduino
- Arduino IDE Docs: https://docs.arduino.cc/
- MicroPython vs Arduino: https://randomnerdtutorials.com/

### Community
- Arduino Forums: https://forum.arduino.cc/
- ESP8266 Community: https://community.blynk.cc/
- ESP8266 Tutorials: https://randomnerdtutorials.com/

### Alternative Tools
- **PlatformIO**: VS Code-based alternative to Arduino IDE
  - Website: https://platformio.org/
  - Better project management and library handling
- **Visual Studio Code**: Free editor with PlatformIO extension
  - Website: https://code.visualstudio.com/

## Next Steps

1. **Choose Implementation**:
   - Arduino IDE: C++ with WebSockets and ArduinoJson (production-grade)
   - MicroPython: Python with built-in json and optional websockets (rapid development)

2. **Set Up Environment**:
   - Install Arduino IDE + ESP8266 boards
   - Install WebSockets and ArduinoJson libraries

3. **Start Development**:
   - Create new sketch
   - Include libraries: `#include <WebSocketsServer.h>` and `#include <ArduinoJson.h>`
   - Implement your BBS client

4. **Deploy to Device**:
   - Verify code compiles
   - Upload to ESP8266
   - Monitor via Serial

## Arduino Implementation vs MicroPython

| Aspect | Arduino IDE | MicroPython |
|--------|------------|-------------|
| **Setup Time** | 30-45 min | 15-20 min |
| **Learning Curve** | Moderate (C++) | Easy (Python) |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Memory Usage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **WebSocket Support** | WebSockets library | micropython-websockets |
| **JSON Handling** | ArduinoJson | json (built-in) |
| **Development Speed** | Medium | Fast |
| **Debugging** | Serial output | REPL + tools |
| **Production Ready** | ✅ Yes | ✅ Yes |
| **Best For** | Performance, stability | Rapid dev, prototyping |

**Recommendation for BBS**: 
- **Start with MicroPython** - Easier to prototype and debug
- **Switch to Arduino** - If you need performance or have team C++ expertise

## Support

For issues with:
- **Arduino IDE**: https://github.com/arduino/arduino-ide/issues
- **ESP8266 Core**: https://github.com/esp8266/Arduino/issues
- **WebSockets Library**: https://github.com/Links2004/arduinoWebsockets/issues
- **ArduinoJson**: https://github.com/bblanchon/ArduinoJson/issues

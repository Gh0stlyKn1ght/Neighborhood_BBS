# Arduino IDE Setup for ESP8266 - Quick Reference

This guide covers setting up ESP8266 development using Arduino IDE with WebSocket and JSON libraries.

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
8. Install "esp8266 by ESP8266 Community" (latest)
9. Restart Arduino IDE

### 3. Install Required Libraries

**Sketch → Include Library → Manage Libraries**

#### Library 1: WebSockets
```
Search: WebSockets
Author: Markus Sattler
Version: 2.4+ (latest)
Status: Install
```
- **GitHub**: https://github.com/Links2004/arduinoWebsockets
- **Purpose**: Real-time WebSocket communication

#### Library 2: ArduinoJson
```
Search: ArduinoJson
Author: Benoit Blanchon
Version: 7.0+ (latest)
Status: Install
```
- **GitHub**: https://github.com/bblanchon/ArduinoJson
- **Purpose**: JSON serialization/deserialization

### 4. Select Board & Port

**Tools Menu:**
- **Board**: Select "NodeMCU 1.0 (ESP-12E Module)"
- **Port**: Select your device (COM3, COM4, etc.)
- **Upload Speed**: 115200
- **Flash Size**: 4M (FS:2M OTA:~1019KB)

## Testing Installation

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

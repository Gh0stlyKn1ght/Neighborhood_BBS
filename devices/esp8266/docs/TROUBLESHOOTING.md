# ESP8266 Troubleshooting & Diagnostics
**Neighborhood BBS | Complete Debugging Guide**

---

## Quick Diagnostic Report

Before opening an issue, run this diagnostic:

```python
# Save as: diagnostic.py
# Run: python -m ampy --port COM3 run diagnostic.py

import machine
import network
import gc

print("=" * 50)
print("ESP8266 DIAGNOSTIC REPORT")
print("=" * 50)

# 1. HARDWARE INFO
print("\n[HARDWARE]")
print(f"ESP Version: {machine.freq()}")
print(f"Chip ID: {machine.unique_id().hex()}")
print(f"Flash Size: {len(machine.flash_read(0, 1))}")

# 2. MEMORY
print("\n[MEMORY]")
free_mem = gc.mem_free()
alloc_mem = gc.mem_alloc()
total_mem = free_mem + alloc_mem
print(f"Free: {free_mem} bytes ({100*free_mem//total_mem}%)")
print(f"Allocated: {alloc_mem} bytes")
print(f"Total: {total_mem} bytes")

# 3. WIFI
print("\n[WIFI]")
sta = network.WLAN(network.STA_IF)
print(f"Station Active: {sta.active()}")
print(f"Connected: {sta.isconnected()}")
if sta.isconnected():
    print(f"IP: {sta.ifconfig()[0]}")
    print(f"Gateway: {sta.ifconfig()[2]}")
    print(f"DNS: {sta.ifconfig()[3]}")
    print(f"Signal: {sta.status('rssi')} dBm")

# 4. FILESYSTEM
print("\n[STORAGE]")
import os
files = os.listdir('/')
print(f"Files: {', '.join(files)}")

# 5. CONFIG CHECK
print("\n[CONFIG]")
try:
    import ujson
    with open('config.json') as f:
        cfg = ujson.load(f)
    print(f"SSID: {cfg.get('ssid', 'MISSING')}")
    print(f"Server: {cfg.get('server_host', 'MISSING')}:{cfg.get('server_port', 'MISSING')}")
    print(f"Device Name: {cfg.get('device_name', 'MISSING')}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 50)
```

---

## Common Issues & Solutions

### 1. "Connection refused" Error

**Symptom:**
```
Connecting to server...
Error: Connection refused
```

**Causes & Fixes:**

1. **Server is not running**
   ```bash
   # Check if server is up
   curl -I http://192.168.1.100:8080/health
   # Should return: "200 OK"
   ```

2. **Wrong IP address in config.json**
   ```json
   "server_host": "192.168.1.100"  // ← Verify this
   ```
   To find server IP:
   - On Windows: `ipconfig` → look for IPv4 Address
   - On Linux/Mac: `ifconfig` or `ip addr`

3. **Firewall blocking connections**
   - Windows Firewall: Allow Python through firewall
   - Linux: `sudo ufw allow 8080/tcp`
   - Check router firewall settings

4. **Different WiFi networks**
   ```
   ESP8266 WiFi: Home-2GHz
   Server WiFi: Home-5GHz  ← WRONG! Different networks
   ```
   **Solution:** Connect both to same network

**Diagnostic:**
```python
import socket
result = socket.getaddrinfo("192.168.1.100", 8080)
print(result)  # Should return address list
```

---

### 2. WiFi Connection Problems

**Symptom:**
```
Connecting to WiFi...
(long pause)
Failed to connect
```

**Diagnosis Steps:**

1. **Verify WiFi credentials**
   ```python
   # Check what networks are available
   import network
   sta = network.WLAN(network.STA_IF)
   sta.active(True)
   networks = sta.scan()
   for net in networks:
       print(net)  # (b'MyWiFi', <bssid>, <channel>, <rssi>, <security>, <not_hidden>)
   ```

2. **Try manual connection**
   ```python
   sta = network.WLAN(network.STA_IF)
   sta.active(True)
   sta.connect("MyWiFi", "MyPassword")
   
   import time
   for i in range(20):
       if sta.isconnected():
           print(f"Connected in {i} seconds!")
           break
       time.sleep(1)
       print(".", end="")
   ```

3. **Check signal strength**
   ```python
   sta = network.WLAN(network.STA_IF)
   signal = sta.status('rssi')
   print(f"Signal: {signal} dBm")
   
   # Interpretation:
   # 0 to -50 dBm:   Excellent
   # -50 to -70 dBm: Good  ← Target
   # -70 to -80 dBm: Fair (unreliable)
   # Below -80 dBm:  Poor (will disconnect)
   ```

**Solutions:**

| Problem | Solution |
|---------|----------|
| **Hidden SSID** | Unhide network in router settings |
| **5GHz network** | ESP8266 only supports 2.4GHz |
| **Special chars in password** | Use ASCII only (no émojis, ümlaut, etc.) |
| **Wrong password** | Reset router or check WiFi settings |
| **Too far from router** | Move ESP8266 closer or add WiFi extender |
| **Interference** | Microwave/cordless phone nearby? Move router |

---

### 3. Message Sending Fails

**Symptom:**
```
Sending message...
Error: 400 Bad Request
```

**Causes:**

1. **Room ID doesn't exist**
   ```python
   # Check valid rooms
   rooms = client.get_rooms()
   print(rooms)
   # Example: [{'id': 1, 'name': 'General'}, ...]
   
   # Use valid ID
   client.send_message(room_id=1, message="Hello")  # ✓
   client.send_message(room_id=999, message="Hello")  # ✗
   ```

2. **Message too long**
   ```python
   # MicroPython limit: 1000 chars
   # Arduino limit: 240 chars
   
   msg = "x" * 250  # Too long for Arduino
   client.send_message(1, msg)  # FAIL
   
   msg = "Hello!"  # Good
   client.send_message(1, msg)  # OK
   ```

3. **Rate limiting (429 error)**
   ```
   Error: 429 Too Many Requests
   ```
   **Solution:** Wait before sending more messages
   ```python
   import time
   time.sleep(5)  # Wait 5 seconds
   client.send_message(1, "Next message")
   ```

4. **Server not accepting messages**
   - Check server is running: `curl http://server:8080/health`
   - Check server logs for errors
   - Server might be in read-only mode

**Debug:**
```python
# Try simpler messages
client.send_message(1, "A")              # Single char
client.send_message(1, "Hello world")    # Simple text
client.send_message(1, '{"test": 1}')    # JSON (rare)
```

---

### 4. Server Not Responding / Timeouts

**Symptom:**
```
Connecting to server...
(timeout, then fails)
```

**Causes:**

1. **Timeout too short for slow connection**
   ```json
   "timeout": 10  // ← Change to 20 or 30
   ```

2. **Server under heavy load**
   - Check server CPU: `top` or Task Manager
   - Check available RAM: `free -h`
   - Restart server if needed

3. **Network latency**
   ```bash
   # From ESP8266 location, test latency
   # (Windows): ping 192.168.1.100
   # (Linux): ping -c 4 192.168.1.100
   ```
   - If > 50ms, network is slow
   - If > 100ms and unstable, WiFi interference

4. **Reconnection storm**
   ```json
   "reconnect_interval": 5  // ← Too frequent!
   // Change to: 60 or higher
   ```

**Fix Priority:**
1. Try increasing timeout to 30s: `"timeout": 30`
2. Reduce reconnect frequency: `"reconnect_interval": 300`
3. Check server is responding: `curl http://server:8080/health`
4. Check network: move ESP8266 closer to router

---

### 5. Out of Memory Error

**Symptom:**
```
MemoryError
Traceback (most recent call last):
  File "main.py", line 42, in <module>
MemoryError
```

**Causes:**

1. **Too many messages buffered**
   ```python
   # Arduino problem: MAX_MESSAGES = 20
   // Change in .ino:
   #define MAX_MESSAGES 10  // Reduce from 20
   ```

2. **Memory leak in connection**
   ```python
   # MicroPython: WiFi object not released
   import gc
   gc.collect()  # Force garbage collection
   ```

3. **Large HTTP response**
   - Server sending 100+ messages at once
   - Solution: Reduce limit in request
   ```python
   messages = client.get_messages(room_id=1, limit=5)  # Not 100!
   ```

**Memory Monitoring:**
```python
import gc

print(f"Free: {gc.mem_free()} bytes")  # Should be > 10,000
gc.collect()
print(f"After GC: {gc.mem_free()} bytes")

# If always < 5,000 bytes:
# - Reduce polling frequency
# - Reduce message history size
# - Use Arduino IDE (more efficient)
```

---

### 6. REPL or Upload Not Working

**Symptom:**
```
$ ampy --port COM3 ls /
Traceback (most recent call last):
  File "ampy", line 8, in <module>
OSError: could not open port COM3
```

**Causes:**

1. **Device not accessible**
   ```bash
   # Check if port exists
   # Windows: Check Device Manager
   # Linux/Mac: ls /dev/tty.*
   
   # Try different port (COM4, COM5, etc.)
   ampy --port COM4 ls /
   ```

2. **Another program using port**
   - Serial monitor still open? Close it.
   - Arduino IDE open? Close it.
   - PuTTY connected? Disconnect.

3. **Wrong baud rate**
   ```bash
   # Try different rates
   ampy --port COM3 --baud 115200 ls /
   ampy --port COM3 --baud 57600 ls /
   ```

4. **USB driver missing (Windows)**
   - If device shows as "USB-SERIAL CH340", install driver:
     - Download: https://www.wch.cn/downloads/ch341ser_exe.html
     - Run installer, restart computer

**Fix:**
```bash
# Full reset
python -m esptool --chip esp8266 --port COM3 erase_flash
python -m esptool --chip esp8266 --port COM3 write_flash 0x0 micropython.bin
```

---

### 7. Arduino IDE Upload Fails

**Symptom:**
```
error: espcomm_send_command: sending command header failed
```

**Causes & Fixes:**

1. **Device not in upload mode**
   - Hold GPIO0 button
   - While holding, click Reset button
   - Wait 2 seconds, release GPIO0
   - LED should be blinking

2. **Wrong board selected**
   - **Tools → Board**: Select "NodeMCU 1.0 (ESP-12E Module)"
   - Not "ESP32" or generic "ESP8266"

3. **Baud rate mismatch**
   - **Tools → Upload Speed**: 115200
   - Not 230400 or 9600

4. **Bad USB cable**
   - Try different cable (must be data cable, not charge-only)

5. **Port selection wrong**
   - **Tools → Port**: COM3 (or your device port)
   - If grayed out, restart IDE with device connected

**Diagnostic:**
```bash
# Manual upload test
python -m esptool --chip esp8266 --port COM3 --baud 115200 \
  write_flash -z 0x0 firmware.bin
```

---

### 8. Messages Show Wrong/Corrupted Content

**Symptom:**
```
[User] x#@Ñ€ÿ corrupted message
```

**Causes:**

1. **Encoding mismatch**
   - JSON encoding issue
   - Solution: Ensure UTF-8 encoding
   ```python
   message = "Hello".encode('utf-8').decode('utf-8')
   ```

2. **Message buffer overflow**
   - Message longer than buffer
   - Bytes get truncated/corrupted
   - Solution: Reduce message size

3. **Profanity filter error (Arduino)**
   - Message contains filter trigger
   - Solution: Check profanity list in .ino

---

### 9. Device Keeps Rebooting

**Symptom:**
```
ets Jan  8 2013,rst cause:4, boot mode:(1,6)
wdt reset
...
ets Jan  8 2013,rst cause:4, boot mode:(1,6)  ← Repeating
```

**Causes:**

1. **Insufficient power**
   - Needs 500mA sustained
   - Solution: Use powered USB hub, not computer port
   ```
   USB Hub (with power supply)
        ↓
   ESP8266 ← More stable
   ```

2. **Bad firmware**
   - Solution: Erase and re-flash
   ```bash
   esptool.py --port COM3 erase_flash
   esptool.py --port COM3 write_flash 0x0 micropython.bin
   ```

3. **Corrupt main.py**
   - Solution: Delete and re-upload
   ```bash
   ampy --port COM3 rm /main.py
   ampy --port COM3 put main.py /main.py
   ```

4. **Watchdog timeout**
   - Code running too long without yield
   - Solution: Add delays
   ```python
   import time
   time.sleep_ms(10)  # Let watchdog trigger reset
   ```

---

## Advanced Debugging

### Enable Verbose Logging (MicroPython)

```python
# Add to main.py before starting
import logging
logging.basicConfig(level=logging.DEBUG)

import main_orig as orig
orig.run()
```

### Check HTTP Responses in Detail

```python
import urequests

r = urequests.get("http://192.168.1.100:8080/health")
print(f"Status: {r.status_code}")
print(f"Headers: {r.headers}")
print(f"Body: {r.text}")

if r.status_code != 200:
    print(f"ERROR: {r.status_code}")
    print(r.text)  # Error details
```

### Monitor Network Traffic (Arduino)

```cpp
// Add to neighborhood_bbs_chat.ino
void debugWebSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    Serial.printf("[%u] ", num);
    if(type == WStype_TEXT) {
        Serial.printf("got Text: %s\n", payload);
    }
}
```

### Memory Leak Detection (MicroPython)

```python
import gc

# Before operation
gc.collect()
before = gc.mem_free()

# Run operation
client.get_messages(1, 50)

# After operation
gc.collect()
after = gc.mem_free()

leaked = before - after
print(f"Memory change: {leaked} bytes")
if leaked < 0:
    print("WARNING: Memory leak detected!")
```

---

## Performance Tuning

### Reduce Power Consumption

```json
{
  "reconnect_interval": 600,     // Poll every 10 min instead of 5
  "timeout": 10,
  "request_timeout": 5           // Skip slower requests
}
```

### Faster Response Times

```json
{
  "reconnect_interval": 30,      // Poll every 30 seconds
  "timeout": 30,                 // More patience for WiFi
  "cache_size": 5                // Fewer messages in memory
}
```

### WiFi Reliability

```json
{
  "reconnect_interval": 300,     // More stable pattern
  "timeout": 20,                 // Reasonable timeout
  "retry_attempts": 3            // More retries
}
```

---

## Testing Checklist

Before deploying to production:

- ✅ Device connects to WiFi without errors
- ✅ Can reach server (`/health` endpoint)
- ✅ Can send message and see it appear
- ✅ Can receive messages from other clients
- ✅ Survives WiFi disconnection (reconnects)
- ✅ Memory stays stable (no leak) after 1 hour
- ✅ No reboots in 24 hours
- ✅ Power consumption reasonable (< 200mA avg)
- ✅ Can handle 10 concurrent messages
- ✅ Message order preserved

---

## Getting Help

If you're still stuck after trying above:

1. **Collect diagnostics:**
   ```bash
   # Run diagnostic.py (see above)
   # Save output to: esp8266_diagnostic.txt
   ```

2. **Gather logs:**
   ```bash
   # Serial monitor output (Tools → Serial Monitor)
   # Save to: esp8266_logs.txt
   ```

3. **Open GitHub issue** with:
   - Diagnostic output
   - Serial logs
   - config.json (without password!)
   - Steps to reproduce

---

**Last Updated:** March 2026

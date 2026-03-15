# ESP8266 Firmware for Neighborhood BBS

Run Neighborhood BBS on ESP8266 devices with the retro cyan CRT terminal theme - a portable WiFi-enabled BBS node.

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

1. **esptool.py** - For flashing firmware

   ```bash
   pip install esptool
   ```

2. **MicroPython** - Get the latest firmware from [micropython.org](https://micropython.org/)

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

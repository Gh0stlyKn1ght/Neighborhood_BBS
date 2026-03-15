# ESP8266 Firmware for Neighborhood BBS

This directory contains MicroPython firmware for running Neighborhood BBS on ESP8266 devices.

## Hardware Requirements

- ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
- USB Cable for flashing
- WiFi connectivity

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
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put -d lib
```

### Using WebREPL

1. Connect to the device REPL
2. Run: `webrepl_setup.py`
3. Upload files via the web interface

## Configuration

Edit `config.py` to set:

```python
SSID = "Your_WiFi_SSID"
PASSWORD = "Your_WiFi_Password"
SERVER_HOST = "192.168.1.100"  # Main server IP
SERVER_PORT = 8080
DEVICE_NAME = "ESP8266_Neighborhood_1"
```

## Running the Application

Via REPL:

```python
import main
main.start()
```

## Troubleshooting

### Device Not Detected

```bash
# Check USB connection
ls /dev/ttyUSB*  # Linux/Mac
Get-Content com:  # Windows

# Install USB drivers if needed
```

### WiFi Connection Issues

- Verify SSID and password in config.py
- Check WiFi signal strength
- Ensure main server is accessible

### Memory Issues

ESP8266 has limited memory (4MB). Optimize by:
- Using the `--flash_mode dio` option
- Removing unused imports
- Using MicroPython's built-in libraries

## Development

### Main Files

- `main.py` - Application entry point
- `config.py` - Configuration
- `network.py` - WiFi connectivity
- `client.py` - MQTT/HTTP client
- `sensor.py` - Optional sensor integration

### Testing

Connect via REPL and test commands:

```python
from main import *
device.connect_to_server()
device.send_message("general", "Hello from ESP8266!")
```

## Resources

- MicroPython Docs: https://docs.micropython.org/
- ESP8266 Community: https://github.com/orgs/micropython
- esptool Docs: https://github.com/espressif/esptool

## Next Steps

- [Setup Guide](../../docs/SETUP.md)
- [API Documentation](../../docs/API.md)
- [Development Guide](../../docs/DEVELOPMENT.md)

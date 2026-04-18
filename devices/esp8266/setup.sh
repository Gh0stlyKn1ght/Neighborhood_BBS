#!/bin/bash
# Neighborhood BBS - ESP8266 Flash & Deploy Script
# Flashes MicroPython firmware and uploads BBS client to an ESP8266
#
# Usage:
#   ./setup.sh                  # auto-detect serial port
#   ./setup.sh /dev/ttyUSB1     # specify port explicitly
#
# Requirements:
#   pip install -r requirements.txt

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MICROPYTHON_URL="https://micropython.org/resources/firmware/esp8266-20230426-v1.20.0.bin"
FIRMWARE_FILE="micropython.bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Neighborhood BBS - ESP8266 Flasher    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Detect or accept serial port
if [ -n "$1" ]; then
    PORT="$1"
else
    PORT=$(ls /dev/ttyUSB* /dev/ttyACM* /dev/cu.usbserial* /dev/cu.SLAB* 2>/dev/null | head -1)
    if [ -z "$PORT" ]; then
        echo -e "${RED}ERROR: No serial device found.${NC}"
        echo "Connect your ESP8266 via USB, then re-run:"
        echo "  ./setup.sh /dev/ttyUSB0"
        exit 1
    fi
fi

echo -e "${YELLOW}Using port: ${PORT}${NC}"

# Check host tools are installed
echo -e "${YELLOW}[1/5]${NC} Checking host tools..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}ERROR: python3 is required.${NC}"
    exit 1
fi

if ! command -v curl &>/dev/null; then
    echo -e "${RED}ERROR: curl is required.${NC}"
    exit 1
fi

if ! command -v esptool.py &>/dev/null || ! command -v mpremote &>/dev/null; then
    echo -e "${YELLOW}Installing host tools...${NC}"
    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Download MicroPython firmware if not present
echo -e "${YELLOW}[2/5]${NC} Fetching MicroPython firmware..."
if [ ! -f "$SCRIPT_DIR/$FIRMWARE_FILE" ]; then
    curl -L "$MICROPYTHON_URL" -o "$SCRIPT_DIR/$FIRMWARE_FILE"
else
    echo "  Firmware already downloaded, skipping."
fi

# Erase flash
echo -e "${YELLOW}[3/5]${NC} Erasing ESP8266 flash..."
esptool.py --port "$PORT" erase_flash

# Flash MicroPython
echo -e "${YELLOW}[4/5]${NC} Flashing MicroPython..."
esptool.py --port "$PORT" --baud 460800 write_flash \
    --flash_size=detect \
    --flash_mode=dio \
    0x0 "$SCRIPT_DIR/$FIRMWARE_FILE"

# Upload BBS client files
echo -e "${YELLOW}[5/5]${NC} Uploading BBS client files..."

# Check config exists
if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
    echo -e "${YELLOW}No config.json found — copying example config...${NC}"
    cp "$SCRIPT_DIR/config/config.json.example" "$SCRIPT_DIR/config/config.json"
    echo ""
    echo -e "${RED}ACTION REQUIRED: Edit config/config.json with your WiFi and BBS server details${NC}"
    echo -e "  ${YELLOW}nano $SCRIPT_DIR/config/config.json${NC}"
    echo ""
    read -p "Press Enter after editing config.json to continue, or Ctrl+C to cancel... "
fi

# Use mpremote to upload files
mpremote connect "$PORT" cp "$SCRIPT_DIR/src/main.py" :main.py
mpremote connect "$PORT" cp "$SCRIPT_DIR/config/config.json" :config.json

echo ""
echo -e "${GREEN}✅ ESP8266 setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Open the REPL to watch startup:"
echo -e "   ${YELLOW}mpremote connect $PORT repl${NC}"
echo ""
echo "2. The device will connect to your WiFi and begin posting messages."
echo "   Output is visible over serial at 115200 baud."
echo ""
echo "3. To update config later:"
echo -e "   ${YELLOW}mpremote connect $PORT cp config/config.json :config.json${NC}"

#!/bin/bash
# Neighborhood BBS - Meshtastic Bridge Setup
# Installs dependencies and registers the bridge as a systemd service
#
# Usage:
#   ./setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BBS_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_PIP="$BBS_ROOT/venv/bin/pip"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Neighborhood BBS - Meshtastic Bridge  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Check Python version
echo -e "${YELLOW}[1/4]${NC} Checking Python version..."
python3 -c "import sys; assert sys.version_info >= (3, 9), 'Python 3.9+ required'" || {
    echo -e "${RED}Python 3.9 or higher is required.${NC}"
    exit 1
}

# Install Python dependencies
echo -e "${YELLOW}[2/4]${NC} Installing Python dependencies..."
if [ -x "$VENV_PIP" ]; then
    "$VENV_PIP" install -r "$SCRIPT_DIR/requirements.txt"
else
    echo -e "${YELLOW}No repository venv found at $BBS_ROOT/venv. Falling back to pip3.${NC}"
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

# Grant serial port access
echo -e "${YELLOW}[3/4]${NC} Granting serial port access..."
if ! groups "$USER" | grep -q dialout; then
    sudo usermod -aG dialout "$USER"
    echo -e "${YELLOW}Added $USER to dialout group. You must log out and back in for this to take effect.${NC}"
fi

# Create config if not present
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo -e "${YELLOW}No config.json found — copying example...${NC}"
    cp "$SCRIPT_DIR/config.json.example" "$SCRIPT_DIR/config.json"
    echo ""
    echo -e "${RED}ACTION REQUIRED: Edit config.json with your BBS server details${NC}"
    echo -e "  ${YELLOW}nano $SCRIPT_DIR/config.json${NC}"
    echo ""
fi

# Install systemd service (optional)
echo -e "${YELLOW}[4/4]${NC} Installing systemd service..."
SERVICE_SRC="$SCRIPT_DIR/systemd/meshtastic-bridge.service"
SERVICE_DEST="/etc/systemd/system/meshtastic-bridge.service"

# Patch paths in service file to match actual install location
sed "s|/home/pi/Neighborhood_BBS|$BBS_ROOT|g; s|User=pi|User=$USER|g" \
    "$SERVICE_SRC" | sudo tee "$SERVICE_DEST" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable meshtastic-bridge

echo ""
echo -e "${GREEN}✅ Meshtastic bridge setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Plug in your Meshtastic node (T-Beam, Heltec, etc.) via USB."
echo ""
echo "2. Verify it's visible:"
echo -e "   ${YELLOW}meshtastic --info${NC}"
echo ""
echo "3. Start the bridge:"
echo -e "   ${YELLOW}sudo systemctl start meshtastic-bridge${NC}"
echo ""
echo "4. Watch logs:"
echo -e "   ${YELLOW}sudo journalctl -u meshtastic-bridge -f${NC}"

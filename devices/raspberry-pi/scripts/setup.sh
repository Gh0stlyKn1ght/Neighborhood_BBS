#!/bin/bash
# Neighborhood BBS - Raspberry Pi Setup Script
# Automated installation and configuration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Neighborhood BBS - Raspberry Pi Setup ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# 1. Check if running on Raspberry Pi
echo -e "${YELLOW}[1/8]${NC} Checking system..."
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. Update system
echo -e "${YELLOW}[2/8]${NC} Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y

# 3. Install dependencies
echo -e "${YELLOW}[3/8]${NC} Installing dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    sqlite3 \
    build-essential \
    libssl-dev \
    libffi-dev \
    nginx

# 4. Clone repository
echo -e "${YELLOW}[4/8]${NC} Cloning Neighborhood BBS..."
if [ -f "$REPO_ROOT/server/src/main.py" ] && [ -f "$REPO_ROOT/requirements.txt" ]; then
    echo -e "${GREEN}Using existing repository at: $REPO_ROOT${NC}"
else
    TARGET_DIR="$HOME/Neighborhood_BBS"
    if [ -d "$TARGET_DIR" ]; then
        echo -e "${YELLOW}Directory already exists, using: $TARGET_DIR${NC}"
    else
        git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git "$TARGET_DIR"
    fi
    REPO_ROOT="$TARGET_DIR"
fi

cd "$REPO_ROOT"

# 5. Create virtual environment
echo -e "${YELLOW}[5/8]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 6. Install Python dependencies
echo -e "${YELLOW}[6/8]${NC} Installing Python packages..."
pip install --upgrade pip setuptools wheel
if [ -f "$REPO_ROOT/devices/raspberry-pi/requirements.txt" ]; then
    pip install -r "$REPO_ROOT/devices/raspberry-pi/requirements.txt"
else
    pip install -r "$REPO_ROOT/requirements.txt"
fi

# 7. Initialize database
echo -e "${YELLOW}[7/8]${NC} Initializing database..."
python "$REPO_ROOT/server/scripts/init_db.py"

# Ensure env file exists for systemd EnvironmentFile
if [ -f "$REPO_ROOT/devices/raspberry-pi/config/config.env.example" ] && [ ! -f "$REPO_ROOT/devices/raspberry-pi/config/.env" ]; then
    cp "$REPO_ROOT/devices/raspberry-pi/config/config.env.example" "$REPO_ROOT/devices/raspberry-pi/config/.env"
    echo -e "${YELLOW}Created devices/raspberry-pi/config/.env from example. Review before production use.${NC}"
fi

# 8. Create systemd service
echo -e "${YELLOW}[8/8]${NC} Installing systemd service..."
SERVICE_TEMPLATE="$REPO_ROOT/devices/raspberry-pi/systemd/neighborhood-bbs.service"
SERVICE_DEST="/etc/systemd/system/neighborhood-bbs.service"
PRIMARY_GROUP="$(id -gn "$USER")"

if [ -f "$SERVICE_TEMPLATE" ]; then
    sed "s|/home/pi/Neighborhood_BBS|$REPO_ROOT|g; s|User=pi|User=$USER|g; s|Group=pi|Group=$PRIMARY_GROUP|g" \
        "$SERVICE_TEMPLATE" | sudo tee "$SERVICE_DEST" > /dev/null
else
    sudo tee "$SERVICE_DEST" > /dev/null << EOF
[Unit]
Description=Neighborhood BBS
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$PRIMARY_GROUP
WorkingDirectory=$REPO_ROOT
EnvironmentFile=-$REPO_ROOT/devices/raspberry-pi/config/.env
Environment="PATH=$REPO_ROOT/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$REPO_ROOT/venv/bin/python server/src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=neighborhood-bbs

[Install]
WantedBy=multi-user.target
EOF
fi

sudo systemctl daemon-reload
sudo systemctl enable neighborhood-bbs

echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Start the service:"
echo -e "   ${YELLOW}sudo systemctl start neighborhood-bbs${NC}"
echo ""
echo "2. Check status:"
echo -e "   ${YELLOW}sudo systemctl status neighborhood-bbs${NC}"
echo ""
echo "3. View logs:"
echo -e "   ${YELLOW}sudo journalctl -u neighborhood-bbs -f${NC}"
echo ""
echo "4. Access the application:"
echo -e "   ${YELLOW}http://raspberrypi.local:8080${NC}"
echo ""
echo -e "${BLUE}Optional: Configure Nginx reverse proxy${NC}"
echo "See devices/raspberry-pi/docs/README.md for details"
echo ""
echo -e "${GREEN}Happy serving! 🏘️${NC}"

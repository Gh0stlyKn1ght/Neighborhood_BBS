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
if [ -d "Neighborhood_BBS" ]; then
    echo -e "${YELLOW}Directory already exists, skipping clone${NC}"
else
    git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
fi

cd Neighborhood_BBS

# 5. Create virtual environment
echo -e "${YELLOW}[5/8]${NC} Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 6. Install Python dependencies
echo -e "${YELLOW}[6/8]${NC} Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 7. Initialize database
echo -e "${YELLOW}[7/8]${NC} Initializing database..."
python server/scripts/init_db.py

# 8. Create systemd service
echo -e "${YELLOW}[8/8]${NC} Installing systemd service..."
sudo tee /etc/systemd/system/neighborhood-bbs.service > /dev/null << EOF
[Unit]
Description=Neighborhood BBS
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Neighborhood_BBS
Environment="PATH=$HOME/Neighborhood_BBS/venv/bin"
ExecStart=$HOME/Neighborhood_BBS/venv/bin/python server/src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

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
echo "See firmware/raspberry-pi/README.md for details"
echo ""
echo -e "${GREEN}Happy serving! 🏘️${NC}"

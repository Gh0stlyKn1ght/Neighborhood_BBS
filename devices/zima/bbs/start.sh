#!/bin/bash
# Neighborhood BBS - ZimaBoard deployment script

set -e

echo "◆ Neighborhood BBS Setup"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "!! This script must run as root (use: sudo bash start.sh)"
    exit 1
fi

# Install dependencies
echo "▸ Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip nginx > /dev/null 2>&1

# Install Python packages
echo "▸ Installing Python packages..."
pip3 install -r requirements.txt --break-system-packages > /dev/null 2>&1

# Create database
echo "▸ Initializing database..."
python3 app.py &
PID=$!
sleep 2
kill $PID 2>/dev/null || true

# Setup systemd service
echo "▸ Setting up systemd service..."
cp bbs.service /etc/systemd/system/bbs.service
systemctl daemon-reload
systemctl enable bbs --quiet
systemctl restart bbs

# Setup nginx
echo "▸ Configuring nginx..."
cp nginx.conf /etc/nginx/sites-available/bbs
ln -sf /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t > /dev/null 2>&1
systemctl restart nginx

# Display status
echo ""
echo "✓ BBS Online!"
echo ""
echo "Access:"
echo "  http://192.168.4.1 (local from AP)"
echo "  http://<zimaboard-ip> (from network)"
echo ""
echo "Admin:"
echo "  http://192.168.4.1/admin/login"
echo "  Default: sysop / gh0stly"
echo "  CHANGE THIS PASSWORD IMMEDIATELY"
echo ""
echo "Service control:"
echo "  systemctl status bbs"
echo "  systemctl restart bbs"
echo "  journalctl -u bbs -f (live logs)"
echo ""

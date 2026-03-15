# Raspberry Pi - Neighborhood BBS Deployment

Deploy Neighborhood BBS on Raspberry Pi (3B+, 4, and 5) with the retro cyan CRT terminal theme.

## Features

- **Retro Cyan CRT Terminal Theme** - Classic monospace interface with scanline effects
- **IRC-Style Chat** - Real-time community chat with channels and user lists  
- **Community Board** - Post and view messages from your neighborhood
- **Hardware-Only Logging** - Privacy-first, no user tracking
- **Local Network** - Access from any device on your WiFi network
- **Easy Deployment** - One-command setup via systemd service

## Hardware Requirements

- **Raspberry Pi** 3B+, 4, or 5
- **SD Card** 32GB minimum (class 10 recommended)
- **Power Supply** 5V/3A (2.5A minimum)
- **Network** Ethernet or WiFi
- **Optional**: Heatsink for Pi 4/5

## Operating System

### Supported OS
- **Raspberry Pi OS Lite** (64-bit recommended)
- **Raspberry Pi OS Desktop** (with GUI)
- Ubuntu 22.04 (ARM64)

### Installation

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select device: **Raspberry Pi 4** (or your model)
3. Select OS: **Raspberry Pi OS Lite (64-bit)**
4. Write to SD card
5. Insert SD card into Pi and power on

## Network Setup

### Enable SSH

```bash
# Connect keyboard/monitor or use SSH from another device
sudo raspi-config

# Navigate to: Interfacing Options > SSH > Enable
```

### Connect via SSH

```bash
# From your computer
ssh pi@raspberrypi.local
# Default password: raspberry
```

## Installation Steps

### 1. System Update

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
```

### 2. Install Dependencies

```bash
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
```

### 3. Clone Repository

```bash
cd ~
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS
```

### 4. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

# Note for Pi 4/5: This may take a few minutes
```

### 5. Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 6. Initialize Database

```bash
python scripts/init_db.py
```

### 7. Run the Server

```bash
python src/main.py
```

Browse to `http://raspberrypi.local:8080` from any device on your network

**You'll see:**
- 🖥️ Cyan CRT terminal interface with ASCII art header
- 💬 Real-time IRC-style chat room
- 📋 Community announcement board
- 🏘️ Local neighborhood communication

## Running as a Service

### Option A: Systemd Service (Recommended)

Create service file:

```bash
sudo tee /etc/systemd/system/neighborhood-bbs.service > /dev/null << 'EOF'
[Unit]
Description=Neighborhood BBS
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Neighborhood_BBS
Environment="PATH=/home/pi/Neighborhood_BBS/venv/bin"
ExecStart=/home/pi/Neighborhood_BBS/venv/bin/python src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable neighborhood-bbs
sudo systemctl start neighborhood-bbs
sudo systemctl status neighborhood-bbs
```

View logs:

```bash
sudo journalctl -u neighborhood-bbs -f
```

### Option B: Cron Job (Alternative)

```bash
# Edit crontab
crontab -e

# Add this line:
@reboot cd ~/Neighborhood_BBS && source venv/bin/activate && python src/main.py >> ~/logs/nbbs.log 2>&1
```

## Nginx Reverse Proxy (Optional)

Set up Nginx for better performance:

```bash
sudo tee /etc/nginx/sites-available/neighborhood-bbs > /dev/null << 'EOF'
upstream nbbs {
    server 127.0.0.1:8080;
}

server {
    listen 80 default_server;
    server_name _;
    
    location / {
        proxy_pass http://nbbs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/neighborhood-bbs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Access at: `http://raspberrypi.local` (port 80, no port number needed!)

## HTTPS Setup (Let's Encrypt)

### Install Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### Get Certificate

```bash
sudo certbot certonly --standalone -d yourdomain.com
```

### Configure Nginx

```bash
sudo certbot --nginx -d yourdomain.com
```

## Optimization for Raspberry Pi

### Reduce Memory Usage

Edit `.env`:

```env
DEBUG=false
WORKERS=2
```

### Enable Swap

```bash
sudo dphys-swapfile swapoff
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile swapon
```

### Monitor Resources

```bash
# View system stats
top

# View disk usage
df -h

# View temperature (Pi 4/5)
vcgencmd measure_temp
```

## Backup & Recovery

### Automated Backup Script

Create `~/backup-nbbs.sh`:

```bash
#!/bin/bash
BACKUP_DIR="$HOME/backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
sqlite3 ~/Neighborhood_BBS/data/neighborhood.db ".backup $BACKUP_DIR/neighborhood-bbs-$TIMESTAMP.db"
echo "Backup created: $BACKUP_DIR/neighborhood-bbs-$TIMESTAMP.db"
```

Make executable:

```bash
chmod +x ~/backup-nbbs.sh
```

Schedule daily backup:

```bash
crontab -e
# Add: 0 2 * * * ~/backup-nbbs.sh
```

### Restore from Backup

```bash
sqlite3 ~/Neighborhood_BBS/data/neighborhood.db ".restore /path/to/backup.db"
sudo systemctl restart neighborhood-bbs
```

## Performance Benchmarks

### Pi 4 (4GB)
- **Max Concurrent Users:** 50-100
- **Messages/Second:** 100+
- **CPU Usage:** 10-20%
- **Memory Usage:** 150-200MB

### Pi 5 (8GB)
- **Max Concurrent Users:** 100-200
- **Messages/Second:** 200+
- **CPU Usage:** 5-10%
- **Memory Usage:** 200-300MB

## Troubleshooting

### SSH Connection Refused
```bash
# On Pi: Enable SSH in raspi-config
sudo raspi-config
# Interfacing Options > SSH > Enable
```

### Port Already in Use
```bash
# Change port in .env
export PORT=8081
python src/main.py
```

### Database Locked
```bash
# Stop service, reset, restart
sudo systemctl stop neighborhood-bbs
python scripts/reset_db.py
sudo systemctl start neighborhood-bbs
```

### High CPU Usage
```bash
# Check running processes
top

# Restart service
sudo systemctl restart neighborhood-bbs
```

### Out of Disk Space
```bash
# Check available space
df -h

# Clean apt cache
sudo apt-get clean
sudo apt-get autoclean
```

## Useful Commands

```bash
# Restart service
sudo systemctl restart neighborhood-bbs

# Check service status
sudo systemctl status neighborhood-bbs

# View logs
sudo journalctl -u neighborhood-bbs -n 100

# Test API
curl http://localhost:8080/health

# Find Pi IP
hostname -I
```

## Resources

- [Raspberry Pi Official](https://www.raspberrypi.com/)
- [Raspberry Pi OS](https://www.raspberrypi.com/software/)
- [SSH Guide](https://www.raspberrypi.com/documentation/computers/remote-access.html)
- [Performance Tips](https://www.raspberrypi.com/documentation/computers/configuration/configuring.html)

## Next Steps

1. Configure domain (optional)
2. Set up HTTPS (Let's Encrypt)
3. Create backups
4. Invite neighbors to join!

---

Happy hosting on Raspberry Pi! 🏘️

For issues, visit: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues

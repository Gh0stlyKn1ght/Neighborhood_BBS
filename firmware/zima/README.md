# Zima Board - Neighborhood BBS Deployment

This directory contains instructions and utilities for deploying Neighborhood BBS on Zima Board.

## Hardware Requirements

- Zima Board with Zima OS or compatible Linux distribution
- Network connectivity (Ethernet or WiFi)
- 2GB+ storage for application and database

## System Requirements

- Linux OS (Zima OS, Ubuntu, Debian, etc.)
- Python 3.7+
- pip or apt package manager
- systemd (for service management)

## Installation

### 1. System Updates

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Dependencies

```bash
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sqlite3 \
    nginx  # Optional, for reverse proxy
```

### 3. Clone Repository

```bash
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS
```

### 4. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Initialize Application

```bash
# Create necessary directories
mkdir -p data logs

# Initialize database
python3 scripts/init_db.py
```

## Running as a Service

### 1. Create systemd Service File

```bash
sudo nano /etc/systemd/system/neighborhood-bbs.service
```

Add the following content:

```ini
[Unit]
Description=Neighborhood BBS
After=network.target

[Service]
Type=simple
User=pi  # Or your user
WorkingDirectory=/home/pi/Neighborhood_BBS
ExecStart=/home/pi/Neighborhood_BBS/venv/bin/python src/main.py
Restart=on-failure
RestartSec=10
EnvironmentFile=/home/pi/Neighborhood_BBS/.env

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable neighborhood-bbs
sudo systemctl start neighborhood-bbs
sudo systemctl status neighborhood-bbs
```

### 3. View Logs

```bash
sudo journalctl -u neighborhood-bbs -f
```

## Accessing the Application

### Local Network

```
http://<zima-board-ip>:8080
```

Find your IP:

```bash
hostname -I
```

### Behind Nginx Reverse Proxy (Optional)

```bash
sudo nano /etc/nginx/sites-available/neighborhood-bbs
```

Add:

```nginx
upstream neighborhood_bbs_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://neighborhood_bbs_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/neighborhood-bbs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Configuration

### Environment File

Create `.env`:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=false
HOST=0.0.0.0
PORT=8080
DATABASE_URL=sqlite:///data/neighborhood.db
```

### Application Config

Edit `config/config.conf`:

```ini
[SERVER]
host = 0.0.0.0
port = 8080
debug = false

[DATABASE]
type = sqlite
path = data/neighborhood.db
```

## Updating the Application

```bash
cd ~/Neighborhood_BBS
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart neighborhood-bbs
```

## Monitoring

### System Resources

```bash
top
df -h
free -m
```

### Service Status

```bash
sudo systemctl status neighborhood-bbs
journalctl -u neighborhood-bbs --since "1 hour ago"
```

### Database

```bash
sqlite3 data/neighborhood.db
.tables
SELECT COUNT(*) FROM messages;
```

## Backup

### Automated Backup

Create `~/backup-nbbs.sh`:

```bash
#!/bin/bash
BACKUP_DIR="$HOME/backups"
mkdir -p $BACKUP_DIR
sqlite3 ~/Neighborhood_BBS/data/neighborhood.db ".backup $BACKUP_DIR/neighborhood-bbs-$(date +%Y%m%d_%H%M%S).db"
```

Schedule with crontab:

```bash
crontab -e
# Add: 0 2 * * * ~/backup-nbbs.sh
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u neighborhood-bbs -n 50

# Check manually
cd ~/Neighborhood_BBS
source venv/bin/activate
python3 src/main.py
```

### Port Already in Use

```bash
# Find process on port 8080
sudo lsof -i :8080

# Kill if necessary
sudo kill -9 <PID>
```

### Database Issues

```bash
# Backup current database
cp data/neighborhood.db data/neighborhood.db.backup

# Reset database
python3 scripts/reset_db.py
```

## Security Considerations

1. Set strong `SECRET_KEY` in `.env`
2. Use HTTPS (Let's Encrypt with Nginx)
3. Restrict network access if needed
4. Keep system updated: `sudo apt-get update && sudo apt-get upgrade`
5. Run as non-root user (never as root!)

## Resources

- Zima Board: https://www.cardberry.cc/zima
- Zima OS: https://github.com/zima-board
- Flask Deployment: https://flask.palletsprojects.com/deployment/

## Performance Tips

- Enable caching for static files
- Use a production WSGI server (e.g., Gunicorn)
- Monitor log files for errors
- Regular backups are essential

---

For general setup help, see [Setup Guide](../../docs/SETUP.md)

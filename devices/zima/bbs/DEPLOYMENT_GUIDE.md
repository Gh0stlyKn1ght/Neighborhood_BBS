# ZimaBoard Neighborhood BBS - Complete Deployment Guide

**Choose Your Deployment Path:**

- **Path A: Native Debian** - Simple, lightweight, direct control
- **Path B: Docker / CasaOS** - Professional, discoverable, scalable

---

## 📊 Quick Comparison

| Aspect | Native Debian | Docker | CasaOS |
|--------|--|--|--|
| **Complexity** | Simple | Moderate | Beginner-friendly |
| **Resource usage** | ~50MB RAM | ~200MB RAM | Same as Docker |
| **Setup time** | 5 minutes | 10 minutes | 2 minutes (AppStore) |
| **Updates** | Manual | Docker pull | Auto-update in CasaOS |
| **Who's it for?** | Developers, power users | Teams, scaling | End-users |
| **Discoverability** | SSH only | Manual pull | CasaOS AppStore catalog |

---

# Path A: Native Debian Deployment

**Best for:** Quick local setup, development, direct control

## Prerequisites

- ZimaBoard or Debian Linux machine
- SSH access
- Python 3.7+
- Git

## Quick Install (Automated)

```bash
# SSH to ZimaBoard
ssh root@zimaboard.local

# Clone repository
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS/devices/zima/bbs

# Run automated setup
bash start.sh
```

**What start.sh does:**
- Installs Python3, pip, nginx
- Installs Flask + flask-sock dependencies
- Initializes SQLite database
- Creates systemd service
- Configures nginx proxying
- Starts the BBS

Done! Access at: `http://<zimaboard-ip>:8080`

## Manual Install (Step-by-Step)

```bash
# SSH to ZimaBoard
ssh root@zimaboard.local

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3 python3-pip nginx curl

# Clone repository
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS/devices/zima/bbs

# Install Python packages
pip3 install -r requirements.txt --break-system-packages

# Initialize database
python3 -c "from app import init_db; init_db()"

# Create systemd service
sudo cp bbs.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bbs
sudo systemctl start bbs

# Configure nginx (optional, but recommended)
sudo cp nginx.conf /etc/nginx/sites-available/bbs
sudo ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
sudo systemctl restart nginx
```

## Verify Installation

```bash
# Check service status
systemctl status bbs

# View logs
journalctl -u bbs -f

# Test endpoint
curl http://localhost:5000/health

# Expected output:
# {"status":"healthy","clients":0,"bulletins":3,"messages":0}
```

## Access the BBS

1. **Web Interface:** `http://<zimaboard-ip>:8080`
2. **Direct API:** `http://<zimaboard-ip>:5000`
3. **Admin Panel:** `http://<zimaboard-ip>:8080/admin`
   - Username: `sysop`
   - Password: `gh0stly` (CHANGE THIS!)

## Management Commands

```bash
# View logs in real-time
journalctl -u bbs -f

# Restart service
systemctl restart bbs

# Stop service
systemctl stop bbs

# Start service
systemctl start bbs

# Check service status
systemctl status bbs

# Update code
cd Neighborhood_BBS
git pull origin main
systemctl restart bbs
```

## Troubleshooting

### Service won't start

```bash
journalctl -u bbs -n 50  # See last 50 lines of log
```

Common issues:
- Port 5000 already in use: `sudo lsof -i :5000`
- Database permission error: `chmod 777 /opt/zima_bbs/`
- Missing dependencies: `pip3 install -r requirements.txt --break-system-packages`

### Can't connect to BBS

```bash
# Verify service is running
curl http://localhost:5000/health

# Check if nginx is running
ps aux | grep nginx

# Check firewall
sudo ufw status
sudo ufw allow 8080/tcp
```

### Database issues

```bash
# Reset database (WARNING: deletes all messages!)
rm bbs.db
python3 -c "from app import init_db; init_db()"

# Restart service
systemctl restart bbs
```

---

# Path B: Docker Deployment

**Best for:** Containerized environments, easier updates, multi-instance runs

## Prerequisites

- ZimaBoard with Docker installed
- Or: Debian with Docker + Docker Compose
- Git

## Quick Install with Docker Compose

```bash
# SSH to ZimaBoard
ssh root@zimaboard.local

# Clone repository
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS/devices/zima/bbs

# Start with Docker Compose
docker-compose up -d

# Verify
docker-compose logs -f neighborhood-bbs
```

Access at: `http://<zimaboard-ip>:5000`

## Building Your Own Image

```bash
# From the bbs directory
docker build -t neighborhood-bbs:latest .

# Run the image
docker run -d \
  --name neighborhood-bbs \
  -p 5000:5000 \
  -v bbs_data:/app/data \
  -e ADMIN_PASSWORD=your_password \
  neighborhood-bbs:latest

# Verify
docker logs neighborhood-bbs
```

## Docker Compose Production Setup

```bash
# Copy and edit docker-compose.yml
cp docker-compose.yml docker-compose.prod.yml

# Edit for production
nano docker-compose.prod.yml
```

Example production config:

```yaml
version: '3.8'

services:
  neighborhood-bbs:
    image: ghcr.io/gh0stlykn1ght/neighborhood-bbs:latest
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - bbs_data:/app/data
    environment:
      FLASK_ENV: production
      ADMIN_PASSWORD: your_secure_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  bbs_data:

networks:
  default:
    name: bbs-network
```

## Running on ZimaBoard

```bash
# Stop any existing instance
docker-compose down

# Use production config
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Check container status
docker ps

# See volumes
docker volume ls
```

## Management Commands

```bash
# View logs
docker-compose logs -f neighborhood-bbs

# Restart container
docker-compose restart neighborhood-bbs

# Stop container
docker-compose stop

# Start container
docker-compose start

# Remove everything (keeps volumes)
docker-compose down

# Remove everything including data (WARNING!)
docker-compose down -v
```

## Updating

```bash
# Pull latest image
docker pull ghcr.io/gh0stlykn1ght/neighborhood-bbs:latest

# Restart with new image
docker-compose up -d

# Or rebuild locally
docker build -t neighborhood-bbs:latest .
docker-compose up -d --force-recreate --build
```

---

# Path C: CasaOS Installation (Easiest)

**Best for:** Non-technical users, one-click installation

## Requirements

- ZimaBoard with CasaOS installed
- Internet connection to AppStore

## Install from CasaOS AppStore

1. Open CasaOS dashboard: `http://<zimaboard-ip>:80`
2. Navigate to **AppStore**
3. Search for **"Neighborhood BBS"**
4. Click **Install**
5. Configure:
   - Port: `5000` (default)
   - Admin Password: `your_password`
6. Click **Deploy**

Wait ~30 seconds for container to start.

Access BBS at: `http://<zimaboard-ip>:5000`

## Managing via CasaOS

- **View logs:** Apps → Neighborhood BBS → View logs
- **Restart:** Apps → Neighborhood BBS → Restart
- **Stop/Start:** Apps → Neighborhood BBS → Stop/Start
- **Update:** Apps → Neighborhood BBS → Update (when new version available)
- **Uninstall:** Apps → Neighborhood BBS → Uninstall

## First Time Setup

After installation:

1. **Change admin password:**
   - Visit `http://<zimaboard-ip>:5000/admin`
   - Login: sysop / gh0stly
   - Settings → Change password

2. **Add custom bulletins:**
   - Admin panel → New bulletin
   - Title: Your message
   - Text: Content

3. **Configure WiFi:**
   - If using USB adapter, set SSID
   - Default: `NEIGHBORHOOD_BBS`

---

# Multi-Instance Setup (Advanced)

Run multiple BBS instances on one ZimaBoard:

## Docker Compose with Multiple Services

```yaml
version: '3.8'

services:
  bbs-1:
    image: neighborhood-bbs:latest
    restart: unless_stopped
    ports:
      - "5001:5000"
    volumes:
      - bbs_1_data:/app/data
    environment:
      ADMIN_PASSWORD: password1

  bbs-2:
    image: neighborhood-bbs:latest
    restart: unless_stopped
    ports:
      - "5002:5000"
    volumes:
      - bbs_2_data:/app/data
    environment:
      ADMIN_PASSWORD: password2

  bbs-3:
    image: neighborhood-bbs:latest
    restart: unless_stopped
    ports:
      - "5003:5000"
    volumes:
      - bbs_3_data:/app/data
    environment:
      ADMIN_PASSWORD: password3

volumes:
  bbs_1_data:
  bbs_2_data:
  bbs_3_data:
```

Run:
```bash
docker-compose -f docker-compose.multi.yml up -d
```

Access instances:
- BBS 1: `http://<ip>:5001`
- BBS 2: `http://<ip>:5002`
- BBS 3: `http://<ip>:5003`

---

# Network Configuration

## Exposing via Nginx Reverse Proxy

For production, use nginx to:
- Expose on port 80 (HTTP standard)
- Handle SSL/TLS (HTTPS)
- Mask internal ports
- Load balance multiple instances

### Nginx config example:

```nginx
upstream bbs_backend {
    server localhost:5000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 10M;

    location / {
        proxy_pass http://bbs_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /ws {
        proxy_pass http://bbs_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

Apply:
```bash
cp nginx.conf /etc/nginx/sites-available/bbs
ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
systemctl restart nginx
```

Access at: `http://<zimaboard-ip>` (port 80)

---

# Backup & Restore

## Backing Up Data

### Native Debian

```bash
# Backup SQLite database
cp /path/to/bbs.db /backup/bbs_$(date +%Y%m%d_%H%M%S).db

# Or automated backup (cron)
0 2 * * * cp /path/to/bbs.db /backup/bbs_$(date +\%Y\%m\%d).db
```

### Docker

```bash
# Export volume data
docker run --rm -v bbs_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/bbs_data.tar.gz -C /data .

# Or use Docker Desktop for GUI backup
```

## Restoring Data

### Native Debian

```bash
# Stop service
systemctl stop bbs

# Restore database
cp /backup/bbs_latest.db /path/to/bbs.db

# Restart
systemctl start bbs
```

### Docker

```bash
# Create new volume from backup
docker volume create bbs_data_new

# Restore data
docker run --rm -v bbs_data_new:/data -v /backup:/backup \
  alpine tar xzf /backup/bbs_data.tar.gz -C /data

# Update docker-compose.yml to use new volume
# Then restart:
docker-compose up -d
```

---

# SSL/HTTPS Configuration

For internet-facing deployments:

```bash
# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Update nginx config
# ... ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ... ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Restart nginx
systemctl restart nginx

# Auto-renew
certbot renew --quiet --cron
```

---

# Monitoring & Logging

## Health Check

```bash
# Manual health check
curl http://localhost:5000/health

# Expected response:
# {
#   "status": "healthy",
#   "messages": 42,
#   "bulletins": 3,
#   "clients": 5,
#   "timestamp": "2026-03-16T10:30:45.123456"
# }
```

## Real-time Logs

### Native Debian

```bash
journalctl -u bbs -f
```

### Docker

```bash
docker-compose logs -f neighborhood-bbs
```

## Disk Usage

```bash
# Check database size
du -sh /path/to/bbs.db

# If too large, archive old messages
sqlite3 /path/to/bbs.db \
  "DELETE FROM messages WHERE datetime(created_at) < datetime('now', '-30 days')"
```

---

# Troubleshooting References

- **Native Debian issues:** See [Debian Troubleshooting](#troubleshooting)
- **Docker issues:** See [Docker Troubleshooting](#docker-troubleshooting)
- **General issues:** See [Neighborhood BBS Main Docs](../../README.md)

---

**Last Updated:** March 2026  
**Supported Platforms:** Debian 10+, Ubuntu 20.04+, CasaOS 0.4.4+  
**Docker Image:** ghcr.io/gh0stlykn1ght/neighborhood-bbs

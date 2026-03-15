# Neighborhood BBS - Debian/Ubuntu Setup Guide

Complete setup guide for Debian, Ubuntu, and Ubuntu-based Linux distributions.

---

## Quick Start

### Method 1: Docker (Easiest)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Clone and run
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d

# Access: http://localhost:8080
```

### Method 2: Native Installation

```bash
# Install dependencies
sudo apt update && sudo apt install -y python3.10 python3-pip python3-venv sqlite3 git

# Clone repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 scripts/init-db-local.py

# Run
python3 src/main.py
```

---

## Full Installation Guide

### Prerequisites

#### Debian 12 (Bookworm)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    build-essential git sqlite3 curl wget
```

#### Ubuntu 22.04 LTS
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3-pip python3-venv \
    build-essential git sqlite3
```

#### Ubuntu 24.04 LTS
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv \
    build-essential git sqlite3
```

#### Debian 11 (Bullseye) - Legacy
```bash
sudo apt update
sudo apt install -y python3.9 python3-pip python3-venv git sqlite3
# Note: Ensure pip is up-to-date
pip install --upgrade pip setuptools wheel
```

---

## Installation Methods

### Option 1: Docker Compose (Recommended for Production)

#### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# Generate secure SECRET_KEY
SECRET_KEY=$(python3 -c "import os; print(os.urandom(32).hex())")

# Create .env file
cat > .env << EOF
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
MAX_CONNECTIONS=100
EOF

# Build and start
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d

# Verify
docker-compose ps
docker-compose logs -f
```

#### Access
```
Browser: http://localhost:8080
Default Admin: admin / admin (change immediately!)
```

#### Management
```bash
# View logs
docker-compose logs -f bbs

# Stop
docker-compose down

# Restart
docker-compose restart

# Remove everything (including data!)
docker-compose down -v
```

---

### Option 2: Native Python Installation

#### Step 1: System Setup

```bash
# Create application user (optional but recommended)
sudo useradd -m -s /bin/bash nbbs
sudo su - nbbs

# Or use your existing user
cd /home/$USER
```

#### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS
```

#### Step 3: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### Step 4: Install Dependencies

```bash
# Install from requirements
pip install -r requirements.txt

# Optional: Development dependencies (for testing/development)
pip install -r requirements-dev.txt
```

#### Step 5: Configuration

```bash
# Generate secure key
SECRET_KEY=$(python3 -c "import os; print(os.urandom(32).hex())")

# Create .env
cat > .env << EOF
FLASK_ENV=production
DEBUG=false
SECRET_KEY=$SECRET_KEY
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
DATABASE_PATH=data/neighborhood.db
LOG_PATH=logs/
EOF
```

#### Step 6: Initialize Database

```bash
python3 scripts/init-db-local.py

# Expected output:
# Creating database tables...
# Initializing default rooms...
# Creating default theme...
# Database ready at: data/neighborhood.db
```

#### Step 7: Create Admin Account

```bash
python3 scripts/create_admin_user.py
# Follow prompts:
# Username: admin
# Email: admin@example.com
# Password: [strong password - minimum 12 characters]
```

#### Step 8: Start the Application

```bash
python3 src/main.py

# Expected output:
# INFO - Neighborhood BBS starting...
# INFO - Database initialized successfully
# WARNING - Running with debug=false
#  * Running on http://127.0.0.1:8080
#  * Press CTRL+C to quit
```

#### Step 9: Access the Application

```
Browser: http://localhost:8080
Admin Panel: http://localhost:8080/admin/
Login: admin / [your-password]
```

---

### Option 3: Systemd Service (Auto-start on Boot)

#### Create Service File

```bash
# Create service
sudo tee /etc/systemd/system/neighborhood-bbs.service > /dev/null << 'EOF'
[Unit]
Description=Neighborhood BBS - Secure Team Communication
After=network.target
Documentation=https://github.com/yourusername/Neighborhood_BBS

[Service]
Type=simple
User=nbbs
Group=nbbs
WorkingDirectory=/home/nbbs/Neighborhood_BBS
Environment="PATH=/home/nbbs/Neighborhood_BBS/venv/bin"
ExecStart=/home/nbbs/Neighborhood_BBS/venv/bin/python server/src/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/neighborhood-bbs.log
StandardError=append:/var/log/neighborhood-bbs.log

[Install]
WantedBy=multi-user.target
EOF
```

#### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable neighborhood-bbs

# Start service
sudo systemctl start neighborhood-bbs

# Check status
sudo systemctl status neighborhood-bbs

# View logs
sudo journalctl -u neighborhood-bbs -f

# Stop service
sudo systemctl stop neighborhood-bbs
```

---

## Networking Configuration

### Localhost Only (Default - Most Secure)

```bash
# No additional configuration needed
# Access only from this machine: http://localhost:8080
```

### Local Network Access

#### Option A: Nginx Reverse Proxy

```bash
# Install nginx
sudo apt install -y nginx

# Create config
sudo tee /etc/nginx/sites-available/neighborhood-bbs > /dev/null << 'EOF'
upstream nbbs_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name _;
    
    # Disable server tokens
    server_tokens off;

    location / {
        proxy_pass http://nbbs_backend;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable
sudo ln -s /etc/nginx/sites-available/neighborhood-bbs /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and start
sudo nginx -t
sudo systemctl restart nginx
```

#### Option B: SSH Tunnel (Most Secure for Remote Access)

From remote machine:
```bash
# Create secure tunnel
ssh -L 8080:127.0.0.1:8080 user@bbs-server.example.com

# Then access: http://localhost:8080
```

#### Option C: UFW Firewall Rules

```bash
# Install UFW
sudo apt install -y ufw

# Default deny incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow BBS from local network only
sudo ufw allow from 192.168.1.0/24 to any port 8080

# Enable firewall
sudo ufw enable

# Check rules
sudo ufw status
```

---

## Security Hardening

### SSL/TLS with Let's Encrypt (HTTPS)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (requires domain and public access)
sudo certbot certonly --nginx -d your-domain.com

# Update nginx config
sudo tee /etc/nginx/sites-available/neighborhood-bbs-ssl > /dev/null << 'EOF'
upstream nbbs_backend {
    server 127.0.0.1:8080;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://nbbs_backend;
        proxy_set_header X-Forwarded-Proto $scheme;
        # ... other headers ...
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
EOF

# Reload nginx
sudo systemctl restart nginx
```

### AppArmor Profile

```bash
# Create profile
sudo tee /etc/apparmor.d/usr.bin.python3-nbbs > /dev/null << 'EOF'
#include <tunables/global>

/usr/bin/python3 {
  #include <abstractions/base>
  #include <abstractions/python>
  
  /home/nbbs/Neighborhood_BBS/** r,
  /home/nbbs/Neighborhood_BBS/data/ r,
  /home/nbbs/Neighborhood_BBS/data/** rw,
  /home/nbbs/Neighborhood_BBS/logs/ r,
  /home/nbbs/Neighborhood_BBS/logs/** rw,
  
  deny /sys/module/apparmor/parameters/logsyscall w,
  deny capability sys_module,
  deny capability sys_admin,
}
EOF

# Load profile
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.python3-nbbs
```

### SELinux Context (if applicable)

```bash
# Check if SELinux is installed
getenforce

# If using SELinux:
sudo semanage fcontext -a -t http_port_t -p tcp 8080
sudo restorecon -v /home/nbbs/Neighborhood_BBS
```

---

## Backup & Restore

### Automated Daily Backups

```bash
#!/bin/bash
# /home/nbbs/backup-bbs.sh

BACKUP_DIR="/home/nbbs/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
cp /home/nbbs/Neighborhood_BBS/data/neighborhood.db "$BACKUP_DIR/neighborhood.db.$TIMESTAMP"

# Compress
gzip "$BACKUP_DIR/neighborhood.db.$TIMESTAMP"

# Keep last 30 days only
find "$BACKUP_DIR" -name "neighborhood.db.*" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### Schedule with Crontab

```bash
# Open crontab editor
crontab -e

# Add line: Daily backup at 2 AM
0 2 * * * /home/nbbs/backup-bbs.sh
```

### Restore from Backup

```bash
# Stop the service
sudo systemctl stop neighborhood-bbs

# Restore database
cp /home/nbbs/backups/neighborhood.db.20240314-020000.gz ./
gunzip neighborhood.db.20240314-020000.gz
cp neighborhood.db.20240314-020000 /home/nbbs/Neighborhood_BBS/data/neighborhood.db

# Restart
sudo systemctl start neighborhood-bbs
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
sudo lsof -i :8080

# Kill process (if safe)
sudo kill -9 PID

# Or use different port
echo "PORT=9000" >> .env
```

### Permission Denied Errors

```bash
# Fix permissions after git clone
sudo chown -R nbbs:nbbs /home/nbbs/Neighborhood_BBS
chmod -R 755 /home/nbbs/Neighborhood_BBS
chmod -R 700 /home/nbbs/Neighborhood_BBS/data
```

### Database Lock Errors

```bash
# SQLite locked - usually temporary
# Just wait a few seconds and retry

# Force unlock (dangerous - only if confident no processes using DB)
sqlite3 /home/nbbs/Neighborhood_BBS/data/neighborhood.db ".tables"

# Compact/optimize database
sqlite3 /home/nbbs/Neighborhood_BBS/data/neighborhood.db "VACUUM;"
```

### High Memory Usage

```bash
# Monitor resource usage
watch -n 1 free -h

# Check Python process
ps aux | grep python3

# If using too much memory, archive old messages:
sqlite3 data/neighborhood.db "DELETE FROM messages WHERE created_at < datetime('now', '-90 days');"
sqlite3 data/neighborhood.db "VACUUM;"
```

### Can't Connect to Application

```bash
# Test connectivity
curl http://localhost:8080

# Check if service is running
sudo systemctl status neighborhood-bbs

# Check logs
sudo journalctl -u neighborhood-bbs -n 50

# Restart service
sudo systemctl restart neighborhood-bbs
```

---

## Performance Tips

### Database Optimization

```bash
# Run periodic maintenance
sqlite3 data/neighborhood.db << 'SQL'
VACUUM;
ANALYZE;
REINDEX;
SQL
```

### Python Performance

```bash
# Use PyPy for better performance (optional)
sudo apt install -y pypy3 pypy3-venv

# Create PyPy virtual environment
pypy3 -m venv venv-pypy
source venv-pypy/bin/activate
pip install -r requirements.txt
```

### Resource Limits

```bash
# Edit service file
sudo systemctl edit neighborhood-bbs

# Add under [Service] section:
MemoryLimit=512M
CPUQuota=50%
```

---

## Update & Maintenance

### Update Application

```bash
# Stop service
sudo systemctl stop neighborhood-bbs

# Pull latest code
cd /home/nbbs/Neighborhood_BBS
git pull origin main

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart
sudo systemctl start neighborhood-bbs
```

### Security Updates

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade pip
pip audit  # Check for vulnerabilities
pip install --upgrade -r requirements.txt

# Restart application
sudo systemctl restart neighborhood-bbs
```

---

## Running Multiple Instances

### Different Ports

```bash
# Instance 1 (Port 8080) - Operations
PORT=8080 python3 src/main.py

# Instance 2 (Port 8081) - Intelligence
PORT=8081 python3 src/main.py

# Instance 3 (Port 8082) - Coordination
PORT=8082 python3 src/main.py
```

### Docker Multi-Instance

```bash
# Operations team
docker run -d --name bbs-ops -p 8080:8080 -v ops_data:/app/data neighborhood-bbs

# Intelligence team
docker run -d --name bbs-intel -p 8081:8080 -v intel_data:/app/data neighborhood-bbs

# Command & Control
docker run -d --name bbs-cc -p 8082:8080 -v cc_data:/app/data neighborhood-bbs
```

---

## Integration with System Services

### Run After Network Startup

```bash
# Edit service
sudo systemctl edit neighborhood-bbs

# Add:
[Unit]
After=network-online.target
Wants=network-online.target
```

### Run with Specific User/Security Context

```bash
# Edit service
sudo systemctl edit neighborhood-bbs

# Add:
[Service]
User=nbbs
Group=nbbs
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=true
PrivateTmp=yes
```

---

## Support

- **Docker Issues:** See [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **Security:** See [SECURITY_AUDIT_FINAL.md](SECURITY_AUDIT_FINAL.md)
- **API:** See [docs/API.md](docs/API.md)
- **Development:** See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

**Neighborhood BBS - Secure communication for Linux users.**

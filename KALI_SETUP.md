# Neighborhood BBS - Kali Linux Setup Guide

**For Security Professionals, Red Teamers, Bug Bounty Hunters, and Pentesters**

This guide provides optimized setup for Kali Linux (and other Debian-based distributions) to run Neighborhood BBS as a secure team communication and intelligence sharing platform.

---

## Why Neighborhood BBS for Security Teams?

✅ **Secure Team Chat** - Real-time communication without cloud dependency  
✅ **Bulletin Board** - Share findings, techniques, and intelligence  
✅ **Offline Capable** - Run on isolated networks or behind firewalls  
✅ **Retro Terminal UI** - Clean, minimal interface with no bloat  
✅ **No Cloud Metadata** - All data stays on your infrastructure  
✅ **Easy Deployment** - Docker or bare Python on any Debian system  
✅ **Lightweight** - Runs on low-end hardware (Raspberry Pi, old laptops)  

Perfect for:
- Red team internal communications
- Bug bounty hunting collaboration
- Penetration testing labs
- Networking at security conferences (local network)
- CTF event coordination
- Security research groups
- Incident response teams

---

## Installation Options

### Option 1: Docker (Recommended for Teams)

#### Prerequisites

```bash
# Update Kali repositories
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
docker-compose --version
```

#### Run Neighborhood BBS in Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# Create .env file with secure settings
cat > .env << 'EOF'
SECRET_KEY=$(python3 -c "import os; print(os.urandom(32).hex())")
FLASK_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
EOF

# Build and start the container
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d

# View logs
docker-compose logs -f bbs

# Access the BBS
# Open browser: http://localhost:8080
```

#### Multi-Team Docker Deployment

For large teams, run multiple isolated instances:

```bash
# Instance 1: Red Team Operations
docker-compose -f docker/docker-compose.linux.yml -p redteam up -d
# Access: http://localhost:8080

# Instance 2: Bug Bounty Hunters
docker run -d \
  --name bbs-bounty \
  -p 8081:8080 \
  -v bounty_data:/app/data \
  -e SECRET_KEY=$(python3 -c "import os; print(os.urandom(32).hex())") \
  neighborhood-bbs

# Instance 3: Pentesting Lab
docker run -d \
  --name bbs-lab \
  -p 8082:8080 \
  -v lab_data:/app/data \
  neighborhood-bbs
```

---

### Option 2: Bare Installation (Direct Python)

#### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and dependencies
sudo apt install -y python3.10 python3-pip python3-venv git sqlite3 build-essential

# Verify Python version
python3 --version  # Should be 3.10+
```

#### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate secure SECRET_KEY
# Save this string somewhere safe
python3 -c "import os; print('SECRET_KEY=' + os.urandom(32).hex())"

# 5. Create .env file
cat > .env << 'EOF'
FLASK_ENV=production
DEBUG=false
SECRET_KEY=YOUR_SECURE_KEY_HERE
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
DATABASE_PATH=data/neighborhood.db
EOF

# 6. Initialize database
python3 scripts/init-db-local.py

# 7. Create first admin account
python3 scripts/create_admin_user.py
# Follow prompts (suggested: username "admin", strong password)

# 8. Start the server
python3 src/main.py
```

Your server will be accessible at `http://localhost:8080`

---

## Networking Setup for Remote Teams

### Local Network Only (Recommended)

By default, BBS listens only on localhost. For local network access:

**Option 1: Reverse Proxy with Nginx**

```bash
# Install nginx
sudo apt install -y nginx

# Create Neighborhood BBS upstream
sudo tee /etc/nginx/sites-available/bbs << 'EOF'
upstream bbs_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name bbs.local;

    location / {
        proxy_pass http://bbs_backend;
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

# Enable the site
sudo ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Add to /etc/hosts on client machines
echo "192.168.1.100 bbs.local" | sudo tee -a /etc/hosts
```

**Option 2: SSH Tunnel (Most Secure)**

From client machine:
```bash
# Create SSH tunnel to BBS server
ssh -L 8080:127.0.0.1:8080 user@bbs-server.local

# Now access via: http://localhost:8080
```

### VPN/Isolated Network Setup

For truly isolated team communication on untrusted networks:

```bash
# 1. Generate Wireguard keys
wg genkey | tee privatekey | wg pubkey > publickey

# 2. Create /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.1/24
PrivateKey = [YOUR_PRIVATE_KEY]
ListenPort = 51820

[Peer]
PublicKey = [CLIENT_PUBLIC_KEY]
AllowedIPs = 10.0.0.2/32

# 3. Enable and start WireGuard
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0

# 4. Update BBS to listen on VPN interface
# Edit .env: HOST=10.0.0.1
# Restart BBS

# 5. Clients connect to VPN and access http://10.0.0.1:8080
```

---

## Integration with Kali Tools

### Sharing Scan Results

```bash
# 1. Run Nmap scan
nmap -A -p- --script http-title 192.168.1.0/24 > scan.txt

# 2. Post to Neighborhood BBS via API
curl -X POST http://localhost:8080/api/board/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Network Scan: 192.168.1.0/24",
    "content": "'"$(cat scan.txt)"'",
    "author": "red-team",
    "category": "findings"
  }'
```

### Metasploit Integration Script

```bash
#!/bin/bash
# post-exploit-to-bbs.sh - Share exploitation results

TARGET=$1
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Create report
REPORT="Target: $TARGET
Time: $TIMESTAMP
$(msfvenom -p windows/meterpreter/reverse_tcp | strings | grep -i version)"

# Post to BBS
curl -X POST http://localhost:8080/api/board/posts \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Exploitation Report: $TARGET\",
    \"content\": \"$REPORT\",
    \"author\": \"pentest-team\",
    \"category\": \"events\"
  }"
```

### SQLMap Result Sharing

```bash
#!/bin/bash
# share-sqlmap-findings.sh

URL=$1

# Run SQLMap
sqlmap -u "$URL" --batch --dump 2>&1 | tee sqlmap_report.txt

# Extract findings
FINDINGS=$(grep -A5 "retrieved" sqlmap_report.txt)

# Post to BBS
curl -X POST http://localhost:8080/api/board/posts \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"SQL Injection Found: $URL\",
    \"content\": \"$FINDINGS\",
    \"author\": \"sqlmap-bot\",
    \"category\": \"findings\"
  }"
```

---

## Performance Optimization for Red Teams

### Resource Limits

For Kali machines running alongside heavy tools (Burp Suite, Wireshark, etc.):

```bash
# Limit BBS memory usage to 256MB
python3 -c "
import resource
resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
" && python3 src/main.py
```

### Database Maintenance

```bash
#!/bin/bash
# optimize-bbs-db.sh

# Vacuum database (reclaim space from deleted messages)
sqlite3 data/neighborhood.db "VACUUM;"

# Analyze for better query performance
sqlite3 data/neighborhood.db "ANALYZE;"

# Check database integrity
sqlite3 data/neighborhood.db "PRAGMA integrity_check;"
```

### Archive Old Chat Logs

```bash
#!/bin/bash
# archive-old-logs.sh - Keep active chat, archive older messages

sqlite3 data/neighborhood.db << 'SQL'
-- Create archive table
CREATE TABLE IF NOT EXISTS messages_archive AS
SELECT * FROM messages WHERE created_at < datetime('now', '-30 days');

-- Delete archived messages from active table
DELETE FROM messages WHERE created_at < datetime('now', '-30 days');

-- Optimize database
VACUUM;
SQL

echo "Archived messages older than 30 days"
```

---

## Security Hardening for Sensitive Environments

### Network Isolation

```bash
# Create isolated bridge for BBS only
sudo ip link add name bbs-isolated type bridge
sudo ip addr add 172.20.0.1/24 dev bbs-isolated
sudo ip link set bbs-isolated up

# Run BBS container on isolated network
docker network create --driver bridge --subnet=172.20.0.0/24 bbs-isolated
docker run -d \
  --name bbs-secure \
  --network bbs-isolated \
  -p 172.20.0.1:8080:8080 \
  neighborhood-bbs
```

### Firewall Rules (UFW)

```bash
# Allow only localhost access
sudo ufw default deny incoming
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 8080
sudo ufw allow from 192.168.1.0/24 to 192.168.1.100 port 8080  # Team network only
sudo ufw enable
```

### Container Security (AppArmor)

```bash
# Create AppArmor profile for BBS
sudo tee /etc/apparmor.d/docker-bbs << 'EOF'
#include <tunables/global>

profile docker-bbs flags=(attach_disconnected) {
  #include <abstractions/base>
  
  deny /sys/module/apparmor/parameters/logsyscall w,
  deny /sys/module/audit/** w,
  deny capability sys_module,
  deny capability sys_admin,
}
EOF

sudo apparmor_parser -r /etc/apparmor.d/docker-bbs
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8080
sudo lsof -i :8080

# Kill process (if safe)
sudo kill -9 PID

# Or use different port in .env: PORT=9000
```

### Database Corruption

```bash
# Check database integrity
sqlite3 data/neighborhood.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp data/neighborhood.db data/neighborhood.db.corrupt
cp data/neighborhood.db.backup data/neighborhood.db

# Or reinitialize (WARNING: loses data)
rm data/neighborhood.db
python3 scripts/init-db-local.py
```

### Slow Performance

```bash
# Monitor system resources
watch -n 1 'free -h && ps aux | grep python3'

# Check database size
du -sh data/neighborhood.db

# Archive old messages (see above)
bash scripts/archive-old-logs.sh
```

### Python Module Errors

```bash
# Reinstall dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Or create fresh environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Automated Startup Scripts

### Systemd Service (Bare Installation)

```bash
# Create service file
sudo tee /etc/systemd/system/neighborhood-bbs.service << 'EOF'
[Unit]
Description=Neighborhood BBS - Secure Team Chat
After=network.target

[Service]
Type=simple
User=bbs
WorkingDirectory=/opt/neighborhood-bbs
Environment="PATH=/opt/neighborhood-bbs/venv/bin"
ExecStart=/opt/neighborhood-bbs/venv/bin/python src/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable neighborhood-bbs
sudo systemctl start neighborhood-bbs

# Check status
sudo systemctl status neighborhood-bbs
```

### Docker Startup Script

```bash
#!/bin/bash
# start-bbs-docker.sh

cd /opt/neighborhood-bbs

# Pull latest
docker pull neighborhood-bbs:latest

# Start container with restart policy
docker run -d \
  --name neighborhood-bbs \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v bbs_data:/app/data \
  -v bbs_logs:/app/logs \
  -e SECRET_KEY=$(cat .env | grep SECRET_KEY | cut -d= -f2) \
  neighborhood-bbs

echo "Neighborhood BBS started"
docker logs -f neighborhood-bbs
```

---

## Example Red Team Configuration

```bash
#!/bin/bash
# setup-redteam-bbs.sh

# 1. Create dedicated user
sudo useradd -m -s /bin/bash bbs
sudo su - bbs

# 2. Setup environment
cd /home/bbs
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# 3. Create isolated Python environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Secure configuration
python3 -c "import os; print('SECRET_KEY=' + os.urandom(32).hex())" > secret.txt
cat secret.txt >> .env

# 6. Initialize
python3 scripts/init-db-local.py

# 7. Create team admin account
python3 scripts/create_admin_user.py
# Username: team-commander
# Strong password: [generate with: openssl rand -base64 16]

# 8. Setup firewall for team network only
sudo ufw allow from 192.168.1.0/24 to 192.168.1.100 port 8080

# 9. Start service
sudo systemctl start neighborhood-bbs
sudo systemctl status neighborhood-bbs

# 10. Verify
curl http://localhost:8080
```

---

## Backing Up Team Data

```bash
#!/bin/bash
# backup-bbs.sh

BACKUP_DIR="/mnt/secure-backup/bbs-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
cp data/neighborhood.db "$BACKUP_DIR/"

# Backup configuration
cp .env "$BACKUP_DIR/"

# Backup logs
cp -r logs "$BACKUP_DIR/"

# Encrypt backup (optional but recommended)
tar -czf - "$BACKUP_DIR" | gpg --symmetric --cipher-algo AES256 > "bbs-backup-$(date +%Y%m%d).tar.gz.gpg"

# Clean unencrypted copy if encrypted
rm -rf "$BACKUP_DIR"

echo "Backup complete: bbs-backup-$(date +%Y%m%d).tar.gz.gpg"
```

---

## Tips for Security Professionals

### Hide It From Network Scanning
```bash
# Restrict TLS/SSL fingerprinting
# Use minimal HTTP headers
# Run on non-standard ports (change from 8080)
PORT=7331 python3 src/main.py

# Or proxy through proxy_pass to hide signatures
```

### Enable Command Logging
```bash
# Log all BBS activity for post-engagement reports
tail -f logs/neighborhood.log | tee engagement_$(date +%Y%m%d).log
```

### Team Separation (Multiple Instances)
```bash
# Separate instances by team/role
# Red Team: http://localhost:8080
# Blue Team: http://localhost:8081
# White Hats: http://localhost:8082
```

### Automate Report Generation
```bash
#!/bin/bash
# Generate team report from BBS

sqlite3 data/neighborhood.db << 'SQL' > team_report.txt
SELECT 'Team Chat Logs:' || char(10);
SELECT '[' || created_at || '] ' || author || ': ' || content FROM messages;
SELECT '' || char(10) || 'Findings:' || char(10);
SELECT '- ' || title || char(10) || '  ' || content FROM posts WHERE category = 'findings';
SQL

cat team_report.txt > engagement_report_$(date +%Y%m%d).txt
```

---

## Next Steps

1. **Choose Installation Method:** Docker (recommended) or bare Python
2. **Configure Networking:** Local only, SSH tunnel, or VPN
3. **Set Up Team Accounts:** Create admin and team member accounts
4. **Integrate Tools:** Connect Nmap, Metasploit, SQLMap, etc.
5. **Schedule Backups:** Set up automated encrypted backups
6. **Test Security:** Verify firewall rules and access control

---

## Support & Resources

- **Documentation:** See [DOCKER_SETUP.md](DOCKER_SETUP.md) for Docker specifics
- **API Reference:** See [docs/API.md](docs/API.md) for programmatic access
- **Security:** See [SECURITY_AUDIT_FINAL.md](SECURITY_AUDIT_FINAL.md) for security implementation details
- **Issues:** Report bugs via GitHub issues
- **Community:** Join security professional community channels

---

**Neighborhood BBS - By security professionals, for security professionals.**

Keep chatting, stay secure, hack responsibly. 🛡️

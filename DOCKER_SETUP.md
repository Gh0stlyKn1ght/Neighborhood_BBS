# Docker Setup Guide - Neighborhood BBS

## Overview

Running Neighborhood BBS in Docker provides **security isolation**, **consistency across platforms**, and **easy deployment**. This guide covers:
- Windows (Docker Desktop)
- Raspberry Pi / Linux servers
- Complete security best practices

---

## Security Features in Docker

✅ **Non-root user** - Runs as `bbsuser` (UID 1000), not root  
✅ **Dropped capabilities** - No unnecessary Linux capabilities  
✅ **Resource limits** - CPU and memory constraints prevent DoS  
✅ **Read-only root** - Filesystem hardening where possible  
✅ **Network isolation** - Private bridge network  
✅ **Health checks** - Automatic monitoring and restart  
✅ **No privileged mode** - No `--privileged` flag  
✅ **Localhost-only** - Port 8080 only accessible from this machine  

---

## Windows Setup (Docker Desktop)

### Prerequisites
1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Enable WSL 2 backend (recommended)
3. Clone the Neighborhood BBS repository

### Running Locally on Windows

```powershell
# Navigate to project directory
cd C:\Users\YourName\Desktop\Neighborhood_BBS

# Build and start the container
docker-compose -f docker\docker-compose.yml -f docker\docker-compose.windows.yml up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Access the BBS
# Open browser: http://localhost:8080
```

### Environment Variables (Windows)

Create a `.env` file in the project root:

```env
SECRET_KEY=your-very-secure-random-key-here-min-32-chars
NBBS_DATA_PATH=./data
NBBS_LOGS_PATH=./logs
```

### Important Windows Notes

- Docker Desktop runs in Hyper-V on Windows
- Volumes use Windows paths (converted automatically)
- Network is accessible only from your local machine
- To remote access: Use SSH tunnel or configure firewall rules

### Accessing from Other Machines (Not Recommended)

If you must expose it (not recommended for security):

```yaml
ports:
  - "0.0.0.0:8080:8080"  # Warning: exposes to entire network
```

Then access via: `http://<windows-machine-ip>:8080`

---

## Linux / Raspberry Pi Setup

### Prerequisites

**Raspberry Pi / Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Reboot to apply group changes
sudo reboot
```

### Running on Raspberry Pi

```bash
# Navigate to project directory
cd ~/Neighborhood_BBS

# Create data directories
sudo mkdir -p /opt/neighborhood-bbs/data /opt/neighborhood-bbs/logs
sudo chown $USER:$USER /opt/neighborhood-bbs/{data,logs}

# Build and start (uses ARMv7 Dockerfile)
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d

# View logs
docker-compose logs -f neighborhood-bbs

# Check status
docker ps

# Stop the container
docker-compose down
```

### Environment Setup (Linux)

Create `.env` file:

```bash
# Generate a strong secret key
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
echo "SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n1)" >> .env
```

### Accessing from Remote (Secure SSH Tunnel)

Instead of exposing port 8080 to the network, use SSH tunneling:

```bash
# On your local machine (Windows/Mac/Linux)
ssh -L 8080:localhost:8080 pi@raspberrypi.local

# Then access: http://localhost:8080
# Connection is encrypted through SSH
```

### Systemd Service (Optional - Auto-start on Pi)

Create `/etc/systemd/system/neighborhood-bbs.service`:

```ini
[Unit]
Description=Neighborhood BBS Docker Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/Neighborhood_BBS
ExecStart=/usr/bin/docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d
ExecStop=/usr/bin/docker-compose down
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable neighborhood-bbs
sudo systemctl start neighborhood-bbs
sudo systemctl status neighborhood-bbs
```

---

## Security Best Practices

### 1. Secret Key Management

**Never commit `SECRET_KEY` to git!**

```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Store in .env (add to .gitignore)
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env
```

### 2. Network Isolation

- Containers run on internal `172.28.0.0/16` network
- Port 8080 is bound to `127.0.0.1` (localhost only)
- Use SSH tunneling for remote access instead of exposing ports

### 3. Resource Limits

- Max CPU: 1 core (Windows/Linux)
- Max Memory: 512MB (Windows/Linux), 256MB (Pi)
- Prevents resource exhaustion attacks

### 4. Capability Dropping

Container runs with minimal Linux capabilities:
- ✅ `NET_BIND_SERVICE` (can bind to port 8080)
- ❌ All others dropped for security

### 5. Read-Only Filesystem

Production deployment can be hardened further:

```yaml
read_only: true
tmpfs:
  - /tmp
  - /app/logs
```

### 6. Regular Updates

```bash
# Pull latest base image
docker pull python:3.11-slim

# Rebuild container
docker-compose build --no-cache

# Restart
docker-compose up -d
```

---

## Monitoring and Maintenance

### Check Container Status

```bash
# View running containers
docker ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f neighborhood-bbs

# Last 100 lines
docker-compose logs --tail=100
```

### Backup Data

```bash
# On Windows
docker run --rm -v neighborhood-bbs_nbbs-data:/app/data -v ${PWD}:/backup alpine tar czf /backup/nbbs-data-backup.tar.gz -C /app data

# On Linux
docker run --rm -v neighborhood-bbs_nbbs-data:/app/data -v /tmp:/backup alpine tar czf /backup/nbbs-data-backup.tar.gz -C /app data
```

### Database Management

```bash
# Connect to container bash
docker-compose exec neighborhood-bbs sh

# Access SQLite database
sqlite3 /app/data/neighborhood_bbs.db

# Import/export
sqlite3 /app/data/neighborhood_bbs.db < backup.sql
sqlite3 /app/data/neighborhood_bbs.db .dump > backup.sql
```

---

## Comparison: Docker vs Local

| Feature | Docker | Local Python |
|---------|--------|--------------|
| **Security** | ✅ Isolated, limited capabilities | ❌ Full system access |
| **Dependencies** | ✅ Containerized | ❌ Pollutes system |
| **Updates** | ✅ Easy (rebuild image) | ❌ Manual pip updates |
| **Dev Speed** | ⚠️ Rebuild needed | ✅ Direct changes |
| **Production** | ✅ Recommended | ❌ Not recommended |
| **Platform Consistency** | ✅ Same everywhere | ❌ OS-specific |
| **Scaling** | ✅ Multiple containers | ❌ Single instance |

---

## Troubleshooting

### Container won't start

```bash
# View detailed logs
docker-compose logs

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up

# Check resource limits
docker stats
```

### Permission denied errors

```bash
# Linux - add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again

# Check ownership
ls -la /opt/neighborhood-bbs/
sudo chown $USER:$USER /opt/neighborhood-bbs/{data,logs}
```

### Port already in use

```bash
# Find process using port 8080
# Windows: netstat -ano | findstr :8080
# Linux: sudo lsof -i :8080

# Kill the process or change port in docker-compose.yml
```

### No internet access in container

```bash
# Check network
docker network ls
docker network inspect nbbs_nbbs-network

# Rebuild network
docker-compose down
docker-compose up
```

---

## ESP8266 Note

The ESP8266 **cannot run Docker** (embedded microcontroller). It must run:
- **Native MicroPython** directly on the device
- See `firmware/esp8266/` for setup

---

## Next Steps

1. **Windows**: `docker-compose up -d` and visit `http://localhost:8080`
2. **Raspberry Pi**: SSH tunnel for secure remote access
3. **Production**: Enable SSL/TLS reverse proxy (nginx)
4. **Backup**: Regular database exports

---

**Your Neighborhood BBS is now running securely in Docker!** 🐳🏘️

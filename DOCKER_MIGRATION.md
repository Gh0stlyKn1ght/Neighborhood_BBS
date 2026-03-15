# Migration Guide: Local Python → Docker-Only

This guide helps you transition from running Neighborhood BBS with local Python to a secure Docker-only setup.

## Why Migrate to Docker?

✅ **Security**: Isolated container with dropped capabilities  
✅ **Consistency**: Same environment on Windows, Linux, Raspberry Pi  
✅ **Simplicity**: No Python/dependency management on host  
✅ **Production-Ready**: Matches enterprise deployment standards  
✅ **Easy Updates**: Rebuild container, no system pollution  

---

## Step 1: Stop Local Python Server

### Windows
```powershell
# Stop any running Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Verify it's stopped
Get-Process python -ErrorAction SilentlyContinue | Write-Host "Python still running"
```

### Linux/Pi
```bash
# Stop the server
sudo systemctl stop neighborhood-bbs 2>/dev/null || pkill -f "python src/main.py"

# Disable auto-start (if using systemd)
sudo systemctl disable neighborhood-bbs 2>/dev/null
```

---

## Step 2: Backup Your Data

### Windows
```powershell
# Backup database
Copy-Item -Path "data\neighborhood_bbs.db" -Destination "data\neighborhood_bbs.db.backup"

# Backup logs
Copy-Item -Path "logs\*" -Destination "logs.backup\" -Recurse
```

### Linux/Pi
```bash
# Create backup directory
mkdir -p ~/nbbs-backups
cd ~/nbbs-backups

# Backup database
cp ~/Neighborhood_BBS/data/neighborhood_bbs.db ./neighborhood_bbs.db.backup

# Export database
sqlite3 ~/Neighborhood_BBS/data/neighborhood_bbs.db ".dump" > database.sql

# Backup logs
tar czf logs.tar.gz ~/Neighborhood_BBS/logs/
```

---

## Step 3: Set Up Docker Environment

### Windows

1. **Install Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop
   - Enable WSL 2 backend (recommended)
   - Restart computer

2. **Create environment file**
   ```powershell
   # Generate strong secret key
   $secretKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((GCM -GenerateRandomBytes 32 | ForEach-Object { "{0:x2}" -f $_ } | Join-String)))
   
   # Create .env file
   @"
   SECRET_KEY=$secretKey
   NBBS_DATA_PATH=./data
   NBBS_LOGS_PATH=./logs
   "@ | Out-File -FilePath .env -Encoding ASCII
   ```

### Linux/Raspberry Pi

1. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   sudo apt install -y docker-compose
   ```

2. **Create environment file**
   ```bash
   # Generate strong secret key
   SECRET_KEY=$(openssl rand -hex 32)
   
   # Create .env file
   echo "SECRET_KEY=$SECRET_KEY" > .env
   chmod 600 .env  # Restrict permissions
   ```

3. **Prepare Docker volumes**
   ```bash
   # Create data directory (uses /opt for production)
   sudo mkdir -p /opt/neighborhood-bbs/data /opt/neighborhood-bbs/logs
   sudo chown $USER:$USER /opt/neighborhood-bbs/{data,logs}
   
   # Copy existing data if migrating
   cp -r ~/Neighborhood_BBS/data/* /opt/neighborhood-bbs/data/
   cp -r ~/Neighborhood_BBS/logs/* /opt/neighborhood-bbs/logs/ 2>/dev/null || true
   ```

---

## Step 4: Build and Start Docker Container

### Windows
```powershell
cd C:\Users\YourName\Desktop\Neighborhood_BBS

# Build the container
docker-compose -f docker\docker-compose.yml -f docker\docker-compose.windows.yml build

# Start the container
docker-compose -f docker\docker-compose.yml -f docker\docker-compose.windows.yml up -d

# Verify it's running
docker ps

# Check logs
docker-compose logs -f

# Access: http://localhost:8080
```

### Linux/Raspberry Pi
```bash
cd ~/Neighborhood_BBS

# Build the container
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml build

# Start the container
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.linux.yml up -d

# Verify it's running
docker ps

# Check logs
docker-compose logs -f

# For remote access, use SSH tunnel:
# ssh -L 8080:localhost:8080 user@raspberrypi.local
# Then access: http://localhost:8080
```

---

## Step 5: Verify Migration

### 1. Check Container Health
```bash
docker ps
docker stats neighborhood-bbs
```

### 2. Test Web Interface
```bash
# Windows or local access
curl http://localhost:8080

# Linux/Pi remote access
ssh -L 8080:localhost:8080 user@host
# Then open http://localhost:8080 in browser
```

### 3. Verify Data Persistence
```bash
# Create a test message in the BBS
# Then stop and restart container

docker-compose stop
docker-compose start

# Verify message is still there
curl http://localhost:8080
```

### 4. Check Logs
```bash
docker-compose logs --tail=50
```

---

## Step 6: Clean Up Local Python Installation

### Windows (Optional)

```powershell
# Remove Python virtual environment (not system Python)
Remove-Item -Path "venv" -Recurse -Force

# Keep local Python installed for other projects
# To uninstall: Settings > Apps > Python
```

### Linux/Raspberry Pi (Optional)

```bash
# Remove virtual environment
rm -rf ~/Neighborhood_BBS/venv

# Keep system Python
# Don't uninstall python3 as system depends on it
```

---

## Step 7: Enable Auto-Start (Production)

### Windows (Docker Desktop)

Docker Desktop automatically starts containers on system reboot if set to restart:
- Default: enabled in docker-compose.yml (`restart: unless-stopped`)

### Linux/Raspberry Pi (Systemd)

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

## Step 8: Final Checks

### Security Verification

```bash
# 1. Verify non-root user
docker exec neighborhood-bbs id
# Should show: uid=1000(bbsuser)

# 2. Check running process
docker exec neighborhood-bbs ps aux | grep main.py

# 3. Verify network isolation
docker exec neighborhood-bbs curl http://8.8.8.8 2>&1
# Should timeout or fail (no external internet)

# 4. Check resource limits
docker stats
```

### Backup Verification

```bash
# Test restore from backup
docker-compose down
docker volume rm neighborhood-bbs_nbbs-data
docker-compose up -d
# Data should be restored from volume
```

---

## Rollback Plan

If you need to revert to local Python:

### Windows
```powershell
# Stop Docker container
docker-compose down

# Restore from backup
Copy-Item "data\neighborhood_bbs.db.backup" -Destination "data\neighborhood_bbs.db"

# Start local Python
.\venv\Scripts\Activate.ps1
python scripts/init-db-local.py
python src/main.py
```

### Linux/Pi
```bash
# Stop Docker container
docker-compose down

# Restore from backup
cp ~/nbbs-backups/neighborhood_bbs.db.backup ~/Neighborhood_BBS/data/neighborhood_bbs.db

# Start local Python
source venv/bin/activate
python scripts/init-db-local.py
python src/main.py
```

---

## Troubleshooting Migration

### Container won't start

```bash
# Check detailed logs
docker-compose logs

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up

# Check disk space
docker system df

# Cleanup unused images/volumes
docker system prune -a
```

### Data not persisting

```bash
# Verify volume is mounted correctly
docker inspect neighborhood-bbs | grep -A 5 "Mounts"

# Check volume ownership (Linux)
ls -la /opt/neighborhood-bbs/

# Recreate volume
docker volume rm neighborhood-bbs_nbbs-data
docker volume create neighborhood-bbs_nbbs-data
```

### Port conflicts

```bash
# Find process using port 8080
# Windows: netstat -ano | findstr :8080
# Linux: sudo lsof -i :8080

# Change port in docker-compose.yml
# ports:
#   - "127.0.0.1:8081:8080"
```

---

## Success! 🎉

Your Neighborhood BBS is now running securely in Docker!

### Next Steps:
1. ✅ Docker running on Windows and/or Linux
2. ✅ Data persisted in volumes
3. ✅ Auto-restart enabled
4. ✅ Security hardened

### Maintenance:
- **Logs**: `docker-compose logs`
- **Restart**: `docker-compose restart`
- **Backup**: Regular SQLite exports
- **Updates**: `docker-compose build --no-cache && docker-compose up -d`

**Your neighborhood is now more secure!** 🏘️🐳

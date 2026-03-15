# 🚀 Local Setup - Quick Start

Get Neighborhood BBS running locally on Windows, Mac, or Linux in 5 minutes.

## For Windows Users 🪟

### Easiest Option (Batch Files)

1. **Double-click:** `scripts\setup-local.bat`
   - Wait for it to complete
   - When prompted, enter admin username and password

2. **Double-click:** `scripts\run-local.bat`
   - Server starts automatically
   - See address in console

3. **Open browser:** `http://localhost:8080`

### PowerShell Option (More Features)

```powershell
# Setup
.\scripts\setup-local.ps1

# Run (with options)
.\scripts\run-local.ps1              # Local only
.\scripts\run-local.ps1 -Network     # Allow network access
.\scripts\run-local.ps1 -Port 9000   # Use different port
```

---

## For Mac/Linux Users 🐧

### Setup

```bash
# Make scripts executable
chmod +x scripts/setup-local.sh scripts/run-local.sh

# Run setup
./scripts/setup-local.sh

# Enter admin username and password when prompted
```

### Run

```bash
# Basic
./scripts/run-local.sh

# Options
./scripts/run-local.sh --network     # Allow network access
./scripts/run-local.sh --port 9000   # Use different port
```

---

## Run on Raspberry Pi 🍓

Once you're comfortable locally, deploy to a Raspberry Pi as a dedicated server:

### Ultra-Quick Setup
```bash
# One-liner from Raspberry Pi:
curl https://raw.githubusercontent.com/Gh0stlyKn1ght/Neighborhood_BBS/main/firmware/raspberry-pi/setup.sh | bash
```

The script automatically:
1. Installs all dependencies
2. Sets up Python virtual environment
3. Initializes database
4. Creates systemd service (auto-starts on reboot)
5. Installs Nginx reverse proxy (optional HTTPS)

### After Setup
```bash
# Start service
sudo systemctl start neighborhood-bbs

# Check status
sudo systemctl status neighborhood-bbs

# View logs
sudo journalctl -u neighborhood-bbs -f

# Access
http://raspberrypi.local:8080
```

### Hardware Options
- **Pi 3B+** - Entry-level, ~$35
- **Pi 4** - Best value, ~$55 (recommended)
- **Pi 5** - Latest, ~$80

**See:** [firmware/raspberry-pi/README.md](firmware/raspberry-pi/README.md) for advanced setup (HTTPS, Nginx, optimization)

---

## Connect WiFi Devices (ESP8266/ESP32) 📡

Once the local server is running, you can connect IoT devices:

### Quick Setup
1. Configure `firmware/esp8266/config.py`:
   ```python
   SSID = "Your_WiFi_SSID"
   PASSWORD = "Your_WiFi_Password"
   SERVER_HOST = "192.168.1.100"  # Your computer's local IP
   SERVER_PORT = 8080
   ```

2. Flash MicroPython to ESP8266:
   ```bash
   esptool.py --port COM3 erase_flash
   esptool.py --port COM3 write_flash 0 micropython.bin
   ```

3. Upload code:
   ```bash
   ampy --port COM3 put firmware/esp8266/main.py
   ```

4. Device automatically connects to your BBS!

**See:** [firmware/esp8266/README.md](firmware/esp8266/README.md) for detailed instructions

**Manage devices in Admin Panel:** Device banning, monitoring, mesh networks

---

## Manual Setup (Any OS)

### 1. Install Python
- Download [Python 3.10+](https://www.python.org/downloads/)
- Verify: `python --version`

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Initialize Database
```bash
python server/scripts/init-db-local.py
python server/scripts/create_admin_user.py
```

### 5. Run the Server
```bash
cd server
python src/main.py
```

### 6. Open Browser
```
http://localhost:8080
```

---

## First Time Setup

### Admin Account
**Username:** `admin`  
**Password:** (as you set during setup)

⚠️ **Change your password immediately in the admin panel!**

### Initial Configuration
1. Login to admin panel: `http://localhost:8080/admin/login`
2. Go to "Network Configuration"
3. Customize settings for your needs
4. (Optional) Create custom theme

---

## What's Next?
### 🍓 Run on Raspberry Pi
Deploy as a dedicated server for your neighborhood:
- Automatic one-command setup
- Runs 24/7
- Auto-starts on power loss
- See [firmware/raspberry-pi/README.md](firmware/raspberry-pi/README.md)
### � Add WiFi Devices
Connect ESP8266/ESP32 nodes to your BBS:
- See [firmware/esp8266/README.md](firmware/esp8266/README.md)
- Automatic discovery and management
- Monitor hardware via admin panel

### �👥 Add Users
Share `http://localhost:8080` with others on your network:
- Same WiFi: Use your computer's local IP
- Remote: Use VPN or port forwarding

### ⚙️ Customize
- **Admin Panel:** `http://localhost:8080/admin/login`
  - Ban devices
  - Set chat retention
  - Configure themes
  - View hardware logs

- **Chat Rooms:** Create and manage from main interface

- **Settings:** Edit `.env` for advanced config

### 📱 Test on Mobile
1. Find your computer IP: 
   - Windows: `ipconfig` → Look for IPv4
   - Mac: `ifconfig` → Look for inet
   - Linux: `hostname -I`

2. From phone on same WiFi: `http://192.168.x.x:8080`

### 🔐 Make It Secure (Optional)
- Change admin password (do this first!)
- Configure SSL/HTTPS (see docs)
- Set device bans if needed
- Enable user registration controls

---

## Troubleshooting

### "Python not found"
**Windows:**
```powershell
# Check if Python is in PATH
python --version

# If not, reinstall from https://www.python.org/downloads/
# ✓ Check "Add Python to PATH" during installation
```

### "Port 8080 already in use"
Edit `.env`:
```env
PORT=8081  # Use 8081 instead
```

Then restart the server.

### "Can't activate virtual environment"
**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### "Database errors"
```bash
# Backup existing database
cp data/neighborhood_bbs.db data/neighborhood_bbs.db.backup

# Reinitialize
python scripts/init-db-local.py
```

### "WebSocket connection failed"
```bash
# Reinstall Flask-SocketIO
pip install --upgrade Flask-SocketIO gevent gevent-websocket
```

---

## Common Tasks

### Stop the Server
```
Press CTRL+C in the terminal
```

### Change Port
Edit `.env`:
```env
PORT=9000
```

### Enable Network Access
Edit `.env`:
```env
HOST=0.0.0.0
```

Or use flag: `./run-local.ps1 -Network`

### View Hardware Logs
```bash
# On Windows
type logs/hardware_events.log

# On Mac/Linux
cat logs/hardware_events.log
```

### Backup Database
```bash
# Windows
Copy-Item data/neighborhood_bbs.db data/backups/backup-$(Get-Date -Format 'yyyy-MM-dd').db

# Mac/Linux
cp data/neighborhood_bbs.db data/backups/backup-$(date +%Y-%m-%d).db
```

### Reset Everything
```bash
# Remove data
rm -rf data/neighborhood_bbs.db logs/*

# Reinitialize
python scripts/init-db-local.py
python scripts/create_admin_user.py
```

---

## Full Documentation

- **Local Setup Details:** [LOCAL_SETUP.md](LOCAL_SETUP.md)
- **Admin Panel API:** [docs/ADMIN_PANEL.md](docs/ADMIN_PANEL.md)
- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (if exists)
- **Troubleshooting:** [LOCAL_SETUP.md#troubleshooting](LOCAL_SETUP.md#troubleshooting)

---

## Performance Tips

### For Better Speed
1. Use SSD storage (instead of USB drive)
2. Close other applications
3. Edit `.env`:
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   LOG_LEVEL=WARNING
   ```

### For More Users
1. Increase workers in `.env` (if supported):
   ```env
   WORKERS=4
   ```
2. Use a modern browser (Chrome, Firefox, Safari)

---

## Need Help?

1. **Check logs:**
   ```bash
   # Terminal output shows errors
   # Also check: logs/hardware_events.log
   ```

2. **Review documentation:**
   - [LOCAL_SETUP.md](LOCAL_SETUP.md) - Detailed setup
   - [docs/ADMIN_PANEL.md](docs/ADMIN_PANEL.md) - Admin features
   - [QUICKSTART.md](QUICKSTART.md) - General guide

3. **Common issues:** See [LOCAL_SETUP.md#troubleshooting](LOCAL_SETUP.md#troubleshooting)

---

**Enjoy running Neighborhood BBS locally! 🏘️**

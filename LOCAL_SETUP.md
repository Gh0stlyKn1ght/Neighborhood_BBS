# Local Setup Guide - Neighborhood BBS

Run Neighborhood BBS locally on Windows, Mac, or Linux without Docker.

## Quick Start (Windows)

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```powershell
   .\scripts\setup-local.ps1
   ```

2. **Launch the app:**
   ```powershell
   .\scripts\run-local.ps1
   ```

3. **Access the BBS:**
   - Open browser to `http://localhost:8080`
   - Default login: `admin` / `admin` (change after first login!)

### Option 2: Manual Setup

#### Step 1: Install Python
- Download [Python 3.10+](https://www.python.org/downloads/)
- **IMPORTANT:** Check "Add Python to PATH" during installation
- Verify: Open PowerShell and run `python --version`

#### Step 2: Create Virtual Environment
```powershell
cd c:\Users\NEO\Desktop\Neighborhood_BBS
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Step 4: Initialize Database
```powershell
python scripts/init-db-local.py
python scripts/create_admin_user.py
# Follow prompts to create first admin account
```

#### Step 5: Run the Application
```powershell
python src/main.py
```

You should see:
```
 * Running on http://127.0.0.1:8080
 * Press CTRL+C to quit
```

#### Step 6: Access in Browser
- Open: `http://localhost:8080`
- Admin panel: `http://localhost:8080/admin/login`

---

## Directory Structure

```
Neighborhood_BBS/
├── src/
│   ├── main.py              # Entry point
│   ├── server.py            # Flask app factory
│   ├── models.py            # Database models
│   ├── routes.py            # Handlers
│   ├── admin/               # Admin panel
│   └── utils/               # Utilities
├── web/
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, assets
│   └── socket_handlers.py   # WebSocket handlers
├── data/                    # Local database (created at first run)
│   └── neighborhood_bbs.db
├── logs/                    # Hardware logs
├── scripts/
│   ├── setup-local.ps1      # Windows setup (automated)
│   ├── run-local.ps1        # Windows launcher
│   ├── init-db-local.py     # Database initialization
│   └── create_admin_user.py # Admin account creation
├── requirements.txt         # Python dependencies
└── .env                     # Local config (auto-created)
```

---

## Configuration

### `.env` File (Auto-Created)

The system creates `.env` automatically on first run with:

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-random-key-here
DATABASE_PATH=data/neighborhood_bbs.db
LOG_PATH=logs/
PORT=8080
HOST=127.0.0.1
```

**To customize:**
1. Edit `.env` in the project root
2. Restart the app

### Key Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `PORT` | 8080 | Server port |
| `HOST` | 127.0.0.1 | Only local (change to 0.0.0.0 for network access) |
| `FLASK_DEBUG` | True | Auto-reload on code changes |
| `LOG_LEVEL` | INFO | Hardware logging level |

---

## Admin Panel

### First Login

1. Navigate to `http://localhost:8080/admin/login`
2. Username: `admin`
3. Password: `admin`
4. **CHANGE THIS PASSWORD IMMEDIATELY** in admin panel

### Features

- **Device Management**: Ban/unban devices by ID, MAC, or IP
- **Network Config**: Set custom settings for your local network
- **Themes**: Create and activate UI themes
- **Chat Logs**: Configure retention (daily deletion)
- **Hardware Logs**: View system events (CPU, memory, network)

---

## Database

### Location
- **Default:** `data/neighborhood_bbs.db`
- **Backup:** Automatically backed up to `data/backups/`

### Initialize Fresh Database
```powershell
python scripts/init-db-local.py
```

### Reset Everything
```powershell
# Backup first!
Copy-Item data/neighborhood_bbs.db data/backups/neighborhood_bbs.db.backup

# Delete the database
Remove-Item data/neighborhood_bbs.db

# Reinitialize
python scripts/init-db-local.py
python scripts/create_admin_user.py
```

---

## Running Tests

### Run All Tests
```powershell
pytest tests/ -v
```

### Run Specific Test
```powershell
pytest tests/test_basic.py::test_function_name -v
```

### Generate Coverage Report
```powershell
pytest --cov=src tests/
```

---

## Development Workflow

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Start Development Server
```powershell
python src/main.py
# Auto-reloads on file changes (FLASK_DEBUG=True)
```

### 3. Make Changes
- Edit files in `src/` and `web/`
- Server auto-reloads (browser refresh may be needed)

### 4. View Logs
```powershell
# Hardware logs
Get-Content logs/hardware_events.log -Tail 20

# Flask debug logs appear in terminal
```

### 5. Commit Changes
```powershell
git add .
git commit -m "feat: describe your change"
git push
```

---

## Troubleshooting

### Issue: "Python not found"
**Solution:** Python isn't in PATH
```powershell
# Reinstall Python with "Add Python to PATH" checked
# Or add manually: https://docs.python.org/3/using/windows.html
```

### Issue: "Virtual environment won't activate"
**Solution:** Execution policy issue
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Issue: "Port 8080 already in use"
**Solution:** Change PORT in `.env`
```env
PORT=8081  # Use a different port
```

Then restart the app.

### Issue: "Can't connect to database"
**Solution:** Check permissions
```powershell
# Ensure data/ directory exists and is writable
mkdir -p data
chmod 755 data
```

### Issue: "Admin login fails"
**Solution:** Recreate admin account
```powershell
python scripts/create_admin_user.py
# Enter username: admin
# Enter password: your-new-password
```

### Issue: WebSocket connection errors
**Solution:** Verify Python-SocketIO installation
```powershell
pip install --upgrade Flask-SocketIO
```

---

## Performance Tips

### 1. Use Release Mode
```env
FLASK_ENV=production
FLASK_DEBUG=False
```

### 2. Increase Worker Threads
Edit `src/main.py`:
```python
socketio.run(app, host='127.0.0.1', port=8080, 
             workers=4,  # Increase from default 1
             worker_class='gevent')
```

### 3. Enable Database Caching
Already enabled by default for local mode.

### 4. Optimize Logging
Reduce log verbosity in `.env`:
```env
LOG_LEVEL=WARNING  # Only warnings and errors
```

---

## Deploy on Raspberry Pi 🍓

Once you've tested locally, deploy to a Raspberry Pi as a permanent server:

### Hardware Options

| Model | Cost | Power | RAM | Recommended |
|-------|------|-------|-----|-------------|
| **Pi 3B+** | $35 | 2.5W | 1GB | ✅ Entry-level |
| **Pi 4** | $55 | 3.5W | 4GB | ⭐ **Best value** |
| **Pi 5** | $80 | 4W | 8GB | 🚀 Latest |

All models work great! Pi 4 is typically the sweet spot.

### Step 1: Set Up Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select: **Raspberry Pi OS Lite (64-bit)**
3. Write to 32GB+ SD card
4. Insert and power on

### Step 2: One-Command Installation

SSH into your Pi:
```bash
ssh pi@raspberrypi.local
# Default password: raspberry
```

Run the automated setup:
```bash
curl https://raw.githubusercontent.com/Gh0stlyKn1ght/Neighborhood_BBS/main/firmware/raspberry-pi/setup.sh | bash
```

The script runs 8 automated steps:
1. ✅ System compatibility check
2. ✅ Update packages (apt-get)
3. ✅ Install dependencies
4. ✅ Clone repository
5. ✅ Create virtual environment
6. ✅ Install Python packages
7. ✅ Initialize database
8. ✅ Create systemd service

Takes about 10-15 minutes on Pi 4.

### Step 3: Start the Service

```bash
# Start
sudo systemctl start neighborhood-bbs

# Check status
sudo systemctl status neighborhood-bbs

# View logs
sudo journalctl -u neighborhood-bbs -f

# Enable auto-start on reboot
sudo systemctl enable neighborhood-bbs
```

### Step 4: Access Your BBS

From any device on your network:
```
http://raspberrypi.local:8080
```

Or use Pi's IP address:
```bash
# Find Pi's IP
hostname -I

# Access
http://192.168.x.x:8080
```

### Configuration

Edit `.env` on the Pi:
```bash
ssh pi@raspberrypi.local
nano ~/Neighborhood_BBS/.env
```

Key settings:
```env
PORT=8080                    # Web server port
FLASK_DEBUG=False           # Production mode
WORKERS=2                   # Auto-tune for Pi
DEBUG=false                 # Disable verbose logging
```

### Advanced Features (Optional)

**Enable HTTPS (Let's Encrypt):**
```bash
sudo certbot --nginx -d yourdomain.com
```

**Set up Nginx reverse proxy:**
See [firmware/raspberry-pi/README.md](firmware/raspberry-pi/README.md#nginx-reverse-proxy-optional)

**Monitor system resources:**
```bash
# CPU/Memory usage
top

# Disk space
df -h

# Temperature (Pi 4/5)
vcgencmd measure_temp
```

### Backup Your Data

```bash
# SSH into Pi and backup database
ssh pi@raspberrypi.local
scp pi@raspberrypi.local:~/Neighborhood_BBS/data/neighborhood_bbs.db ./backup-$(date +%Y-%m-%d).db
```

### Performance Optimization

For multiple users/devices:

```bash
# On Pi: Increase swap memory
sudo dphys-swapfile swapoff
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile swapon

# Monitor
free -h
```

### Useful Commands

```bash
# Restart service
sudo systemctl restart neighborhood-bbs

# Stop service
sudo systemctl stop neighborhood-bbs

# View service logs
sudo journalctl -u neighborhood-bbs -n 100

# Test API health
curl http://localhost:8080/health

# Check network connectivity
hostname -I
netstat -an | grep 8080
```

### Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u neighborhood-bbs -f
# Check for errors in logs
```

**Out of disk space:**
```bash
df -h  # Check usage
sudo apt-get clean  # Clear apt cache
```

**High CPU usage:**
```bash
top  # Identify process
sudo systemctl restart neighborhood-bbs
```

**Port already in use:**
```bash
sudo lsof -i :8080  # See what's using port
# Change PORT in .env and restart
```

**Full documentation:** [firmware/raspberry-pi/README.md](firmware/raspberry-pi/README.md)

---

## Connect WiFi Devices (ESP8266/ESP32) 📡

The local server can host IoT devices like ESP8266 microcontrollers:

### Step 1: Configure Device
Edit [firmware/esp8266/config.py](firmware/esp8266/config.py):
```python
SSID = "Your_WiFi_SSID"                # Your WiFi network
PASSWORD = "Your_WiFi_Password"        # WiFi password
SERVER_HOST = "192.168.1.100"          # Your computer's IP (local network only!)
SERVER_PORT = 8080                     # Same port as server
DEVICE_NAME = "ESP8266_Living_Room"    # Unique device name
```

**Find your computer's IP:**
```powershell
# Windows
ipconfig

# Mac/Linux
ifconfig | grep inet
```

### Step 2: Flash MicroPython Firmware
Connect ESP8266 via USB and run:
```bash
pip install esptool
esptool.py --port COM3 erase_flash
esptool.py --port COM3 write_flash 0 micropython.bin
```

### Step 3: Upload Application
```bash
pip install adafruit-ampy
ampy --port COM3 put firmware/esp8266/main.py
ampy --port COM3 put firmware/esp8266/config.py
```

### Step 4: Device Connects Automatically
The device will:
1. Connect to your WiFi
2. Communicate with your local BBS server
3. Appear in admin panel for monitoring/management
4. Can be banned or configured as needed

### Device Management in Admin Panel
- **Monitor:** View in Hardware Logs
- **Control:** Ban devices by ID/MAC/IP
- **Network:** Configure mesh topology
- **Status:** See real-time connections

**Full documentation:** [firmware/esp8266/README.md](firmware/esp8266/README.md)

---

## Accessing from Other Devices

### Local Network Access

1. **Find your computer's IP:**
   ```powershell
   ipconfig
   # Look for "IPv4 Address" under your network adapter
   # Example: 192.168.1.100
   ```

2. **Update `.env`:**
   ```env
   HOST=0.0.0.0  # Listen on all interfaces
   PORT=8080
   ```

3. **Restart the app**

4. **Connect from other device:**
   - From phone/tablet: `http://192.168.1.100:8080`
   - Note: Only works if on same WiFi network

### Via WireGuard/VPN
For secure remote access, see `docs/VPN_SETUP.md`

---

## Next Steps

1. **Create Admin Account:**
   ```powershell
   python scripts/create_admin_user.py
   ```

2. **Configure Network Settings:**
   - Admin Panel → Network Configuration
   - Set chat retention, themes, etc.

3. **Add Devices:**
   - Start inviting friends to `http://your-ip:8080`
   - Manage bans in admin panel if needed

4. **Monitor Hardware:**
   - Admin Panel → Hardware Logs
   - View CPU, memory, network usage

5. **Backup Regularly:**
   ```powershell
   Copy-Item data/neighborhood_bbs.db data/backups/neighborhood_bbs.db.$(Get-Date -Format 'yyyy-MM-dd')
   ```

---

## Need Help?

- **Documentation:** Read `docs/` folder
- **Issues:** Check GitHub issues
- **API Reference:** See `docs/ADMIN_PANEL.md`
- **Logs:** Check `logs/hardware_events.log`

---

**Happy hosting! 🌍**

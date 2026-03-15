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

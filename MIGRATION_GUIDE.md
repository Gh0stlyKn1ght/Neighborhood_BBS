# Project Reorganization - Migration Guide

## Overview

The Neighborhood BBS project has been reorganized for better structure and maintainability. This guide helps you adapt your workflows to the new directory layout.

**New Structure Summary:**
- `/server/` - All server code (src/, web/, config/, scripts/, tests/)
- `/devices/` - Device-specific code (esp8266/, raspberry-pi/, zima/, docker/)
- `/docs/` - ALL documentation
- Top level - Configuration, setup, and reference files

---

## ⚠️ Important Changes

### Command Changes

#### Before (Old Structure)
```bash
# Running the server
python src/main.py
cd src && python main.py

# Running scripts
python scripts/init_db.py
python scripts/create_admin_user.py

# Testing
python -m pytest tests/
```

#### After (New Structure)
```bash
# Running the server (from project root)
python server/src/main.py

# Or change directory first (RECOMMENDED)
cd server
python src/main.py

# Running scripts (from project root)
python server/scripts/init_db.py
python server/scripts/create_admin_user.py

# Or from server directory
cd server
python scripts/init_db.py

# Testing (from project root)
python -m pytest server/tests/
# Or from server directory
cd server
python -m pytest tests/
```

### Environment Variables

Update your `.env` file:

**OLD:**
```bash
FLASK_APP=src/server.py
```

**NEW:**
```bash
FLASK_APP=server/src/main.py
```

### Docker Deployment

#### Dockerfile Changes

When running Docker from the new structure:

```dockerfile
# OLD path references (❌ won't work)
COPY src/ ./src/
COPY web/ ./web/

# NEW path references (✅ correct)
COPY server/src/ ./src/
COPY server/web/ ./web/
```

#### Docker Compose Changes

The `docker-compose.yml` files have been updated to use the correct build context:

```yaml
# OLD (❌ won't work)
build:
  context: ..
  dockerfile: docker/Dockerfile

# NEW (✅ correct)
build:
  context: ../..
  dockerfile: devices/docker/Dockerfile
```

**How to update your docker-compose calls:**

```bash
# From project root
cd devices/docker
docker-compose -f docker-compose.yml -f docker-compose.linux.yml up -d

# Or explicitly specify files
docker-compose -f devices/docker/docker-compose.yml up -d
```

---

## 📋 Step-by-Step Migration

### 1. Update Your Shell Profile (if applicable)

If you had aliases pointing to old paths:

```bash
# OLD
alias start-bbs="python ~/Neighborhood_BBS/src/main.py"

# NEW
alias start-bbs="cd ~/Neighborhood_BBS && python server/src/main.py"
```

### 2. Update Systemd Service Files

If you're using systemd, update the `ExecStart` path:

```ini
# OLD
ExecStart=/path/to/venv/bin/python src/main.py

# NEW
ExecStart=/path/to/venv/bin/python server/src/main.py
```

Then reload systemd:
```bash
sudo systemctl daemon-reload
sudo systemctl restart neighborhood-bbs
```

### 3. Update Development Workflows

**For Python development:**

```bash
# Install in development mode (now uses correct paths)
pip install -e .

# Run tests
cd server
python -m pytest

# Run with debugger
cd server
python -m pdb src/main.py
```

### 4. Update Docker Workflows

```bash
# Build from project root
cd devices/docker
docker-compose build

# Run with new paths
docker-compose -f docker-compose.yml -f docker-compose.linux.yml up -d
```

### 5. Update CI/CD Pipelines

If you have GitHub Actions or other CI/CD:

```yaml
# OLD
- run: python src/main.py &

# NEW
- run: python server/src/main.py &

# For pytest
- run: python -m pytest server/tests/
```

---

## 🔍 Finding The Right Files

### Server Code
`server/src/` - All Python server code
- `main.py` - Entry point
- `server.py` - Flask app factory
- `models.py` - Database models
- `admin/`, `board/`, `chat/`, `utils/` - Feature modules

### Server Configuration
`server/config/` - Configuration files

### Web Frontend  
`server/web/` - HTML, CSS, JavaScript
- `templates/` - HTML templates
- `static/css/` - Stylesheets
- `static/js/` - JavaScript files
- `static/images/` - Images (including logo.png)

### Server Admin Scripts
`server/scripts/` - Utility scripts
- `init_db.py` - Initialize database
- `create_admin_user.py` - Create admin account
- `list_admin_users.py` - List admins
- `reset_db.py` - Reset database

### Server Tests
`server/tests/` - Test suite

### Device Firmware
`devices/esp8266/src/` - ESP8266 MicroPython code
`devices/raspberry-pi/scripts/` - Raspberry Pi setup
`devices/zima/scripts/` - Zima Board setup

### Docker
`devices/docker/` - Docker configuration files

---

## ✅ Verification Checklist

After migration, verify everything works:

- [ ] `python server/src/main.py` starts without errors
- [ ] Web interface accessible at `http://localhost:8080`
- [ ] Database initializes: `python server/scripts/init_db.py`
- [ ] Admin user creation works: `python server/scripts/create_admin_user.py`
- [ ] Tests pass: `python -m pytest server/tests/`
- [ ] Docker builds: `cd devices/docker && docker-compose build`
- [ ] Systemd service works (if applicable): `sudo systemctl start neighborhood-bbs`

---

## 🆘 Troubleshooting

### Import Errors
If you get `ModuleNotFoundError` when running scripts:

```bash
# Make sure you're running from the right location
cd /path/to/Neighborhood_BBS

# Try running with full path
python server/scripts/init_db.py

# Or change directory first
cd server/scripts
python init_db.py
```

### FLASK_APP Not Found
If Flask can't find the app:

```bash
# Make sure your .env has the correct path
FLASK_APP=server/src/main.py

# Or set it when running
FLASK_APP=server/src/main.py python -m flask run
```

### Docker Build Fails
If Docker can't find files:

```bash
# Make sure docker-compose context is correct
cd devices/docker

# Check that Dockerfile references are updated
# Should see: COPY server/src/ ./src/
cat Dockerfile | grep COPY

# Try building with explicit context
docker build -f Dockerfile -t neighborhood-bbs:latest ../..
```

### Systemd Service Won't Start
If the service fails:

```bash
# Check service status
sudo systemctl status neighborhood-bbs

# View detailed logs
sudo journalctl -u neighborhood-bbs -n 50 -f

# Verify ExecStart path in service file
sudo cat /etc/systemd/system/neighborhood-bbs.service | grep ExecStart
# Should show: ExecStart=/path/venv/bin/python server/src/main.py
```

---

## 📚 Additional Resources

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed structure explanation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide (now updated)
- [DEBIAN_SETUP.md](DEBIAN_SETUP.md) - Debian/Ubuntu setup
- [KALI_SETUP.md](KALI_SETUP.md) - Kali Linux setup
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Docker setup

---

## ❓ FAQ

**Q: Do I need to reinstall?**  
A: No, the code is the same. Just update your command paths and FLASK_APP environment variable.

**Q: Will my existing database work?**  
A: Yes, all data is preserved. The database file location in `/data/` hasn't changed.

**Q: How do I update my Git history?**  
A: This reorganization is committed as a structural change. No need to rewrite history.

**Q: Can I still run from Windows?**  
A: Yes, use `python server/src/main.py` or `python server\src\main.py` on Windows CMD.

**Q: What about virtual environments?**  
A: Virtual environment paths don't change. Just make sure to activate it before running commands.

---

## Summary of Changes

| What | Old Path | New Path |
|------|----------|----------|
| Server entry point | `python src/main.py` | `python server/src/main.py` |
| Init database | `python scripts/init_db.py` | `python server/scripts/init_db.py` |
| Create admin | `python scripts/create_admin_user.py` | `python server/scripts/create_admin_user.py` |
| Business logic | `src/` | `server/src/` |
| Web files | `web/` | `server/web/` |
| Config files | `config/` | `server/config/` |
| Tests | `tests/` | `server/tests/` |
| Utilities | `scripts/` | `server/scripts/` |
| Device firmware | `firmware/` | `devices/esp8266/src/` |
| Docker configs | `docker/` | `devices/docker/` |
| FLASK_APP env | `src/server.py` | `server/src/main.py` |

---

Need help? Check the main [README.md](README.md) or post an issue on GitHub.

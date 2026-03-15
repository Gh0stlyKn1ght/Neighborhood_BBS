# Project Structure

**Neighborhood BBS** follows a clean, modular directory structure to organize code by functionality and platform.

## Root Directory

```
Neighborhood_BBS/
├── server/              # Core BBS server application
├── devices/             # Device-specific implementations
├── docs/                # Documentation
├── .github/             # GitHub configuration
├── data/                # Runtime data (database, logs)
├── venv/                # Python virtual environment
└── [configuration files]
```

---

## 📁 `/server` - Core BBS Server

The main server application built with Flask and Python.

```
server/
├── src/                 # Python source code
│   ├── main.py         # Entry point
│   ├── server.py       # Flask app factory
│   ├── models.py       # Database models
│   ├── admin/          # Admin panel routes
│   ├── board/          # Bulletin board module
│   ├── chat/           # Real-time chat module
│   └── utils/          # Utility functions
│
├── web/                # Web frontend
│   ├── static/         # CSS, JS, assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/     # Include logo.png
│   └── templates/      # HTML templates
│       └── index.html  # Main interface
│
├── config/             # Configuration files
│   └── *.conf          # Config templates
│
├── scripts/            # Utility scripts
│   ├── *.py           # Python scripts (initialization, admin, etc)
│   ├── *.ps1          # PowerShell scripts (Windows)
│   └── *.sh           # Shell scripts (Linux)
│
├── tests/              # Test suite
│   └── test_*.py      # Unit and integration tests
│
└── README.md           # Server-specific documentation
```

**How to run:**
```bash
cd server
python src/main.py
```

---

## 📁 `/devices` - Device-Specific Code

Separate implementations for each supported platform.

### ESP8266 - IoT Edge Devices

```
devices/esp8266/
├── src/                # MicroPython source
│   └── main.py        # ESP8266 main firmware
├── config/            # Configuration templates
│   └── config.json.example
├── libs/              # External libraries and utilities
├── docs/              # ESP8266-specific documentation
│   └── README.md      # Setup and flashing instructions
└── [other assets]
```

**Purpose:** Lightweight implementation for ESP8266 microcontrollers to create edge nodes.

**Deploy with:** MicroPython, esptool.py

---

### Raspberry Pi - ARM Single-Board Computer

```
devices/raspberry-pi/
├── scripts/           # Automation scripts
│   ├── setup.sh      # Initial setup script
│   └── *.sh          # Utility scripts
├── config/           # Configuration templates
│   └── *.conf
├── systemd/          # Systemd service files
│   └── neighborhood-bbs.service
├── docs/             # Raspberry Pi documentation
│   └── README.md     # Setup instructions
└── [other assets]
```

**Purpose:** Production deployment on Raspberry Pi (all models).

**Deploy with:** Docker or native Python

---

### Zima Board - Home Server

```
devices/zima/
├── scripts/          # Zima-specific scripts
│   └── *.sh
├── config/           # Configuration files
│   └── *.conf
├── docs/             # Zima documentation
│   └── README.md     # Zima-specific setup
└── [other assets]
```

**Purpose:** Optimized configuration for Zima Board home servers.

**Deploy with:** Docker or native Python

---

### Docker - Container Deployment

```
devices/docker/
├── Dockerfile                  # Main Docker image
├── Dockerfile.armv7           # ARM 32-bit (RPi 3)
├── Dockerfile.arm64           # ARM 64-bit (RPi 4/5, Zima)
├── docker-compose.yml         # Standard compose config
├── docker-compose.windows.yml # Windows-specific
├── docker-compose.linux.yml   # Linux-specific
└── configs/                   # Docker configurations
    └── [nginx, ssl, etc]
```

**Purpose:** Container definitions for all platforms.

**Deploy with:** Docker & Docker Compose

---

## 📁 `/docs` - Documentation

```
docs/
├── API.md             # REST API reference
├── DEVELOPMENT.md     # Developer guide
├── SETUP.md           # Installation guide
├── HARDWARE.md        # Hardware requirements
└── [other docs]
```

---

## 📝 Top-Level Files

| File | Purpose |
|------|---------|
| `README.md` | Main project overview |
| `KALI_SETUP.md` | Kali Linux setup guide |
| `DEBIAN_SETUP.md` | Debian/Ubuntu setup guide |
| `DOCKER_SETUP.md` | Docker deployment guide |
| `DOCKER_MIGRATION.md` | Migration from local to Docker |
| `SECURITY_AUDIT_FINAL.md` | Security implementation details |
| `PROJECT_OVERVIEW.md` | Project goals and scope |
| `setup.py` | Python package configuration |
| `requirements.txt` | Python dependencies |
| `requirements-dev.txt` | Development dependencies |
| `.env.example` | Environment variable template |

---

## 🔄 Import Paths

After reorganization, imports follow this pattern:

**From within server:**
```python
from src.models import User
from src.chat.routes import chat_bp
from src.admin.auth import admin_required
```

**From within specific device:**
```python
# ESP8266
from main import connect_wifi
from config import SSID
```

---

## 📦 Running Different Targets

### Server Only
```bash
cd server
python src/main.py
```

### With Docker
```bash
cd devices/docker
docker-compose -f docker-compose.yml -f docker-compose.linux.yml up
```

### ESP8266 Firmware
```bash
cd devices/esp8266
# Use esptool.py to flash src/main.py
```

### Raspberry Pi
```bash
cd devices/raspberry-pi
bash scripts/setup.sh
```

---

## 🚀 Development Workflow

1. **Server changes:** Modify files in `/server/src/` and test with `python server/src/main.py`
2. **Device firmware:** Update files in `/devices/{ESP8266|RPi|Zima}/` and deploy via appropriate method
3. **Docker:** Test with `/devices/docker/docker-compose.*.yml`
4. **Documentation:** Update relevant files in `/docs/` and root level

---

## 📂 Data & Logs

- **`/data`** - SQLite database and runtime state
- **`/logs`** - Application and hardware logs
- **`/venv`** - Python virtual environment (development only)

---

## ✅ Structure Checklist

- [x] Server code separated in `/server`
- [x] Device code organized by platform in `/devices`
- [x] Docker configs in `/devices/docker`
- [x] Documentation in `/docs`
- [x] Scripts organized by type
- [x] Configuration templates provided
- [x] Clear separation of concerns

This structure makes it easy to:
- Develop server independently
- Add new device types
- Maintain device-specific code
- Scale deployments
- Onboard new contributors

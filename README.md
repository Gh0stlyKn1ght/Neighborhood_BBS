```
█████╗ ███████╗██╗ █████╗ ███████╗╗ █████╗ ███═██╗███████╗███████╗██╗
██╔═══╝██╔════╝██║██╔══██╗██╔════╝██╔══██║██║ ██║██╔═════╝██╚════╗██║
████╗ █████╗  ██║███████║█████╗  ████████║██║ ██║█████╗  ███████║██║
██║ ██║██╔══╝  ██║██╔══██║██╔══╝  ██╔══██║██║ ██║██╔══╝  ╚════██║╚═╝
███████║███████╗██║██║  ██║███████╗██║  ██║╚█████╔╝███████╗███████║██╗
╚══════╝╚══════╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚════╝ ╚══════╝╚══════╝╚═╝
```

<!-- Badges -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/Gh0stlyKn1ght/Neighborhood_BBS)](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues)
[![GitHub Stars](https://img.shields.io/github/stars/Gh0stlyKn1ght/Neighborhood_BBS?style=social)](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS)
[![Open Source](https://img.shields.io/badge/Open%20Source-❤-brightgreen)](OPEN_SOURCE.md)
[![Security Hardened](https://img.shields.io/badge/Security-Hardened-brightgreen.svg)](FIXES_SUMMARY.md)
[![Tests Passing](https://img.shields.io/badge/Tests-25%2F25-brightgreen.svg)](tests/)

## 📋 Overview

**Neighborhood BBS** is a fully open-source, decentralized community board and real-time chatroom platform designed to run on affordable, low-power hardware like the **Raspberry Pi**, **Zima Board**, and **ESP8266**. Create a local neighborhood network where residents can share information, ask questions, organize events, and build community connections—all while keeping data local and secure.

```
    ┌─────────────────────────────────────┐
    │   🏘️  NEIGHBORHOOD COMMUNICATION  🏘️   │
    │  Connect Your Community Offline     │
    │   All Data Stays Local & Secure     │
    └─────────────────────────────────────┘
```

**Perfect for:**
- 🏘️ **Neighborhoods** - Local community communication
- 🔐 **Security Teams** - Red teamers, pentesters, bug bounty hunters (see [Kali Linux Setup](KALI_SETUP.md))
- 🔬 **Research Groups** - Secure intelligence sharing
- 🤝 **Teams** - Any group needing offline-first communication

**🏘️ For neighborhoods. By the community. By hackers. Forever open source.**

### ✨ Features

- 💬 **Real-time Chat** - Instant messaging for neighborhood discussions
- 📌 **Community Board** - Post notices, announcements, and requests
- 🏘️ **Local Network** - Works on local networks and mesh networks
- ⚡ **Low Power** - Runs efficiently on Raspberry Pi, ESP8266, and Zima Board
- 🔒 **Privacy First** - Keep neighborhood data local and secure
- 📱 **Web Interface** - Clean, responsive design for all devices
- 🌐 **WiFi Connected** - Easy setup and connectivity
- 📜 **100% Open Source** - MIT License, fully transparent

## 🖥️ Retro Cyan CRT Terminal Theme

All platforms share the **same retro aesthetic**:

- **Cyan on Black** - Classic monospace terminal feel (#00FFFF on #000000)
- **CRT Scanlines** - Authentic monitor effect overlay
- **IRC-Style Chat** - User list, channels, message timestamps
- **ASCII Art Headers** - Nostalgic BBS welcome screens
- **Glow Effects** - Cyan text shadows and highlights
- **Real-time Updates** - WebSocket chat with instant delivery

Access from any device: **http://raspberrypi.local:8080** (or your device's IP)

```
╔═══════════════════════════════════════════════════════════╗
║           COMPATIBLE HARDWARE PLATFORMS                  ║
╠════════════════════╦════════════╦════╦══════╦════════════╣
║  Device            ║  Status    ║Cost║Power ║ Setup Time ║
╠════════════════════╬════════════╬════╬══════╬════════════╣
║ Raspberry Pi 4/5   ║ ✅ FULL    ║ $$ ║ 5W  ║  30 min   ║
║ Zima Board         ║ ✅ FULL    ║$$$$ ║ 12W ║  30 min   ║
║ ESP8266            ║ ✅ ACTIVE  ║  $ ║<100mA║ 1-2 hrs  ║
║ ESP32              ║ 🔄 WIP     ║ $$ ║50-100mA║ 1-2 hrs ║
╚════════════════════╩════════════╩════╩══════╩════════════╝
```

### Quick Start by Device

**Raspberry Pi (Easiest! 🎯)**
```bash
curl https://raw.githubusercontent.com/Gh0stlyKn1ght/Neighborhood_BBS/main/firmware/raspberry-pi/setup.sh | bash
```

**Docker (Any Platform)**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

**Linux Server (Zima, Ubuntu, Debian)**
See [docs/SETUP.md](docs/SETUP.md)

**Embedded (ESP8266)**
See [firmware/esp8266/README.md](firmware/esp8266/README.md)

## 🚀 Quick Start

```
   INITIALIZING NEIGHBORHOOD BBS v1.0
   ═══════════════════════════════════
   > Setting up your local community...
   > Checking hardware configuration...
   > Loading database...
   > Starting server...
   > Ready for connections!
```

### Prerequisites

- Python 3.7+
- pip or conda
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# Install dependencies
pip install -r requirements.txt

# Run the server
python src/main.py
```

**Access the app:** Open your browser to `http://localhost:8080`

## 📁 Project Structure

```
Neighborhood_BBS/
├── src/                    # Main application source code
│   ├── main.py            # Entry point
│   ├── server.py          # Server implementation
│   ├── chat/              # Chat module
│   ├── board/             # Community board module
│   └── utils/             # Utility functions
├── firmware/              # Embedded firmware
│   ├── esp8266/           # ESP8266 MicroPython code
│   ├── zima/              # Zima Board specific code
│   └── common/            # Shared firmware utilities
├── web/                   # Web frontend
│   ├── static/            # CSS, JS, images
│   ├── templates/         # HTML templates
│   └── assets/            # Icons and media
├── docs/                  # Documentation
│   ├── SETUP.md          # Setup instructions
│   ├── API.md            # API documentation
│   └── DEVELOPMENT.md    # Developer guide
├── config/               # Configuration files
│   ├── default.conf      # Default configuration
│   └── sample.conf       # Sample configuration
├── .github/              # GitHub templates
│   ├── workflows/        # CI/CD pipelines
│   └── ISSUE_TEMPLATE/   # Issue templates
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
├── LICENSE              # Project license
└── README.md            # This file
```

## 🔧 Configuration

Create a `config.conf` file in the root directory:

```ini
[SERVER]
host = 0.0.0.0
port = 8080
debug = false

[NETWORK]
max_connections = 100
message_timeout = 300

[DATABASE]
type = sqlite
path = data/neighborhood.db
```

## 💻 Development

### Setting up the Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Start development server
python src/main.py --debug
```

### Building Firmware

#### ESP8266
```bash
cd firmware/esp8266
# Follow ESP8266 build instructions in firmware/esp8266/README.md
```

#### Zima Board
```bash
cd firmware/zima
# Follow Zima Board build instructions in firmware/zima/README.md
```

## 📚 Documentation

### Platform-Specific Setup Guides

- **[Kali Linux Setup](KALI_SETUP.md)** 🛡️ - For security professionals, pentesters, and hackers
  - Red team collaboration setup
  - Integration with Nmap, Metasploit, SQLMap
  - Secure networking for isolated teams
  - Perfect for bug bounty hunters and security researchers

- **[Debian/Ubuntu Setup](DEBIAN_SETUP.md)** 🐧 - For Debian, Ubuntu, and derivatives
  - Native Python installation
  - systemd service configuration
  - Docker Compose deployment
  - Nginx reverse proxy setup
  - SSL/TLS with Let's Encrypt
  - Performance optimization

- **[Docker Setup](DOCKER_SETUP.md)** 🐳 - Cross-platform Docker deployment
  - Windows (Docker Desktop)
  - Linux/Raspberry Pi
  - Security best practices
  - Multi-instance deployment

### General Documentation

- [Setup Guide](docs/SETUP.md) - Detailed installation and configuration
- [API Reference](docs/API.md) - Complete API documentation
- [Developer Guide](docs/DEVELOPMENT.md) - Contributing and development workflow
- [Hardware Guide](docs/HARDWARE.md) - Hardware-specific instructions
- [Security Audit](SECURITY_AUDIT_FINAL.md) - Security implementation details

## 🤝 Contributing

We welcome contributions! Please follow these steps:

```
╔════════════════════════════════════════╗
║      CONTRIBUTING TO NEIGHBORHOOD BBS  ║
╠════════════════════════════════════════╣
║ 1. Fork the repository                 ║
║ 2. Create feature branch               ║
║ 3. Make your improvements              ║
║ 4. Run tests (pytest)                  ║
║ 5. Submit pull request                 ║
║                                        ║
║ All contributions appreciated! 🙏      ║
╚════════════════════════════════════════╝
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎪 Acknowledgments

- Inspired by classic BBS systems and modern community platforms
- Built with ❤️ for neighborhoods everywhere
- Thanks to the open-source community

## 📞 Support & Contact

- 📧 Email: support@neighborhood-bbs.local
- 💬 Chat: Join our community discussions
- 🐛 Issues: Report bugs on [GitHub Issues](https://github.com/yourusername/Neighborhood_BBS/issues)

---

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║  🏘️  NEIGHBORHOOD BBS - Community Connection Network  🏘️  ║
║                                                           ║
║      Where Neighbors Connect. Data Stays Local.          ║
║           Forever Open Source. Always Free.              ║
║                                                           ║
║              ■ ■ ■ ■ ■ ONLINE ■ ■ ■ ■ ■               ║
║                                                           ║
║           Made with 💙 for local communities            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

<div align="center">

**Neighborhood BBS** - *Where neighbors connect*

</div>

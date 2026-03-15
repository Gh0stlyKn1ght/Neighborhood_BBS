

<!-- Badges -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/Gh0stlyKn1ght/Neighborhood_BBS)](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues)
[![GitHub Stars](https://img.shields.io/github/stars/Gh0stlyKn1ght/Neighborhood_BBS?style=social)](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS)
[![Open Source](https://img.shields.io/badge/Open%20Source-❤-brightgreen)](OPEN_SOURCE.md)

## 📋 Overview

**Neighborhood BBS** is a fully open-source, decentralized community board and real-time chatroom platform designed to run on affordable, low-power hardware like the **Raspberry Pi**, **Zima Board**, and **ESP8266**. Create a local neighborhood network where residents can share information, ask questions, organize events, and build community connections—all while keeping data local and secure.

**🏘️ For neighborhoods. By the community. Forever open source.**

### ✨ Features

- 💬 **Real-time Chat** - Instant messaging for neighborhood discussions
- 📌 **Community Board** - Post notices, announcements, and requests
- 🏘️ **Local Network** - Works on local networks and mesh networks
- ⚡ **Low Power** - Runs efficiently on Raspberry Pi, ESP8266, and Zima Board
- 🔒 **Privacy First** - Keep neighborhood data local and secure
- 📱 **Web Interface** - Clean, responsive design for all devices
- 🌐 **WiFi Connected** - Easy setup and connectivity
- 📜 **100% Open Source** - MIT License, fully transparent

## 🎯 Supported Hardware

| Device | Status | Cost | Power | Setup |
|--------|--------|------|-------|-------|
| **Raspberry Pi 4/5** | ✅ Full Support (NEW!) | $$ | 5W | 30 min |
| **Zima Board** | ✅ Fully Supported | $$$$ | 12W | 30 min |
| **ESP8266** | ✅ Supported | $ | <100mA | 1-2 hrs |
| **ESP32** | 🔄 In Progress | $$ | 50-100mA | 1-2 hrs |

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

- [Setup Guide](docs/SETUP.md) - Detailed installation and configuration
- [API Reference](docs/API.md) - Complete API documentation
- [Developer Guide](docs/DEVELOPMENT.md) - Contributing and development workflow
- [Hardware Guide](docs/HARDWARE.md) - Hardware-specific instructions

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

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

<div align="center">

### 🏘️ Building Stronger Communities, One Network At A Time 🏘️

**Neighborhood BBS** - *Where neighbors connect*

Made with 💙 for local communities

</div>

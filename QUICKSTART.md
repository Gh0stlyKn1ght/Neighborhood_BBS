# Neighborhood BBS - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### For Developers

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# 2. Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python src/main.py

# 5. Open browser
# Visit: http://localhost:8080
```

### For Zima Board Users

```bash
# 1. SSH into your Zima Board
ssh user@zima-board-ip

# 2. Clone repository
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS

# 3. Set up and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Start the service
mkdir -p data logs
sudo systemctl start neighborhood-bbs

# 5. Access the board
# Visit: http://zima-board-ip:8080
```

### For ESP8266 Users

```bash
# 1. Install esptool
pip install esptool

# 2. Flash MicroPython firmware (see firmware/esp8266/README.md)
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 write_flash 0 micropython.bin

# 3. Upload application (using ampy or WebREPL)
ampy --port /dev/ttyUSB0 put firmware/esp8266/main.py

# 4. Device connects automatically to WiFi and server
```

## 📁 Project Structure at a Glance

```
Neighborhood_BBS/
├── src/           ← Main server code
├── firmware/      ← ESP8266 & Zima firmware
├── web/           ← Frontend code
├── docs/          ← Documentation
└── tests/         ← Test suite
```

## 🎯 Common Commands

### Development

```bash
# Run tests
pytest tests/

# Check code quality
black src/
flake8 src/
mypy src/

# Run in debug mode
FLASK_ENV=development python src/main.py
```

### Database

```bash
# Initialize database
python scripts/init_db.py

# Reset database (warning: deletes data!)
python scripts/reset_db.py
```

### Git

```bash
# Create feature branch
git checkout -b feature/my-awesome-feature

# Make changes and commit
git add .
git commit -m "Add awesome feature"

# Push to GitHub
git push origin feature/my-awesome-feature
```

## 📚 Documentation

- **Setup Guide:** [docs/SETUP.md](docs/SETUP.md)
- **API Reference:** [docs/API.md](docs/API.md)
- **Development Guide:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Hardware Guide:** [docs/HARDWARE.md](docs/HARDWARE.md)
- **Zima Board:** [firmware/zima/README.md](firmware/zima/README.md)
- **ESP8266:** [firmware/esp8266/README.md](firmware/esp8266/README.md)

## 🌐 Access Points

Once the server is running:

- **Web Interface:** http://localhost:8080
- **API Base:** http://localhost:8080/api
- **Chat API:** http://localhost:8080/api/chat
- **Board API:** http://localhost:8080/api/board
- **Health Check:** http://localhost:8080/health

## ❓ Troubleshooting

### Port Already in Use
```bash
# Change port
export PORT=8081  # Linux/Mac
set PORT=8081     # Windows
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### WiFi Connection Issues (ESP8266)
- Check WiFi SSID and password in `config.py`
- Restart the device
- Move closer to WiFi router

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📞 Need Help?

- 📖 Read the documentation
- 🐛 Open an issue on GitHub
- 💬 Check existing discussions
- 🔍 Search closed issues

---

**Happy coding!** 🏘️ Let's build stronger communities together!

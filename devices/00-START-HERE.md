# Neighborhood BBS - Complete Setup Guide

**Choose your platform, download the setup files, and follow the guide. 15 min to 1 hour depending on choice.**

## 🚀 Quick Start - Choose Your Path

| Platform | Time | Cost | Best For | Download |
|----------|------|------|----------|----------|
| **Arduino ESP8266** | 15 min | $8 | Testing now | [→ Arduino Setup](./downloads/arduino-esp8266/SETUP_GUIDE.md) |
| **ZimaBoard** ⭐ | 30 min | $120+ | Production | [→ ZimaBoard Setup](./downloads/zimaboard/SETUP_GUIDE.md) |
| **Raspberry Pi 3-5** | 45 min | $35-70 | SBC users | [→ Raspberry Pi Setup](./downloads/raspberry-pi/SETUP_GUIDE.md) |
| **Debian Linux** | 1 hour | Free | Custom server | [→ Debian Setup](./downloads/debian/SETUP_GUIDE.md) |
| **Windows** | 1.5 hr | Free | Dev only | [→ Windows Setup](./downloads/windows/SETUP_GUIDE.md) |
| **Orange Pi 5** | 45 min | $30-50 | Alternative SBC | [→ Orange Pi Setup](./downloads/orange-pi-5/SETUP_GUIDE.md) |

---

## 📦 Downloads

All downloadable files and setup scripts are organized by platform in the `downloads/` folder:

- **[downloads/arduino-esp8266/](./downloads/arduino-esp8266/)** - Arduino IDE + .ino sketch
- **[downloads/zimaboard/](./downloads/zimaboard/)** - ZimaBoard Flask deployment
- **[downloads/raspberry-pi/](./downloads/raspberry-pi/)** - Raspberry Pi 3+, 4, 5
- **[downloads/debian/](./downloads/debian/)** - Bare metal Debian/Ubuntu
- **[downloads/windows/](./downloads/windows/)** - Windows (dev/testing)
- **[downloads/orange-pi-5/](./downloads/orange-pi-5/)** - Orange Pi 5 alternative

---

## 🎯 Which One Should I Choose?

### "I want to test this in 15 minutes"
→ **Arduino ESP8266** - Just upload a sketch  
See: [Arduino Setup Guide](./downloads/arduino-esp8266/SETUP_GUIDE.md)

### "I want persistent messages and admin control"
→ **ZimaBoard** (Recommended) - Professional setup  
See: [ZimaBoard Setup Guide](./downloads/zimaboard/SETUP_GUIDE.md)

### "I already have a Raspberry Pi"
→ **Raspberry Pi 3+/4/5** - Leverage existing hardware  
See: [Raspberry Pi Setup Guide](./downloads/raspberry-pi/SETUP_GUIDE.md)

### "I have a custom Linux server"
→ **Debian** - Bare metal installation  
See: [Debian Setup Guide](./downloads/debian/SETUP_GUIDE.md)

### "I only have Windows"
→ **Windows (Docker/Dev)** - Testing only, not production  
See: [Windows Setup Guide](./downloads/windows/SETUP_GUIDE.md)

### "I want to use Orange Pi 5"
→ **Orange Pi 5** - H6 ARM alternative  
See: [Orange Pi 5 Setup Guide](./downloads/orange-pi-5/SETUP_GUIDE.md)

---

## 📋 Each Setup Includes

Each platform folder contains:

```
downloads/[platform]/
├── SETUP_GUIDE.md        ← Start here (step-by-step instructions)
├── requirements.txt      ← What to install
├── troubleshooting.md    ← Common issues + fixes
├── deploy.[sh|ps1]       ← Automated setup script (if applicable)
└── config/              ← Default configuration files
```

---

## 🔧 Implementation Details by Platform

### Arduino ESP8266 Microcontroller
- **File**: `neighborhood_bbs_chat.ino` (550 lines)
- **Libraries**: WebSockets by Markus Sattler (v2.3.6+)
- **Range**: 50-80m (extend to 150m+ with external antenna)
- **Persistence**: None (messages gone on reboot)
- **Admin**: Re-flash to update

### ZimaBoard x86 ⭐ RECOMMENDED
- **File**: Flask Python application
- **Database**: SQLite (persistent)
- **Persistence**: ✓ All messages saved to disk
- **Admin**: Web dashboard at `/admin`
- **Automation**: One-command deployment (`bash setup.sh`)

### Raspberry Pi 3+, 4, 5 (ARM)
- **File**: Flask Python application
- **Database**: SQLite (persistent)
- **Persistence**: ✓ All messages saved to disk
- **Performance**: Slower than ZimaBoard (ARM vs x86), sufficient for small neighborhoods
- **Power**: ~5W (low power)

### Debian / Ubuntu Linux (x86/ARM)
- **File**: Flask Python application
- **Database**: SQLite (persistent)
- **Persistence**: ✓ All messages saved to disk
- **Flexibility**: Full control over everything
- **Setup**: Manual, requires Linux knowledge

### Windows (Dev Only)
- **File**: Flask Python application
- **Database**: SQLite (persistent)
- **Persistence**: ✓ While running
- **Admin**: Web dashboard
- **Note**: For development/testing only, not production

### Orange Pi 5 (H6 ARM)
- **File**: Flask Python application
- **Database**: SQLite (persistent)
- **Persistence**: ✓ All messages saved to disk
- **Performance**: Similar to Raspberry Pi 4
- **Note**: Requires Armbian or Ubuntu for Orange Pi

---

## 📁 Folder Structure

```
Neighborhood_BBS/
├── devices/
│   ├── README.md                          ← You are here
│   ├── 00-START-HERE.md                   ← Files summary
│   │
│   ├── downloads/                         ← DOWNLOAD THESE FILES
│   │   ├── arduino-esp8266/
│   │   │   ├── SETUP_GUIDE.md
│   │   │   ├── requirements.txt
│   │   │   ├── troubleshooting.md
│   │   │   └── neighborhood_bbs_chat.ino  ← Arduino sketch
│   │   │
│   │   ├── zimaboard/
│   │   │   ├── SETUP_GUIDE.md
│   │   │   ├── setup.sh
│   │   │   ├── requirements.txt
│   │   │   └── troubleshooting.md
│   │   │
│   │   ├── raspberry-pi/
│   │   │   ├── SETUP_GUIDE.md
│   │   │   ├── setup.sh
│   │   │   ├── requirements.txt
│   │   │   └── troubleshooting.md
│   │   │
│   │   ├── debian/
│   │   │   ├── SETUP_GUIDE.md
│   │   │   ├── setup.sh
│   │   │   ├── requirements.txt
│   │   │   └── troubleshooting.md
│   │   │
│   │   ├── windows/
│   │   │   ├── SETUP_GUIDE.md
│   │   │   ├── setup.ps1
│   │   │   ├── requirements.txt
│   │   │   └── troubleshooting.md
│   │   │
│   │   └── orange-pi-5/
│   │       ├── SETUP_GUIDE.md
│   │       ├── setup.sh
│   │       ├── requirements.txt
│   │       └── troubleshooting.md
│   │
│   ├── esp8266/                           ← Implementation details
│   │   ├── README.md
│   │   ├── docs/
│   │   ├── libs/
│   │   ├── config/
│   │   └── src/
│   │
│   ├── zima/                              ← Implementation details
│   │   ├── README.md
│   │   ├── bbs/
│   │   ├── config/
│   │   ├── scripts/
│   │   └── docs/
│   │
│   ├── raspberry-pi/                      ← Implementation details
│   │   ├── README.md
│   │   ├── scripts/
│   │   └── systemd/
│   │
│   └── docker/                            ← Implementation details
│       ├── Dockerfile
│       └── docker-compose.yml
│
└── docs/
    ├── LOCAL_SETUP.md
    ├── SECURITY.md
    ├── QUICKSTART.md
    └── etc...
```

---

## 🎓 Getting Help

### Something not working?
1. Check your platform's **troubleshooting.md** file
2. Read the **SETUP_GUIDE.md** again (missed a step?)
3. Check main project [SECURITY.md](../../SECURITY.md)

### Need more info?
- [LOCAL_SETUP.md](../../LOCAL_SETUP.md) - Development environment
- [API_TESTING.md](../../API_TESTING.md) - REST API reference
- [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md) - How the project is organized
- [ROADMAP.md](../../ROADMAP.md) - Future features

---

## 📞 Support

**Questions?** Start at your platform's setup guide in the `downloads/` folder.

**Think you found a bug?** Check troubleshooting.md first, then open an issue on GitHub.

---

## ✅ Verification Checklist

After setup, verify your BBS is working:

- [ ] Can connect to WiFi SSID `NEIGHBORHOOD_BBS`
- [ ] Landing page loads at `http://192.168.4.1`
- [ ] Can see bulletins
- [ ] Can enter chat room
- [ ] Can type messages
- [ ] Messages appear instant (WebSocket working)
- [ ] Can refresh page, messages still there (database working)
- [ ] Admin login works (for non-Arduino setups)

---

**Choose your platform above and follow the setup guide. Takes 15 minutes to 1 hour. You've got this.** 🚀

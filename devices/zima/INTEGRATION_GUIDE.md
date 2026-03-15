# Neighborhood BBS - Complete Integration Guide

This guide walks through the complete Neighborhood BBS system: from WiFi edge nodes (ESP8266) to central coordination (ZimaBoard), with all components integrated into the reorganized project structure.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NEIGHBORHOOD BBS                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         ZimaBoard (Central Hub)                    │  │
│  │  ├─ Flask Web Server (bulletins, admin, chat)      │  │
│  │  ├─ SQLite Database (persistent messages)          │  │
│  │  ├─ Nginx Reverse Proxy (port 80, IP masking)      │  │
│  │  └─ WiFi AP (via USB adapter or onboard)           │  │
│  └────────────────────────────────────────────────────┘  │
│                           ▲                               │
│                    50-200m range                          │
│                           │                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │   ESP8266 Edge Nodes (Neighborhood WiFi)           │  │
│  │  ├─ WebSocket Chat (realtime messages)             │  │
│  │  ├─ Captive Portal (auto-pop on phone)             │  │
│  │  ├─ Arduino IDE + WebSockets library               │  │
│  │  └─ IRC-style BBS aesthetic (green on black)       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  Broadcast from any device:                              │
│  Neighbors connect → WiFi auto-pops portal →             │
│  See bulletins → Chat live → Leave → repeat              │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Implementation Paths

### Path 1: ESP8266 Standalone (Simplest)

**Use case**: Desk decoration, neighborhood reach, no server sync

```
ESP8266 NodeMCU
├─ Self-contained BBS with chat
├─ Messages wipe on reboot (feature, not bug)
├─ Range: 50-80m (enough for cul-de-sac)
└─ Setup time: 15 minutes
```

**Files**:
- [devices/esp8266/](../esp8266/) - Arduino sketches
- [devices/esp8266/docs/ARDUINO_SETUP.md](../esp8266/docs/ARDUINO_SETUP.md) - complete Arduino IDE guide

**Tech**:
- Arduino IDE + official ESP8266 board package
- WebSockets by Markus Sattler (v2.3.6+)
- Built-in: ESP8266WiFi, ESP8266WebServer, DNSServer

### Path 2: ZimaBoard Hosted (Recommended)

**Use case**: Persistent messages, admin control, scale to multiple pods, KITT integration

```
ZimaBoard
├─ Central BBS server
├─ Messages survive reboots (SQLite)
├─ Admin panel (create/delete bulletins, moderate chat)
├─ Multiple USB WiFi adapters = multiple APs
└─ Setup time: 30 minutes
```

**Files**:
- [devices/zima/bbs/](../zima/bbs/) - Flask + WebSocket server
- [devices/zima/bbs/README.md](../zima/bbs/README.md) - deployment instructions

**Tech**:
- Python 3 + Flask + flask-sock
- SQLite (persistent bulletins + messages)
- Nginx reverse proxy (IP masking, SSL-ready)
- Systemd service (auto-restart)

### Path 3: Hybrid (Best)

**Use case**: Multiple ESP8266 pods broadcasting one ZimaBoard BBS

```
ZimaBoard (Central)
    ▲
    │ MQTT bridge
    │
[ESP8266] [ESP8266] [ESP8266] ← all show same ZimaBoard SSID
    └─────────────────┬────────────────┘
                      │
              Neighbors connect
              to nearest pod →
              all join same BBS
```

## Project Structure

```
Neighborhood_BBS/
├── server/                          # Core BBS server
│   ├── src/
│   │   ├── main.py                 # Flask dev server
│   │   ├── models/                 # Data models
│   │   └── routes/                 # API endpoints
│   ├── web/                        # Frontend (React/Vue - future)
│   ├── config/                     # Environment configs
│   ├── tests/                      # Unit tests
│   └── requirements.txt            # Python dependencies
│
├── devices/                        # Hardware implementations
│   ├── esp8266/                   # Microcontroller BBS
│   │   ├── main.py               # MicroPython HTTP polling
│   │   ├── docs/
│   │   │   └── README.md         # MicroPython setup
│   │   ├── libs/
│   │   │   ├── ARDUINO_SETUP.md  # Arduino IDE guide ← USE THIS
│   │   │   ├── WEBSOCKET_SETUP.md
│   │   │   └── neighborhood_bbs_chat_filter.ino  # Full sketch
│   │   └── config.json.example
│   │
│   ├── raspberry-pi/              # Single-board computer
│   │   ├── scripts/
│   │   │   └── setup.sh
│   │   └── systemd/
│   │       └── bbs.service
│   │
│   ├── zima/                       # ZimaBoard deployment ← RECOMMENDED
│   │   ├── bbs/                   # Flask BBS application
│   │   │   ├── app.py            # Main Flask + WebSocket server
│   │   │   ├── start.sh          # Automated deployment script
│   │   │   ├── bbs.service       # Systemd unit
│   │   │   ├── nginx.conf        # Reverse proxy config
│   │   │   ├── requirements.txt  # Python dependencies
│   │   │   ├── static/
│   │   │   │   └── logo.svg     # Green phosphor ghost logo
│   │   │   └── templates/
│   │   │       ├── base.html    # CRT theme (scanlines, green text)
│   │   │       ├── index.html   # Landing page
│   │   │       ├── chat.html    # Live chat interface
│   │   │       ├── admin_login.html
│   │   │       └── admin.html   # Admin control panel
│   │   ├── config/              # WiFi + BBS settings (future)
│   │   ├── scripts/             # Deployment helpers
│   │   └── docs/
│   │       └── ZIMABOARD_BBS.md
│   │
│   └── docker/                    # Container deployment
│       ├── Dockerfile
│       └── docker-compose.yml
│
└── docs/
    ├── LOCAL_SETUP.md            # Development environment
    ├── KALI_SETUP.md             # Penetration testing rig
    ├── DEBIAN_SETUP.md           # Bare metal Linux
    ├── DOCKER_SETUP.md           # Container quick-start
    ├── QUICKSTART.md             # First-time users
    ├── API_TESTING.md            # REST API reference
    └── SECURITY.md               # Security considerations
```

## Quick Start Comparison

| Task | Path 1 (ESP8266) | Path 2 (ZimaBoard) | Path 3 (Hybrid) |
|------|-----|---------|---------|
| Get BBS online now | 15 min | 30 min | 1 hour |
| Messages survive reboot | ✗ | ✓ | ✓ |
| Range (meters) | 50-80 | 30-500+ | 50-80 per pod |
| Admin updates | Re-flash | Web panel | Web panel |
| Cost | $8 | $120 + $15 adapter | $128 + USB adapters |
| Difficulty | Easy | Medium | Hard |

## Deployment Workflows

### Workflow 1: Deploy ESP8266 BBS

```bash
# 1. Get Arduino IDE + ESP8266 board package
#    See: devices/esp8266/libs/ARDUINO_SETUP.md

# 2. Install WebSockets library (v2.3.6)
#    Arduino IDE → Manage Libraries → WebSockets by Markus Sattler

# 3. Upload sketch
#    File → Open → devices/esp8266/libs/neighborhood_bbs_chat_filter.ino
#    Tools → Board → NodeMCU 1.0
#    Tools → Upload Speed → 115200
#    Sketch → Upload

# 4. Open Serial Monitor → confirm "BBS ONLINE: NEIGHBORHOOD_BBS"

# 5. Connect phone → auto-pops page
#    Or manually → http://192.168.4.1
```

### Workflow 2: Deploy ZimaBoard BBS (Automated)

```bash
# 1. SSH to ZimaBoard
ssh root@zimaboard.local

# 2. Copy project
scp -r Neighborhood_BBS/devices/zima/bbs root@zimaboard.local:/opt/zima_bbs

# 3. Run deployment script
ssh root@zimaboard.local
cd /opt/zima_bbs
bash start.sh

# Script does:
# - Install Python3, pip, nginx
# - Install Flask + flask-sock
# - Create SQLite database
# - Setup systemd service
# - Configure nginx on port 80
# - Start BBS

# 4. Access
#    From WiFi: http://192.168.4.1
#    From network: http://<zimaboard-ip>
#    Admin: http://<zimaboard-ip>/admin/login (gh0stly / gh0stly)
```

### Workflow 3: Deploy Hybrid (ESP8266 + ZimaBoard)

```bash
# 1. Modify ESP8266 sketch to POST messages to ZimaBoard
cd devices/esp8266/libs/

# Edit neighborhood_bbs_chat_filter.ino line 15:
// #define MQTT_BRIDGE "http://192.168.1.100/api/send"

# 2. Deploy ZimaBoard first (see Workflow 2)

# 3. Modify ESP8266 sketch WiFi to connect to ZimaBoard AP
const char* SSID = "NEIGHBORHOOD_BBS";

# 4. Upload to multiple ESP8266 boards

# 5. Each pod broadcasts BBS, but all messages go to ZimaBoard database
```

## WiFi Management

### Create AP with ZimaBoard USB Adapter

```bash
# Install hostapd + dnsmasq
apt-get install -y hostapd dnsmasq

# Configure /etc/hostapd/hostapd.conf
interface=wlan0
ssid=NEIGHBORHOOD_BBS
hw_mode=g
channel=6
wmm_enabled=0

# Configure /etc/dnsmasq.conf
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.50,255.255.255.0,24h
address=/#/192.168.4.1   # ← Captive portal redirect

# Start
systemctl start hostapd
systemctl start dnsmasq
```

### Extend Range

**Default range**: 50m (suburban)

**Extend with external antenna**:
```bash
# Node MCU with antenna connector (~$8 extra)
# + Rubber duck antenna ($3)
# = 150-200m range

# Or ESP32 (slightly faster, same code):
# Core 3.1.2 + WebSockets 2.3.6
```

## Integration with KITT

(ZimaBoard path only)

```bash
# KITT publishes vehicle alerts via MQTT
mosquitto_pub -h localhost -t 'vehicle/alerts' -m 'TEMP_HIGH'

# ZimaBoard subscribes, posts to BBS
python3 kitt_bridge.py

# Neighbors see in chat:
# KITT: ⚠ TEMPERATURE WARNING - 105°F DETECTED
```

## Development

### Local Testing (ZimaBoard BBS)

```bash
cd devices/zima/bbs

# Install dependencies
pip3 install -r requirements.txt

# Run Flask dev server
python3 app.py
# Listens on http://localhost:5000

# Or with auto-reload
FLASK_ENV=development FLASK_APP=app.py flask run -h 0.0.0.0
```

### Testing ESP8266 Sketch Locally

```bash
# Optional: compile without uploading
Arduino IDE → Sketch → Verify

# Check Serial Monitor for debug output
Tools → Serial Monitor (115200 baud)

# Watch chat messages:
# [WS] Client 1 connected
# [MSG] BLOCK_MOM: come over for coffee
# Broadcast complete
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| ESP8266 CompileError: WebSocketsServer.h not found | Library not installed or wrong location | Arduino IDE → Sketch → Include Library → Manage Libraries → search "WebSockets" → install Markus Sattler 2.3.6+ |
| ZimaBoard blank page | Nginx not proxying to Flask | nginx -t → systemctl restart nginx → curl http://127.0.0.1:5000 |
| BBS won't start on boot | Systemd service not enabled | systemctl enable bbs → systemctl start bbs |
| Chat disconnects after 10 min | WebSocket idle timeout | Already handled with reconnect, check browser console |
| Phone doesn't auto-pop captive portal | OS captive detection varies | Manually open http://192.168.4.1 |

## Security Checklist

- [ ] Change admin password from `gh0stly`
- [ ] Enable HTTPS on nginx (certbot + Let's Encrypt)
- [ ] Disable default accounts on ZimaBoard
- [ ] Hide BBS from public WiFi scanning (use WPA2 password if needed)
- [ ] Regular backups of SQLite database
- [ ] Monitor logs for abuse: `journalctl -u bbs -f`
- [ ] Rate limiting enabled (5 msg/10 sec per session)
- [ ] IP addresses stripped at nginx layer ✓

## Next Steps

1. **Choose your path**:
   - Quick test? → ESP8266 (15 min)
   - Permanent setup? → ZimaBoard (30 min)
   - Scale to multiple pods? → Hybrid (1 hour)

2. **Deploy**:
   - ESP8266: [devices/esp8266/libs/ARDUINO_SETUP.md](../esp8266/libs/ARDUINO_SETUP.md)
   - ZimaBoard: [devices/zima/bbs/README.md](../zima/bbs/README.md)

3. **Customize**:
   - Edit bulletins in admin panel
   - Modify logo.svg for your neighborhood
   - Change SSID name in WiFi settings

4. **Extend**:
   - Add MQTT bridge for KITT integration
   - Deploy multiple USB WiFi adapters for mesh coverage
   - Add OLED display to show live messages

## FAQ

**Q: Can neighbors hack my network?**  
A: This BBS is local WiFi only. No internet = no remote attacks. Network itself is secured by WPA2 password (or open if you want). Messages are not encrypted (local AP only).

**Q: How many messages before database gets too big?**  
A: ZimaBoard SQLite handles millions. Default: keep last 50 messages (auto-purge old ones). Bulletins unlimited.

**Q: Can I run this on Raspberry Pi instead?**  
A: Yes, but slower AP performance. ZimaBoard x86 CPU is much better for serving many clients.

**Q: What about ESP8266 with larger antenna?**  
A: External antenna roughly doubles range. See devices/esp8266/ for details.

**Q: Can I add password to the BBS?**  
A: Not currently. It's "open community" by design. For private: Set AP password in hostapd.conf or use MAC filtering.

## Support

- [LOCAL_SETUP.md](../LOCAL_SETUP.md) - development
- [API_TESTING.md](../API_TESTING.md) - REST endpoints
- [SECURITY.md](../SECURITY.md) - security guidelines
- [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md) - repo organization

---

**Version**: 2.0 (ZimaBoard Flask + ESP8266 Arduino)  
**Last updated**: March 2026  
**License**: See root LICENSE file

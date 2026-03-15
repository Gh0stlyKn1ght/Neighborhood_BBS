# Neighborhood BBS - Device Implementations

This folder contains platform-specific deployments of the Neighborhood BBS system. Choose your deployment path based on your needs, budget, and technical comfort level.

## Quick Reference

| Device | Purpose | Range | Cost | Setup Time | Persistence | Admin Control |
|--------|---------|-------|------|-----------|-------------|---------------|
| **ESP8266** | Standalone WiFi BBS | 50-80m | $5-$15 | 15 min | Volatile | Re-flash |
| **ZimaBoard** | Central hub + persistent BBS | 30-50m (can extend to 200m+ with antenna) | $120-$160 | 30 min | SQLite DB ✓ | Web admin ✓ |
| **Raspberry Pi** | Single-board computer | 30-50m | $35-$70 | 45 min | SQLite DB ✓ | Web admin ✓ |
| **Docker** | Containerized (dev/test) | N/A | Free | 10 min | Volatile | CLI |

## Device Folders

### [`esp8266/`](esp8266/) - Microcontroller BBS

**What it does**: Standalone WiFi captive portal with live chat and bulletins. Think "BBS in your pocket."

**Best for**: 
- Testing the concept quickly
- Desktop decoration
- Covers one cul-de-sac or neighborhood block
- No server dependencies

**Hardware needed**:
- NodeMCU ESP8266 v3 (~$8)
- USB cable for programming
- Optional: external antenna + U.FL connector (adds $5, extends range to 150-200m)

**Setup**:
```bash
cd esp8266/
# Quick library reference:
cat ARDUINO_REQUIREMENTS.txt

# Detailed setup instructions:
# 1. See esp8266/libs/ARDUINO_SETUP.md for complete steps
# 2. Install Arduino IDE
# 3. Add ESP8266 board package
# 4. Install required libraries:
#    - WebSockets by Markus Sattler (v2.4.0+)
#    - ArduinoJson by Benoit Blanchon (v6.19.0+)
# 5. Upload neighborhood_bbs_chat.ino
# 6. Done! Connect phone to "NEIGHBORHOOD_BBS" SSID
```

**Key files**:
- `ARDUINO_REQUIREMENTS.txt` - Library checklist (read first!)
- `libs/neighborhood_bbs_chat.ino` - Complete Arduino sketch with chat + bulletins
- `libs/ARDUINO_SETUP.md` - Step-by-step Arduino IDE guide ← DETAILED SETUP
- `libs/WEBSOCKET_SETUP.md` - Optional MicroPython WebSocket implementation
- `docs/README.md` - Firmware and deployment details

**Features**:
- IRC-style chat interface (green text on black, scanlines)
- Ring buffer (last 20 messages)
- Profanity filter (two-layer: client + server)
- Tab switching: Bulletins ↔ Chat Room
- User nick system with duplicate checking
- Zero persistence (messages gone on reboot — feature, not bug)

**Tech stack**:
- Arduino IDE
- ESP8266 board package (official)
- WebSockets by Markus Sattler (v2.3.6+)
- Built-in: WiFi, DNS, WebServer

---

### [`zima/`](zima/) - ZimaBoard Central Hub ⭐ RECOMMENDED

**What it does**: Persistent BBS server with admin panel, SQLite database, and multiple WiFi AP support via USB adapters.

**Best for**:
- Long-term deployment
- Persistent bulletins and chat history
- Admin control (create, edit, delete without re-flashing)
- Scaling to multiple WiFi pods
- Integration with other services (MQTT, REST APIs)

**Hardware needed**:
- ZimaBoard x86 (Ryzen 5, 8GB RAM) ~ $120
- USB 3.0 WiFi adapter (optional, for better range/performance) ~ $15-$40
  - Recommended: Alfa AWUS036ACM (MT7612U, mainline kernel support)
- Ethernet (included on ZimaBoard)

**Setup**:
```bash
# Automated deployment (30 seconds):
scp -r zima/bbs root@zimaboard:/opt/zima_bbs
ssh root@zimaboard
cd /opt/zima_bbs && bash start.sh

# Done! BBS runs on boot via systemd service
```

**Key files**:
- `bbs/app.py` - Flask + WebSocket server
- `bbs/README.md` - Complete deployment guide ← START HERE
- `bbs/start.sh` - Automated setup script
- `bbs/nginx.conf` - Reverse proxy (port 80)
- `bbs/templates/` - HTML templates (IRC aesthetic)

**Features**:
- Persistent SQLite database
- Admin panel: http://192.168.4.1/admin
  - Create/delete/edit bulletins
  - View message history
  - Clear chat
  - Change password
- WebSocket live chat
- Rate limiting (5 msg/10 sec per session)
- Nginx reverse proxy with IP masking
- Systemd service (auto-restart on crash/reboot)

**Tech stack**:
- Python 3 + Flask + flask-sock
- SQLite (persistent storage)
- Nginx (reverse proxy)
- Systemd (service management)

---

### [`raspberry-pi/`](raspberry-pi/) - Single-Board Computer

**What it does**: Full BBS server on a Raspberry Pi. Like ZimaBoard but lower performance hardware.

**Best for**:
- If you already own a Pi
- Educational deployment
- Lower power consumption (vs ZimaBoard)

**Hardware needed**:
- Raspberry Pi 3B+ or 4B ~ $35-$70
- SD card (32GB)
- USB WiFi adapter (~$15) for better AP mode

**Setup**:
```bash
# See scripts/setup.sh
bash raspberry-pi/scripts/setup.sh
```

**Tradeoffs vs ZimaBoard**:
- ✓ Lower initial cost
- ✓ Lower power (5W vs Zima's 15W)
- ✗ Slower CPU (ARM vs x86 Ryzen)
- ✗ Limited RAM (1-8GB vs Zima's 8GB standard)
- ✗ Onboard WiFi weaker for AP mode

---

### [`docker/`](docker/) - Container Deployment

**What it does**: Containerized BBS for development, testing, or cloud deployment.

**Best for**:
- Quick testing without installing on bare metal
- CI/CD pipelines
- Cloud deployment (AWS, Azure, DigitalOcean)
- Development environment

**Setup**:
```bash
docker-compose -f docker/docker-compose.yml up
# BBS available at http://localhost:80
```

**Tech**:
- Docker + docker-compose
- Python 3 container
- Nginx sidecar
- Persistent volume for SQLite

---

## Comparison: Which Should You Deploy?

### Scenario 1: "I want to test this NOW"
→ **ESP8266** (15 minutes, $8, one USB cable)

### Scenario 2: "I want persistent messages and admin control"
→ **ZimaBoard** (30 minutes, $120 + setup, future-proof)

### Scenario 3: "I want multiple WiFi pods in the neighborhood"
→ **ZimaBoard + USB WiFi adapters** (1 hour, $200+)
- One central ZimaBoard (BBS server)
- Multiple USB adapters (one per AP-enabled device)
- ESP8266 pods as "dumb" displays if desired

### Scenario 4: "I'm just playing around / containerized testing"
→ **Docker** (5 minutes, any OS)

---

## Unified System (Hybrid Deployment)

You can run **both** ESP8266 and ZimaBoard:

```
┌─ ZimaBoard (central database, admin panel, persistent)
│
├─ USB WiFi Adapter A: broadcasts "NEIGHBORHOOD_BBS"
├─ USB WiFi Adapter B: broadcasts "NEIGHBORHOOD_BBS" (different channel)
│
└─ Multiple ESP8266 pods (optional):
   ├─ Modified to POST chat to ZimaBoard API
   ├─ Can show local bulletins on small display
   └─ Or just serve link to full ZimaBoard BBS
```

All neighborhood WiFi devices see same SSID → all connect to same ZimaBoard → centralized message history.

---

## WiFi Configuration

### ESP8266 (Built-in)
```cpp
const char* SSID = "NEIGHBORHOOD_BBS";
// Creates personal AP, range ~50-80m

// To extend: external antenna ~150-200m
WiFi.setOutputPower(20.5);  // max TX
```

### ZimaBoard (hostapd + dnsmasq)
```bash
# /etc/hostapd/hostapd.conf
interface=wlan0
ssid=NEIGHBORHOOD_BBS
hw_mode=g
channel=6
max_num_sta=64  # concurrent clients

# /etc/dnsmasq.conf
dhcp-range=192.168.4.2,192.168.4.50,255.255.255.0
address=/#/192.168.4.1  # ← Captive portal redirect
```

### Multiple Adapters on ZimaBoard
```bash
# First adapter (onboard)
hostapd /etc/hostapd/hostapd0.conf

# Second adapter (USB)
hostapd /etc/hostapd/hostapd1.conf  # same or different SSID

# dnsmasq serves all
```

---

## Maintenance

### ESP8266
- No scheduled maintenance (volatile)
- Messages disappear on reboot
- To update: re-flash via Arduino IDE

### ZimaBoard
- Automatic: systemd restarts on crash
- Manual: `systemctl restart bbs`
- Monitor: `journalctl -u bbs -f`
- Backup: copy `/opt/zima_bbs/bbs.db` regularly
- Update Python packages: `pip3 install --upgrade -r requirements.txt`

### Monitoring
```bash
# Service status
systemctl status bbs

# Live logs
journalctl -u bbs -f

# Check port
lsof -i :80

# Test connectivity
curl http://192.168.4.1
```

---

## Security Notes

### All Deployments
- Local WiFi only (no internet)
- Captive portal = auto-redirect (users can't bypass)
- Messages visible to all connected devices (by design)
- No authentication for chat (fake nicks are fine)

### ZimaBoard Specifics
- Admin credentials required for control panel
- Default: `sysop` / `gh0stly` ← **CHANGE THIS**
- Password hashed (SHA-256)
- Sessions tracked (not IP-based)
- Rate limiting prevents spam

### Best Practices
1. Change admin password immediately
2. Disable SSH if not needed (`systemctl disable ssh`)
3. Use WPA2 on WiFi if you want to restrict access
4. Monitor logs regularly
5. Backup database weekly

---

## Integration Examples

### MQTT Bridge (ZimaBoard + Home Automation)
```python
# Publish to MQTT, subscribe in BBS app
import paho.mqtt.client as mqtt

mqtt_client.publish('neighborhood/bbs', json.dumps({
    'handle': 'SYSTEM',
    'message': 'Trash day reminder'
}))
```

### Rest API for External Services
```bash
# KITT alerts to BBS
curl -X POST http://192.168.4.1/api/send \
  -H "Content-Type: application/json" \
  -d '{"handle":"KITT","text":"⚠ High temperature alert"}'
```

### Mirror to OLED Display
```python
# Query BBS API, display latest bulletin on small screen
import requests
bulletins = requests.get('http://192.168.4.1/api/bulletins').json()
display.show(bulletins[0]['text'])
```

---

## Troubleshooting

### WiFi not broadcasting
```bash
# ESP8266: check Serial Monitor for startup messages
# ZimaBoard: check hostapd
systemctl status hostapd
journalctl -u hostapd -n 20

# Restart
systemctl restart hostapd
```

### BBS not responding
```bash
# Check Flask
curl http://127.0.0.1:5000

# Check nginx
curl http://127.0.0.1:80

# Restart all
systemctl restart bbs nginx
```

### Database errors
```bash
# Check disk space
df -h /opt

# Verify database integrity
sqlite3 /opt/zima_bbs/bbs.db ".check"

# Rebuild if needed
sqlite3 /opt/zima_bbs/bbs.db ".recover" > recovered.sql
```

---

## Further Reading

- [Local setup (development)](../LOCAL_SETUP.md)
- [Security guidelines](../SECURITY.md)
- [API testing](../API_TESTING.md)
- [Project structure](../PROJECT_STRUCTURE.md)
- [ZimaBoard Integration Guide](zima/INTEGRATION_GUIDE.md)

---

**Questions?** Check docs/ folder or [ROADMAP.md](../ROADMAP.md) for future features.

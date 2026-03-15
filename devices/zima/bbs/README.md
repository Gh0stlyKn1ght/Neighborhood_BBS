# Neighborhood BBS - ZimaBoard Flask Implementation

Local WiFi captive portal with persistent messages, live WebSocket chat, and admin dashboard.

## Features

- **Captive Portal**: Auto-detect on phone when connecting to WiFi
- **Persistent Bulletins**: Survive reboots, managed via admin panel
- **Live Chat**: WebSocket-based real-time messaging with nick system
- **Admin Panel**: Create/delete bulletins, manage messages, change password
- **Rate Limiting**: 5 messages per 10 seconds per session
- **Security**: 
  - Password hashing (SHA-256)
  - Session-based admin auth
  - IP stripping (nginx proxy)
  - XSS-safe message handling

## Hardware

- **ZimaBoard**: x86 single-board server
- **USB WiFi Adapter** (optional): For higher range
  - Recommended: Alfa AWUS036ACM (MT7612U, 200-500m range)
  - Stock onboard WiFi: 30-50m typical

## Installation

### Quick Deploy (Automated)

```bash
# Copy to ZimaBoard
scp -r zima/bbs root@<zimaboard-ip>:/opt/zima_bbs

# Run setup
ssh root@<zimaboard-ip>
cd /opt/zima_bbs
bash start.sh
```

This will:
- Install Python3, pip, nginx
- Install Flask + flask-sock dependencies
- Initialize SQLite database
- Setup systemd service (auto-restart on reboot)
- Configure nginx as reverse proxy
- Start the BBS

### Manual Setup

```bash
# SSH to ZimaBoard
ssh root@zimaboard

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip nginx

# Install Python packages
cd /opt/zima_bbs
pip3 install -r requirements.txt --break-system-packages

# Create database
python3 app.py &
sleep 2
kill %1

# Setup service
cp bbs.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bbs
systemctl start bbs

# Configure nginx
cp nginx.conf /etc/nginx/sites-available/bbs
ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
systemctl restart nginx
```

## Access

**From any device connected to WiFi `NEIGHBORHOOD_BBS`:**
- http://192.168.4.1 - landing page
- http://192.168.4.1/admin/login - admin panel (default: sysop / gh0stly)

**From network:**
- http://<zimaboard-ip>

## Admin Panel

Login: http://192.168.4.1/admin/login

Default credentials:
- Username: `sysop`
- Password: `gh0stly`

**CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN**

Features:
- Create/delete bulletins
- View message history
- Clear chat messages
- Change admin password

## Configuration

### WiFi SSID

In `/opt/zima_bbs/config/wifi.conf`:
```
SSID=NEIGHBORHOOD_BBS
PASSWORD=  # leave blank for open AP
CHANNEL=6  # 1-13 depending on region
```

(Currently hardcoded in hostapd setup - see `/etc/hostapd/hostapd.conf`)

### Message History

Default: keeps last 50 messages in database (persistent)
- Older messages deleted automatically to prevent database bloat
- Admin can clear chat with one button

### Rate Limiting

- 5 messages per 10 seconds per session
- Returns 429 Too Many Requests if exceeded
- Resets per window

## Database

SQLite at `/opt/zima_bbs/bbs.db`

**Tables:**
- `bulletins` - persistent message board
- `messages` - chat history
- `admin` - login credentials (password hashed)
- `rate_limits` - session tracking

## API Endpoints

### Public

```bash
# Get bulletins
curl http://192.168.4.1/api/bulletins

# Get chat history (default 50 messages)
curl http://192.168.4.1/api/messages/history?limit=100

# Send message via REST (rate limited)
curl -X POST http://192.168.4.1/api/send \
  -H "Content-Type: application/json" \
  -d '{"handle":"KITT","text":"Temperature warning detected"}'
```

### WebSocket

Connect to `ws://192.168.4.1/ws`

**Message types:**
- `{"type":"nick_set","nick":"YOUR_NICK"}` - set display name
- `{"type":"msg","text":"Hello neighbors"}` - send message
- Server responds with history, confirmations, broadcasts

## Deployment Examples

### Option 1: Systemd Service (Recommended)

Runs at boot, auto-restart on crash:
```bash
systemctl status bbs
systemctl restart bbs
journalctl -u bbs -f  # live logs
```

### Option 2: Manual Python

```bash
cd /opt/zima_bbs
python3 app.py
# Listens on 0.0.0.0:5000
# nginx proxies port 80 → 5000
```

### Option 3: With Gunicorn (Production)

```bash
pip3 install gunicorn
gunicorn --worker-class gevent --workers 4 app:app
```

## Security Notes

1. **Default Password**: Change immediately on first login
   ```bash
   curl -X POST http://192.168.4.1/admin/password/change \
     -d "old_password=gh0stly&new_password=YourNewPassword"
   ```

2. **IP Masking**: All client IPs stripped at nginx layer
   - Flask logs never see real IPs
   - Rate limiting by session, not IP

3. **XSS Prevention**: Messages sanitized
   - `<script>` tags stripped  
   - `javascript:` URLs blocked
   - Raw text stored, HTML-escaped on render

4. **HTTPS** (optional): Add SSL cert to nginx
   ```bash
   # Example with Let's Encrypt
   apt-get install -y certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

## Troubleshooting

### BBS won't start

```bash
# Check logs
journalctl -u bbs -n 50

# Verify database
sqlite3 /opt/zima_bbs/bbs.db ".tables"

# Check port 5000
lsof -i :5000

# Restart
systemctl restart bbs
```

### Nginx shows blank page

```bash
# Test config
nginx -t

# Check proxy
curl http://127.0.0.1:5000

# Restart
systemctl restart nginx
```

### WebSocket connection drops

- BBS keeps last 50 messages max (replay on reconnect)
- 10-minute idle timeout (configurable)
- Reconnect logic built into frontend

### Too many simultaneous users

- Default: 50 concurrent connections per adapter
- Increase with: `WiFi.softAP(SSID, password, channel, false, 64)` (ESP8266)
- On ZimaBoard+Linux: can handle 200+ with proper AP setup

## Level-Up Options

### Tier 2: MQTT Bridge to KITT

ZimaBoard posts BBS chat as MQTT events:
```bash
pip3 install paho-mqtt
# KITT subscribes, can post system alerts back
```

### Tier 3: Persistent Message Search

Add full-text search in admin panel:
```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(handle, text);
```

### Tier 4: Multiple APs

Run BBS on multiple ZimaBoards with USB adapters for mesh coverage.

## File Structure

```
zima/bbs/
├── app.py                 # Flask + WebSocket server
├── start.sh              # Deployment script
├── bbs.service          # Systemd unit
├── nginx.conf           # Reverse proxy config
├── requirements.txt     # Python dependencies
├── static/
│   └── logo.svg        # Green phosphor BBS logo
├── templates/
│   ├── base.html       # Base template (CRT scanlines, green text)
│   ├── index.html      # Landing page
│   ├── admin_login.html # Admin login
│   └── admin.html      # Admin panel
└── config/             # (planned) WiFi + BBS settings
```

## License

Same as main Neighborhood_BBS project (see root LICENSE)

## Support

See main project docs:
- [LOCAL_SETUP.md](../../LOCAL_SETUP.md) - development
- [SECURITY.md](../../SECURITY.md) - security guidelines
- [ROADMAP.md](../../ROADMAP.md) - future plans

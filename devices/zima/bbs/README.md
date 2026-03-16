# Neighborhood BBS - ZimaBoard Flask Implementation

Local WiFi bulletin board system with persistent messages, live WebSocket chat, and admin dashboard.

**Choose your deployment path:**
- 🚀 **Quick start?** → [CasaOS (2 minutes)](#casaos-one-click)
- 🔧 **Want control?** → [Native Debian (5 minutes)](#native-debian)
- 🐳 **Prefer Docker?** → [Docker Compose (10 minutes)](#docker)

---

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
- **Multi-platform**: Debian, Ubuntu, Docker, CasaOS
- **Persistent Data**: SQLite database survives restarts

---

## Hardware Requirements

### ZimaBoard (x86)
- Recommended: Intel or AMD x86 processor
- RAM: 2GB+ (4GB recommended)
- Storage: 10GB+ free space
- Network: Ethernet + optional USB WiFi adapter

### USB WiFi Adapter (Optional)
For better range (200-500m):
- **Recommended**: Alfa AWUS036ACM (MT7612U)
- **Budget**: TP-Link Archer T2U
- **Stock**: ZimaBoard onboard WiFi (30-50m range)

---

## CasaOS (One-Click)

**⏱️ ~2 minutes | 🎯 Easiest for everyone**

If you have CasaOS installed:

1. Open CasaOS: `http://<zimaboard-ip>`
2. **AppStore** → Search "Neighborhood BBS"
3. Click **Install**
4. Wait ~30 seconds
5. Access at: `http://<zimaboard-ip>:5000`

**Default credentials:**
- Username: `sysop`
- Password: `gh0stly`

**⚠️ CHANGE THIS PASSWORD IMMEDIATELY!**

See [CASAOS_INTEGRATION.md](CASAOS_INTEGRATION.md) for detailed setup & submission to AppStore.

---

## Native Debian

**⏱️ ~5 minutes | 🎯 Full control, lightweight**

### Automated Setup

```bash
# SSH to ZimaBoard
ssh root@zimaboard.local

# Clone & install
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS/devices/zima/bbs
bash start.sh
```

Done! Access at: `http://<zimaboard-ip>:8080`

### Manual Setup

```bash
# Install dependencies
apt-get update
apt-get install -y python3 python3-pip nginx

# Install Python packages
pip3 install -r requirements.txt --break-system-packages

# Initialize database
python3 -c "from app import init_db; init_db()"

# Setup systemd service (auto-restart)
sudo cp bbs.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bbs
sudo systemctl start bbs

# Configure nginx
sudo cp nginx.conf /etc/nginx/sites-available/bbs
sudo ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
sudo systemctl restart nginx
```

### Verify

```bash
# Check service is running
systemctl status bbs

# View logs
journalctl -u bbs -f

# Test health endpoint
curl http://localhost:5000/health
```

### Access

- **Web Interface**: `http://<zimaboard-ip>:8080`
- **Admin Panel**: `http://<zimaboard-ip>:8080/admin`
  - Username: `sysop`
  - Password: `gh0stly`

### Management

```bash
# View logs in real-time
journalctl -u bbs -f

# Restart BBS
systemctl restart bbs

# Stop BBS
systemctl stop bbs

# Start BBS
systemctl start bbs
```

---

## Docker

**⏱️ ~10 minutes | 🎯 Professional, scalable**

### Quick Start with Docker Compose

```bash
# Clone repository
git clone https://github.com/Gh0stlyKn1ght/Neighborhood_BBS.git
cd Neighborhood_BBS/devices/zima/bbs

# Start with Docker Compose
docker-compose up -d

# Verify
docker-compose logs -f neighborhood-bbs
```

Access at: `http://<zimaboard-ip>:5000`

### Building Your Own Image

```bash
docker build -t neighborhood-bbs:latest .

docker run -d \
  --name neighborhood-bbs \
  -p 5000:5000 \
  -v bbs_data:/app/data \
  -e ADMIN_PASSWORD=your_password \
  neighborhood-bbs:latest
```

### Management

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose stop

# Start
docker-compose start

# Update & restart
docker-compose pull
docker-compose up -d
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for advanced Docker setup.

---

## Access the BBS

### From Any Device on WiFi

1. **Connect to WiFi**: `NEIGHBORHOOD_BBS`
2. **Open browser**: Should auto-redirect
3. **Or manually**: `http://192.168.x.x:5000`

### Admin Panel

- URL: `/admin`
- Username: `sysop`
- Password: `gh0stly` (CHANGE THIS!)

Functions:
- Create/edit bulletins
- View/clear messages
- Change admin password
- View chat statistics

---

## API Reference

### REST Endpoints

```bash
# Get bulletins (public)
curl http://localhost:5000/api/bulletins

# Get message history (public)
curl http://localhost:5000/api/messages/history?limit=50

# Send message (REST - for KITT, mobile apps)
curl -X POST http://localhost:5000/api/send \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "YOUR_NAME",
    "text": "Hello from API"
  }'

# Health check (monitoring)
curl http://localhost:5000/health
```

### WebSocket

Connect to `/ws` for real-time messaging:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.messages); // Chat history on connect
};

// Set your nick
ws.send(JSON.stringify({
  type: 'nick_set',
  nick: 'YOUR_NICKNAME'
}));

// Send message
ws.send(JSON.stringify({
  type: 'msg',
  text: 'Hello everyone!'
}));
```

---

## Configuration

### Environment Variables

```bash
# Admin password
export ADMIN_PASSWORD=your_secure_password

# Production mode (no debug output)
export FLASK_ENV=production

# Port (default 5000)
export LISTEN_PORT=5000
```

### Admin Settings (via Web UI)

After login to `/admin`:
1. Change admin password
2. Edit welcome bulletins
3. Configure message retention
4. View activity logs

### SQLite Database

- **Location**: `bbs.db`
- **Tables**: bulletins, messages, admin, rate_limits
- **Retention**: Messages persist unless admin clears

---

## Persistence & Backup

### Data Location

- **Native Debian**: `/path/to/bbs.db`
- **Docker**: `/app/data/bbs.db` (mounted volume)

### Backing Up

```bash
# Native Debian
cp bbs.db bbs_backup_$(date +%Y%m%d).db

# Docker
docker-compose exec neighborhood-bbs \
  cp /app/data/bbs.db /app/data/bbs_backup.db

# Or via Docker volume
docker run --rm -v bbs_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/bbs_data.tar.gz -C /data .
```

### Restoring

```bash
# Native Debian
cp bbs_backup.db bbs.db
systemctl restart bbs

# Docker
docker-compose stop
docker run --rm -v bbs_data:/data -v /backup:/backup \
  alpine tar xzf /backup/bbs_data.tar.gz -C /data
docker-compose start
```

---

## Troubleshooting

### Service won't start (Native Debian)

```bash
# Check logs
journalctl -u bbs -n 50

# Port already in use?
sudo lsof -i :5000

# Permission error?
chmod 755 /path/to/bbs
chmod 644 /path/to/bbs.db
```

### Can't access web UI

```bash
# Verify service running
curl http://localhost:5000/health

# Check nginx (if using)
ps aux | grep nginx

# Firewall?
sudo ufw allow 5000/tcp
```

### Database corrupted

```bash
# Backup corrupt DB
mv bbs.db bbs.db.corrupted

# Reinitialize
python3 -c "from app import init_db; init_db()"

# Restart
systemctl restart bbs
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for more solutions.

---

## Deployment Paths Comparison

| Aspect | CasaOS | Native Debian | Docker |
|--------|--------|---|---|
| **Ease** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐ Easy |
| **Setup time** | 2 min | 5 min | 10 min |
| **RAM usage** | ~200MB | ~50MB | ~200MB |
| **Updates** | Auto in UI | Manual git pull | Docker pull |
| **Control** | Limited to UI | Full SSH | Full Docker |
| **Best for** | End users | Developers | Teams/Scale |
| **Scaling** | Via CasaOS | Multiple instances | Docker Compose |

---

## Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - All deployment methods in detail
- **[CASAOS_INTEGRATION.md](CASAOS_INTEGRATION.md)** - CasaOS setup & AppStore submission
- **[Dockerfile](Dockerfile)** - Container spec
- **[docker-compose.yml](docker-compose.yml)** - Docker Compose config
- **[casaos.yml](casaos.yml)** - CasaOS manifest

---

## Development

### Project Structure

```
zima/bbs/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── bbs.service              # Systemd service file
├── nginx.conf               # Nginx configuration
├── start.sh                 # Automated setup script
├── Dockerfile               # Docker container spec
├── docker-compose.yml       # Docker Compose config
├── casaos.yml              # CasaOS manifest
├── config/                  # Configuration files
├── templates/               # HTML templates
│   ├── index.html          # Landing page
│   ├── chat.html           # Chat interface
│   └── admin.html          # Admin panel
├── static/                  # CSS, JavaScript
│   ├── style.css
│   ├── chat.js
│   └── admin.js
├── README.md               # This file
├── DEPLOYMENT_GUIDE.md     # Deployment instructions
└── CASAOS_INTEGRATION.md   # CasaOS integration
```

### Running Locally

```bash
# Install Python packages
pip3 install -r requirements.txt

# Initialize database
python3 -c "from app import init_db; init_db()"

# Run Flask development server
python3 app.py

# Access at: http://localhost:5000
```

---

## Support

- 📚 **Documentation**: [https://github.com/Gh0stlyKn1ght/Neighborhood_BBS](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS)
- 🐛 **Issues**: [https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues)
- 💬 **Discussions**: [https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/discussions](https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/discussions)

---

**Last Updated**: March 2026  
**Version**: 1.0.0  
**Status**: Production Ready

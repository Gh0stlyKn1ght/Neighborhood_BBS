# ZimaBoard BBS - Deployment Checklist

Quick reference for deploying Neighborhood BBS on ZimaBoard.

## Pre-Deployment

- [ ] ZimaBoard with Debian/Ubuntu Linux
- [ ] Network connectivity (ethernet), SSH access
- [ ] USB WiFi adapter (optional, for extended range)
- [ ] 30 minutes free time
- [ ] Project repository cloned or copied

## Automated Deployment (Recommended)

```bash
# 1. Copy BBS to ZimaBoard
scp -r Neighborhood_BBS/devices/zima/bbs root@<zimaboard-ip>:/opt/zima_bbs

# 2. SSH to ZimaBoard
ssh root@<zimaboard-ip>

# 3. Run setup (handles everything)
cd /opt/zima_bbs
chmod +x start.sh
sudo bash start.sh

# 4. Verify
curl http://127.0.0.1

# 5. Access from phone/laptop
#    WiFi SSID: NEIGHBORHOOD_BBS
#    URL: http://192.168.4.1
#    Admin: http://192.168.4.1/admin/login
```

**Deployment checklist**:
- [ ] start.sh executed successfully
- [ ] No errors during package installation
- [ ] systemd service enabled
- [ ] Nginx running on port 80
- [ ] Flask BBS running on port 5000

## Manual Deployment (If automated fails)

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip nginx hostapd dnsmasq

# 2. Install Python packages
cd /opt/zima_bbs
pip3 install -r requirements.txt --break-system-packages

# 3. Initialize database
python3 app.py &
sleep 3
kill %1

# 4. Setup systemd
sudo cp bbs.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bbs

# 5. Configure nginx
sudo cp nginx.conf /etc/nginx/sites-available/bbs
sudo ln -s /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 6. Configure WiFi AP
# See: WIFI_SETUP.md (or configure via ZimaBoard web UI)

# 7. Start BBS
sudo systemctl start bbs
sudo systemctl status bbs
```

## Post-Deployment

### Security (DO THIS IMMEDIATELY)

- [ ] Access admin panel: http://192.168.4.1/admin/login
- [ ] Login with default: `sysop` / `gh0stly`
- [ ] Change admin password:
  - [ ] Click "Change Admin Password"
  - [ ] Enter old: `gh0stly`
  - [ ] Enter new: `YourSecurePassword`
- [ ] Verify no default credentials remain

### Verification

- [ ] Landing page loads: http://192.168.4.1
- [ ] Bulletins display
- [ ] Chat room accessible: [ENTER CHAT ROOM] button works
- [ ] Admin panel restricted: requires password
- [ ] WebSocket chat functional

**Test**:
```bash
# From command line
curl http://192.168.4.1/api/bulletins   # Should show JSON

# From phone on WiFi
# Auto-pop should show landing page, click [ENTER CHAT ROOM]
# Type message → should appear instantly
```

### WiFi Configuration (if needed)

**Using ZimaBoard web UI** (if available):
- [ ] AP name: `NEIGHBORHOOD_BBS`
- [ ] Channel: 6 or 1 (check what's crowded in your area)
- [ ] Security: WPA2 (optional if you want password)
- [ ] DHCP range: 192.168.4.0/24

**Or manual**:
```bash
# Check current adapter
ip link show

# If using USB adapter (e.g., wlan0):
sudo vi /etc/hostapd/hostapd.conf
# interface=wlan0
# ssid=NEIGHBORHOOD_BBS
# hw_mode=g
# channel=6
# wmm_enabled=0
# max_num_sta=64

sudo systemctl restart hostapd dnsmasq
```

## Going Live

- [ ] Service auto-starts: `systemctl is-enabled bbs` (should show "enabled")
- [ ] Reboot test: `sudo reboot` → check it comes back up in 2 minutes
- [ ] Remote access: test from different locations/devices
- [ ] Long-term: monitor disk usage (`df -h`), database size (`du -h /opt/zima_bbs/bbs.db`)

## Monitoring & Maintenance

### Daily Checks
```bash
# Service running?
systemctl status bbs

# Recent errors?
journalctl -u bbs -n 50

# WiFi AP broadcasting?
iw wlan0 info | grep SSID
```

### Admin Tasks
- [ ] Review chat logs weekly: http://192.168.4.1/admin/messages
- [ ] Update bulletins as needed
- [ ] Clear chat if spammed: Admin → [CLEAR ALL MESSAGES]
- [ ] Monitor logs: `journalctl -u bbs -f` (live tail)

### Backups
```bash
# Weekly backup of database
sudo cp /opt/zima_bbs/bbs.db ~/bbs_backup_$(date +%Y%m%d).db

# Or automated (add to crontab):
# 0 2 * * 0 cp /opt/zima_bbs/bbs.db /backup/bbs_$(date +\%Y\%m\%d).db
```

## Troubleshooting

### WiFi not showing up
```bash
systemctl status hostapd
journalctl -u hostapd -n 20
# If failed: check interface name, channel interference, IP conflicts
```

### BBS not loading
```bash
# Check Flask
curl http://127.0.0.1:5000

# Check Nginx
curl http://127.0.0.1:80

# Check logs
journalctl -u bbs -n 50
journalctl -u nginx -n 50
```

### Database locked / SQLite errors
```bash
# Restart service
sudo systemctl restart bbs

# If persistent: check disk space
df -h /opt

# Or rebuild:
cd /opt/zima_bbs
rm bbs.db  # WARNING: deletes all messages
python3 app.py &
sleep 2
kill %1
sudo systemctl restart bbs
```

### Can't change admin password
```bash
# Direct SQL method:
sqlite3 /opt/zima_bbs/bbs.db
# Inside sqlite3 prompt:
# SELECT * FROM admin;
# UPDATE admin SET password='<new_hash>' WHERE id=1;
# .exit

# To generate hash:
python3 -c "import hashlib; print(hashlib.sha256(b'YourPassword').hexdigest())"
```

### Performance issues (slow chat)
```bash
# Check memory
free -h

# Check CPU
top -b -n 1 | head -20

# Check connections
netstat -an | grep 5000

# If many WebSocket connections, restart:
sudo systemctl restart bbs
```

## Optional Customizations

### Change SSID / WiFi Name
```bash
sudo vi /etc/hostapd/hostapd.conf
# Change: ssid=NEIGHBORHOOD_BBS
sudo systemctl restart hostapd dnsmasq
```

### Add Password to WiFi
```bash
# In /etc/hostapd/hostapd.conf:
# wpa=2
# wpa_passphrase=YourPassword123
sudo systemctl restart hostapd dnsmasq
```

### Use External Antenna
```bash
# USB WiFi adapters with external antenna
# Plug in, verify with:
iw wlan0 info

# Range extends to ~200-300m
# Might need additional USB hub if power-limited
```

### HTTPS (SSL/TLS)
```bash
# Install Let's Encrypt
sudo apt-get install -y certbot python3-certbot-nginx

# Get cert (requires domain or self-signed)
sudo certbot --nginx -d yourdomain.com

# Nginx auto-configures HTTPS
sudo systemctl restart nginx

# Now use: https://192.168.4.1 (certificate warning expected for local)
```

### Send Messages from External API
```bash
# From KITT or other service:
curl -X POST http://192.168.4.1/api/send \
  -H "Content-Type: application/json" \
  -d '{"handle":"SYSTEM","text":"Test message"}'

# Rate limited: 5 per 10 seconds per session
```

## Uninstall / Factory Reset

```bash
# Stop service
sudo systemctl stop bbs
sudo systemctl disable bbs

# Remove files
sudo rm -rf /opt/zima_bbs
sudo rm /etc/systemd/system/bbs.service

# Reload systemd
sudo systemctl daemon-reload

# Clean up nginx
sudo rm /etc/nginx/sites-available/bbs /etc/nginx/sites-enabled/bbs
sudo systemctl restart nginx
```

## Next Steps

- [ ] Customize bulletins in admin panel
- [ ] Invite neighbors to connect
- [ ] Set up MQTT bridge if using KITT
- [ ] Deploy multiple USB adapters for mesh coverage
- [ ] Add custom logo/branding

## Support

- **Main docs**: See `README.md` in this folder
- **Integration guide**: See `INTEGRATION_GUIDE.md` in parent folder
- **Security notes**: See `../../SECURITY.md`
- **API reference**: See `../../API_TESTING.md`

---

**Stuck?** Check logs first: `journalctl -u bbs -f` and `curl http://127.0.0.1:5000`

**Estimated time**: 5-30 min depending on path (automated ~5 min, manual ~30 min)

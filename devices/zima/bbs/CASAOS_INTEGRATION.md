# CasaOS Integration Guide

**How to integrate Neighborhood BBS with CasaOS and submit to AppStore**

---

## 📋 Quick Setup

### For Users (Installing from CasaOS)

1. Open CasaOS dashboard: `http://<your-device>:80`
2. Go to **AppStore**
3. Search **"Neighborhood BBS"**
4. Click **Install**
5. Access at: `http://<your-device>:5000` after deployment

---

## 🔧 For Developers (Contributing to CasaOS)

### Prerequisites

- CasaOS instance running (v0.4.4+)
- GitHub account
- Docker account (optional, for hosting images)

### File Structure

Your manifest file should be placed in the CasaOS AppStore repository:

```
CasaOS/AppStore/
├── apps/
│   ├── neighborhood-bbs/
│   │   ├── casaos.yml          ← Your app definition
│   │   ├── icon.png            ← App icon (512x512)
│   │   ├── screenshot1.png      ← Screenshots
│   │   └── screenshot2.png
│   └── ...
└── ...
```

### Manifest File (casaos.yml)

```yaml
# casaos.yml - Complete manifest example

name: Neighborhood BBS
description: Local WiFi bulletin board system with captive portal and live chat
version: 1.0.0
category: network
icon: https://raw.githubusercontent.com/.../icon.png

developer:
  name: Gh0stlyKn1ght
  url: https://github.com/Gh0stlyKn1ght

support:
  url: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues

source_code: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS

services:
  neighborhood-bbs:
    name: Neighborhood BBS
    image: ghcr.io/gh0stlykn1ght/neighborhood-bbs:latest
    restart_policy: unless_stopped
    environment:
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-gh0stly}
      - FLASK_ENV=production
    ports:
      - target: 5000
        published: ${APP_PORT:-5000}
    volumes:
      - type: volume
        source: bbs_data
        target: /app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]

volumes:
  bbs_data:

tags:
  - network
  - communication
  - bbs
  - mesh
```

### Key Fields Explained

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | App display name | "Neighborhood BBS" |
| `description` | Short description (1 line) | "Local WiFi BBS with captive portal" |
| `version` | Semantic version | "1.0.0" |
| `category` | AppStore category | "network", "media", "utilities" |
| `icon` | Remote URL to icon (512x512) | "https://...icon.png" |
| `services` | Container definitions | Docker Compose service spec |
| `environment` | Environment variables | Port, passwords, configs |
| `ports` | Port mappings | `target: 5000, published: 5000` |
| `volumes` | Data persistence | Mount paths for SQLite, configs |
| `tags` | Search keywords | ["bbs", "chat", "mesh", "network"] |

### Preparing Your App for Submission

#### 1. Create Docker Image

Ensure your Dockerfile works:

```bash
# Build locally
docker build -t neighborhood-bbs:latest .

# Test it
docker run -p 5000:5000 \
  -e ADMIN_PASSWORD=test \
  neighborhood-bbs:latest

# Verify health endpoint
curl http://localhost:5000/health
```

#### 2. Push to Docker Registry

Option A: Docker Hub

```bash
# Login
docker login

# Tag image
docker tag neighborhood-bbs:latest <your-user>/neighborhood-bbs:latest

# Push
docker push <your-user>/neighborhood-bbs:latest

# Update casaos.yml
# image: <your-user>/neighborhood-bbs:latest
```

Option B: GitHub Container Registry

```bash
# Login (use GitHub token)
docker login ghcr.io -u <github-user>

# Tag image
docker tag neighborhood-bbs:latest ghcr.io/<github-user>/neighborhood-bbs:latest

# Push
docker push ghcr.io/<github-user>/neighborhood-bbs:latest

# Update casaos.yml
# image: ghcr.io/<github-user>/neighborhood-bbs:latest
```

#### 3. Create Assets

**Icon (512x512 PNG)**
- Save as: `icon.png`
- Should be recognizable at small sizes
- Recommend: BBS retro aesthetic

**Screenshots**
- 2-3 screenshots showing UI
- Save as: `screenshot1.png`, `screenshot2.png`
- Recommended dimensions: 1280x720 or 1024x768

#### 4. Create Documentation

Create `README.md` in app directory:

```markdown
# Neighborhood BBS on CasaOS

## Quick Start

1. Install from CasaOS AppStore
2. Wait for container to start (~30 seconds)
3. Open: http://<your-device>:5000
4. Login admin: sysop / gh0stly
5. Change admin password!

## Configuration

### Admin Password
Change after first login in Settings tab.

### WiFi SSID
Default: `NEIGHBORHOOD_BBS`

### Port
Default: 5000

## Support
- Docs: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS
- Issues: https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues
```

### Submitting to CasaOS AppStore

#### Step 1: Fork CasaOS AppStore

```bash
# Go to https://github.com/IceWhaleTech/AppStore
# Click "Fork"
```

#### Step 2: Add Your App

```bash
# In your fork
git clone https://github.com/<your-user>/AppStore.git
cd AppStore

# Create app directory
mkdir -p apps/neighborhood-bbs

# Copy files
cp casaos.yml apps/neighborhood-bbs/
cp icon.png apps/neighborhood-bbs/
cp screenshot1.png apps/neighborhood-bbs/
cp README.md apps/neighborhood-bbs/

# Commit
git add apps/neighborhood-bbs/
git commit -m "Add Neighborhood BBS app"
git push origin main
```

#### Step 3: Create Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Create PR to `IceWhaleTech/AppStore:main`
4. Fill in details:
   - App name: "Neighborhood BBS"
   - Version: "1.0.0"
   - Description: "Local WiFi BBS with captive portal and live chat"
   - Screenshots: Include 2-3 images
5. Submit!

#### Step 4: Respond to Reviews

CasaOS team may request:
- Better description
- Icon improvements
- Changed permissions
- Additional documentation

Address feedback and update PR.

### Validation Checklist

Before submission, verify:

- ✅ App installs from manifest
- ✅ Container starts within 30 seconds
- ✅ Health endpoint returns 200 OK
- ✅ Web UI accessible on configured port
- ✅ Admin login works (sysop/gh0stly)
- ✅ Can send/receive messages
- ✅ Settings panel accessible
- ✅ Restart doesn't lose data (volume persistence)
- ✅ Icon is 512x512 PNG
- ✅ Screenshots are clear and show main features
- ✅ casaos.yml has valid syntax
- ✅ No hardcoded IPs (use 0.0.0.0)
- ✅ Environment variables configurable
- ✅ No exposed secrets in environment

---

## Testing Your Manifest Locally

### Method 1: CasaOS Web UI

If you have CasaOS running:

1. SSH to CasaOS device
2. Edit app directory
3. Place casaos.yml in `/var/lib/casaos/custom-apps/`
4. Restart CasaOS service
5. Check AppStore for your app

### Method 2: Docker Compose Simulation

Test without CasaOS:

```bash
# In your app directory
docker-compose up -d

# Verify
curl http://localhost:5000/health

# Test web UI
open http://localhost:5000
```

### Method 3: Syntax Validation

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('casaos.yml'))"

# Should output nothing if valid
# If error: check YAML indentation
```

---

## Updating Your App

When you release a new version:

1. **Build and push new image:**
   ```bash
   docker build -t ghcr.io/user/neighborhood-bbs:1.1.0 .
   docker push ghcr.io/user/neighborhood-bbs:1.1.0
   ```

2. **Update casaos.yml:**
   ```yaml
   version: 1.1.0
   services:
     neighborhood-bbs:
       image: ghcr.io/user/neighborhood-bbs:1.1.0
   ```

3. **Update in AppStore:**
   - Fork CasaOS/AppStore again
   - Update `apps/neighborhood-bbs/casaos.yml`
   - Create PR with changes

CasaOS users will see "Update Available" and can update with one click.

---

## Environment Variables Reference

Users can customize these variables:

```yaml
environment:
  # Admin password (change this!)
  - ADMIN_PASSWORD=gh0stly
  
  # Production mode (no debug output)
  - FLASK_ENV=production
  
  # Port (usually 5000)
  - LISTEN_PORT=5000
  
  # Optional: Custom log level
  - LOG_LEVEL=INFO
```

---

## Troubleshooting for Users

If user reports issues:

1. **Won't start:**
   - Check logs: CasaOS → App → View logs
   - Ensure port isn't already in use
   - Check Docker disk space: `docker system df`

2. **Can't access web UI:**
   - Verify container running: `docker ps`
   - Try direct IP: `http://192.168.x.x:5000`
   - Check firewall

3. **Lost data on restart:**
   - Check volume is mapped correctly
   - Verify `/app/data` is mounted

4. **Slow/laggy:**
   - Check ZimaBoard CPU: May need more resources
   - Reduce message retention in admin settings

---

## CasaOS API Integration (Advanced)

CasaOS provides an API for deeper integration:

```bash
# Get app status
curl http://localhost:3000/api/apps/neighborhood-bbs

# Get app logs
curl http://localhost:3000/api/apps/neighborhood-bbs/logs

# Restart app
curl -X POST http://localhost:3000/api/apps/neighborhood-bbs/restart
```

---

## Resources

- **CasaOS Documentation:** https://www.casaos.io/docs/
- **AppStore Guidelines:** https://github.com/IceWhaleTech/AppStore#guidelines
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/
- **Manifest Spec:** https://github.com/IceWhaleTech/AppStore#manifest-specification

---

**Last Updated:** March 2026  
**CasaOS Target:** v0.4.4+  
**Docker Target:** v20.10+

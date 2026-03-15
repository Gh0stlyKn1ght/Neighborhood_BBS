# Neighborhood BBS - Setup Guide

## Prerequisites

- Python 3.7 or higher
- pip or conda
- Git
- SQLite (included with Python)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Neighborhood_BBS.git
cd Neighborhood_BBS
```

### 2. Create Virtual Environment

```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Application

Copy the sample configuration:

```bash
cp config/default.conf config.conf
```

Edit `config.conf` with your settings.

### 5. Initialize Database

```bash
python scripts/init_db.py
```

### 6. Run the Application

```bash
cd src
python main.py
```

The application will be available at `http://localhost:8080`

## Hardware Setup

### Zima Board Setup

1. Install the Neighborhood BBS package:
   ```bash
   sudo apt-get install -y git python3-pip
   git clone https://github.com/yourusername/Neighborhood_BBS.git
   cd Neighborhood_BBS
   pip3 install -r requirements.txt
   ```

2. Set up as a service:
   ```bash
   sudo cp config/neighborhood-bbs.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable neighborhood-bbs
   sudo systemctl start neighborhood-bbs
   ```

### ESP8266 Setup

See [firmware/esp8266/README.md](../firmware/esp8266/README.md) for detailed firmware flashing instructions.

## Network Configuration

### Local Network

For local network access, ensure your firewall allows connections on port 8080:

```bash
# On Linux
sudo ufw allow 8080/tcp

# On Windows, use Windows Defender Firewall GUI
```

### Behind a Proxy

If running behind Nginx:

```nginx
server {
    listen 80;
    server_name your.domain.local;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080  # On Linux/Mac
netstat -ano | findstr :8080  # On Windows

# Kill the process or use different port
export PORT=8081  # On Linux/Mac
set PORT=8081  # On Windows
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data!)
rm data/neighborhood.db
python scripts/init_db.py
```

### Connection Issues

- Check firewall settings
- Verify port forwarding if on different network
- Check logs in `logs/` directory

## Support

For issues and questions, please open an issue on GitHub.

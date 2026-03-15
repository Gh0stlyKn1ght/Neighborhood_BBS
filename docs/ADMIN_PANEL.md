# Admin Panel Documentation

## Overview

The Neighborhood BBS Admin Panel provides centralized management for:
- **Device Banning**: Block devices by ID, MAC address, or IP address
- **Network Configuration**: Manage system network settings
- **Theme Management**: Create and manage custom themes for the BBS

## Features

### 🚫 Device Ban Management
- Ban devices permanently or temporarily
- Ban by Device ID, MAC Address, or IP Address
- Track ban reasons and admin who issued the ban
- Set ban expiration times (temporary bans)
- Quick access to unban devices

### 🌐 Network Configuration
- Store and manage network settings
- Support for multiple data types (string, integer, boolean, JSON)
- Audit trail with update timestamps
- Easy configuration lookup and modification

### 🎨 Theme Management
- Create custom themes with color customization
- Set primary/secondary colors, background, and text colors
- Configure custom fonts
- Activate/switch between themes
- Preview theme colors before activation

## Access

### URL
- **Login**: http://localhost:8080/admin-login.html
- **Dashboard**: http://localhost:8080/admin/dashboard.html

### Default Credentials
After initial setup, use the credentials created during database initialization.

## API Endpoints

### Authentication
```
POST /api/admin/login
POST /api/admin/logout
GET /api/admin/me
```

### Device Management
```
POST /api/admin/devices/ban
GET /api/admin/devices/bans
GET /api/admin/devices/check/<device_id>
GET /api/admin/devices/check-ip/<ip_address>
POST /api/admin/devices/unban/<device_id>
```

### Network Configuration
```
GET /api/admin/network/config
GET /api/admin/network/config/<setting_name>
POST /api/admin/network/config
```

### Theme Management
```
GET /api/admin/themes
GET /api/admin/themes/active
POST /api/admin/themes
POST /api/admin/themes/<theme_id>/activate
PUT /api/admin/themes/<theme_id>
DELETE /api/admin/themes/<theme_id>
```

### Dashboard
```
GET /api/admin/dashboard
```

## Initial Setup

### 1. Create Admin User

Use the provided setup script to create an initial admin user:

```bash
python scripts/create_admin_user.py --username admin --password your_secure_password --email admin@bbs.local
```

### 2. Login to Admin Panel

Navigate to http://localhost:8080/admin-login.html and login with the credentials you created.

### 3. Configure Settings

- Create themes for your BBS
- Set up network configurations
- Start managing banned devices as needed

## Security Features

- **Session Management**: Secure session cookies with HttpOnly and SameSite flags
- **Rate Limiting**: Login attempts limited to 5 per minute
- **Password Hashing**: All passwords stored using Werkzeug's secure hash functions
- **Authentication Required**: All admin endpoints require a valid admin session
- **Role-Based Access**: Admin vs Moderator roles for sensitive operations

## User Roles

### Admin
- Full access to all features
- Can manage other admins
- Can delete themes and change critical settings

### Moderator
- Can view settings and manage devices
- Cannot modify critical network configurations
- Cannot delete themes

## Device Ban Management

### Banning a Device

1. Navigate to "Device Management" section
2. Fill in device details:
   - **Device ID**: Unique identifier for the device
   - **Device Type**: Type of device (optional)
   - **MAC Address**: Device MAC address (optional)
   - **IP Address**: Device IP address (optional)
   - **Ban Reason**: Reason for banning
   - **Expire In**: Duration in hours (leave empty for permanent ban)
3. Click "Ban Device"

### Checking if Device is Banned

The system automatically rejects requests from banned devices:

```bash
curl http://localhost:8080/api/admin/devices/check/device-123
curl http://localhost:8080/api/admin/devices/check-ip/192.168.1.100
```

Response:
```json
{
  "is_banned": true,
  "ban_reason": "Spam/Abuse",
  "expires_at": "2024-03-20T10:00:00",
  "banned_at": "2024-03-19T10:00:00"
}
```

## Network Configuration

### Common Settings

```
max_connections: 100
timeout: 300
enable_logging: true
max_message_size: 1000
```

### Setting Custom Configuration

1. Navigate to "Network Config" section
2. Enter setting name and value
3. Select data type
4. Add optional description
5. Click "Save Configuration"

## Theme Management

### Creating a Theme

1. Navigate to "Theme Manager" section
2. Enter theme name
3. Use color pickers to set:
   - Primary Color (main brand color)
   - Secondary Color (accent)
   - Background Color
   - Text Color
4. Set custom font family (default: Arial, sans-serif)
5. Click "Create Theme"

### Available Color Presets

**Dark Theme**
- Primary: #1a1a1a
- Secondary: #333333
- Background: #0d0d0d
- Text: #ffffff

**Light Theme**
- Primary: #007bff
- Secondary: #6c757d
- Background: #ffffff
- Text: #000000

**Forest Theme**
- Primary: #228B22
- Secondary: #32CD32
- Background: #f0f8f0
- Text: #1a1a1a

## Dashboard Overview

The dashboard provides real-time statistics:
- Total banned devices
- Network configurations count
- Available themes count
- Current admin account info

## Troubleshooting

### Login Issues
- Clear browser cookies
- Verify admin user exists: `python scripts/list_admin_users.py`
- Check SECRET_KEY environment variable is set

### Device Ban Not Working
- Verify device ID is spelled correctly
- Check if device is already banned: Use "Check Device" endpoint
- Ensure request includes device ID in headers/parameters

### Theme Not Applying
- Ensure theme is set as "Active"
- Clear browser cache
- Check client-side theme CSS loading
- Verify all color values are valid hex codes

## Environment Variables

```bash
# Admin settings
ADMIN_SESSION_TIMEOUT=3600        # Session timeout in seconds (default: 1 hour)
SESSION_COOKIE_SECURE=true        # Use secure cookies (HTTPS only)

# Security
SECRET_KEY=your_secret_key_here   # Flask secret key
```

## File Locations

- **Admin Routes**: `/src/admin/routes.py`
- **Admin Auth**: `/src/admin/auth.py`
- **Login Template**: `/web/templates/admin-login.html`
- **Dashboard Template**: `/web/templates/admin-dashboard.html`
- **Database**: `/data/neighborhood.db`

## Support

For issues or feature requests, please contact the development team.

# Admin Panel Setup & Quick Start Guide

## Quick Start (5 Minutes)

### 1. Initialize Database
```bash
cd /path/to/Neighborhood_BBS
python server/src/main.py init-db
```

### 2. Create Admin User
```bash
python server/scripts/create_admin_user.py \
  --username admin \
  --password MySecurePass123 \
  --email admin@neighborhood.bbs \
  --role admin
```

### 3. Start the Server
```bash
cd server
python src/main.py
```

### 4. Access Admin Panel
- **Login**: http://localhost:8080/admin-login.html
- **Dashboard**: http://localhost:8080/admin/dashboard.html

---

## Feature Walkthrough

### 🚫 Device Management

**Scenario**: You want to ban a problematic device

1. Go to Dashboard → Device Management
2. Enter device details:
   - Device ID: `malicious-router-01`
   - Device Type: `router`
   - MAC: `AA:BB:CC:DD:EE:FF`
   - IP: `192.168.1.50`
3. Reason: `Repeated spam attempts`
4. Optional: Set ban duration (24 hours)
5. Click "Ban Device"

**Result**: Device is immediately blocked from accessing the BBS

---

### 🌐 Network Configuration

**Scenario**: You want to limit concurrent connections

1. Go to Dashboard → Network Config
2. Setting Name: `max_connections`
3. Value: `50`
4. Type: `Integer`
5. Description: `Maximum concurrent users allowed`
6. Click "Save Configuration"

**Common Settings**:
```
max_connections: 50-100
timeout: 300 (seconds)
enable_logging: true
max_message_size: 1000 (characters)
max_ban_duration: 2592000 (30 days in seconds)
```

---

### 🎨 Theme Management

**Scenario**: Create a dark theme for accessibility

1. Go to Dashboard → Theme Manager
2. Theme Name: `Dark Mode`
3. Use color picker to set:
   - Primary: `#1a1a1a` (dark background)
   - Secondary: `#444444` (accents)
   - Background: `#0d0d0d` (pure dark)
   - Text: `#ffffff` (white text)
4. Font Family: `'Courier New', monospace`
5. Click "Create Theme"
6. Click "Activate" to deploy

**Result**: All users see the dark theme

---

## Admin Roles

| Feature | Admin | Moderator |
|---------|-------|-----------|
| View Dashboard | ✓ | ✓ |
| Ban Devices | ✓ | ✓ |
| View Bans | ✓ | ✓ |
| Unban Devices | ✓ | ✓ |
| Create Themes | ✓ | ✓ |
| Activate Themes | ✓ | ✓ |
| Delete Themes | ✓ | ✗ |
| Modify Network Config | ✓ | ✗ |
| Manage Admin Users | ✓ | ✗ |

---

## API Usage Examples

### Check if Device is Banned
```bash
curl http://localhost:8080/api/admin/devices/check/device-123
```

Response if banned:
```json
{
  "is_banned": true,
  "ban_reason": "Spam/Abuse",
  "expires_at": "2024-03-20T10:00:00",
  "banned_at": "2024-03-19T10:00:00"
}
```

### Get Dashboard Stats
```bash
curl -H "Cookie: session=..." http://localhost:8080/api/admin/dashboard
```

### Get Active Theme
```bash
curl http://localhost:8080/api/admin/themes/active
```

Response:
```json
{
  "id": 1,
  "theme_name": "Dark Mode",
  "primary_color": "#1a1a1a",
  "secondary_color": "#444444",
  "background_color": "#0d0d0d",
  "text_color": "#ffffff",
  "font_family": "'Courier New', monospace",
  "is_active": true
}
```

---

## Troubleshooting

### Can't Login
```bash
# Verify admin user exists
python scripts/list_admin_users.py

# Reset admin password
python scripts/reset_admin_password.py --username admin --password NewPassword123
```

### Ban Not Working
1. Check if device is already banned:
   ```bash
   curl http://localhost:8080/api/admin/devices/check/device-id
   ```

2. Verify device ID in request matches ban record

3. Check browser console for errors

### Theme Not Applying
1. Clear browser cache (Ctrl+Shift+Delete)
2. Verify theme is set as "Active"
3. Refresh page
4. Check CSS colors are valid hex codes

---

## Security Notes

⚠️ **Important**:
- Always use a strong password (12+ characters recommended)
- Never share admin credentials
- Change default SECRET_KEY in production
- Use HTTPS in production (set SESSION_COOKIE_SECURE=true)
- Rotate admin passwords regularly
- Monitor admin login attempts

---

## Database Backup

Backup your admin and ban data:
```bash
cp data/neighborhood.db data/neighborhood.db.backup
```

---

## Advanced: Custom Theme Presets

Save this as a script to create multiple themes at once:

```python
#!/usr/bin/env python
from models import ThemeSettings

themes = [
    {
        'name': 'Light',
        'primary': '#007bff',
        'secondary': '#6c757d',
        'background': '#ffffff',
        'text': '#000000',
        'font': 'Arial, sans-serif'
    },
    {
        'name': 'Dark',
        'primary': '#1a1a1a',
        'secondary': '#444444',
        'background': '#0d0d0d',
        'text': '#ffffff',
        'font': "'Courier New', monospace"
    },
    {
        'name': 'Nature',
        'primary': '#228B22',
        'secondary': '#32CD32',
        'background': '#f0f8f0',
        'text': '#1a4d1a',
        'font': 'Georgia, serif'
    }
]

for theme in themes:
    ThemeSettings.create_theme(
        theme['name'],
        theme['primary'],
        theme['secondary'],
        theme['background'],
        theme['text'],
        theme['font']
    )
    print(f"✓ Created theme: {theme['name']}")
```

---

## Support & Documentation

- Full API docs: See `/docs/ADMIN_PANEL.md`
- Source code: `/src/admin/routes.py`
- Database schema: `/src/models.py`

---

*Last Updated: March 2026*
*Neighborhood BBS Admin Panel v1.0*

# Lite vs Full Mode: Deployment Options

**Date Added:** March 15, 2026  
**Feature:** Configurable BBS deployment modes  
**Status:** ✅ Complete and tested

---

## Overview

Neighborhood BBS now supports two deployment modes:

- **LITE Mode**: Simple, ephemeral anonymous chat. Perfect for quick communities or privacy-focused deployments.
- **FULL Mode**: Complete BBS platform with admin tools, themes, privacy settings, and persistent features.

Both modes support **user blocking** - allowing users to block/unblock nicknames they don't want to see messages from.

---

## Setup: Choosing Your Mode

During the first-time setup wizard (Step 1), you'll be asked to select your mode:

```
┌─────────────────────────────────────┐
│ STEP 1 OF 6: CHOOSE BBS MODE        │
├─────────────────────────────────────┤
│                                     │
│ ◉ LITE MODE                         │
│   Simple anonymous chat, one room,  │
│   no admin panel, no message history│
│                                     │
│ ◯ FULL MODE                         │
│   Complete BBS with admin panel,    │
│   themes, privacy settings          │
│                                     │
└─────────────────────────────────────┘
```

### Setup Steps After Mode Selection

**Steps 2-6** (same for both modes, but behave differently):
1. Admin Password (both modes require this)
2. Privacy Settings (Lite: auto-set to ephemeral, Full: user's choice)
3. User Accounts (Lite: anonymous-only, Full: options)
4. Moderation Settings (Full mode feature, Lite mode simplified)
5. Access Control (Full mode feature, Lite mode simplified)
6. Theme & Appearance (Full mode feature, Lite mode skipped)

---

## Mode Comparison

| Feature | Lite | Full |
|---------|------|------|
| **Chat** | 1 room (General) | Multiple rooms |
| **Messages** | Ephemeral (auto-delete) | 3 options: Ephemeral/7-day/Persistent |
| **User Blocking** | ✅ Yes | ✅ Yes |
| **Admin Panel** | ❌ No | ✅ Yes |
| **Themes** | ❌ No | ✅ Yes |
| **Settings Panel** | ❌ No | ✅ Yes |
| **Moderation Options** | Basic | Advanced |
| **Setup Time** | ~2 minutes | ~5 minutes |
| **Use Case** | Quick communities | Professional BBSes |

---

## LITE Mode Details

### Perfect For:
- Quick community setups (ephemeral chat)
- Privacy-focused deployments (no message history)
- Small groups or events
- Testing/POC environments
- IPFS-style distributed nodes

### Key Characteristics:
- **One Chat Room**: Users join a single General room (no room creation)
- **Anonymous Only**: No user accounts, just pick a nickname
- **Ephemeral Messages**: All messages stored in RAM, deleted when user disconnects
- **No Admin Panel**: Simple moderation only (user blocking)
- **No Themes**: Single default terminal theme
- **User Blocking**: Each user can block up to N nicknames
- **Setup Wizard**: 6 steps, but most Lite options auto-configured
- **Storage**: Minimal database footprint (no message history)

### Use Case Example:
```
User joins → Types nickname "alice" → Enters General room → 
Chats → Sees Bob, blocks Bob if annoying → Disconnects → 
Messages gone, session ended
```

### Message Flow in Lite Mode:
```
┌─────────────┐
│   Alice     │
│  (joins)    │
└──────┬──────┘
       │
       ├─→ [RAM] Session created
       │
       ├─→ [WebSocket] Join General room
       │
       ├─→ Send message "Hello!"
       │        │
       │        ├─→ [RAM] Message stored temporarily
       │        └─→ [Broadcast] Bob, Charlie see it
       │
       └─→ [Disconnect] Session ends
              │
              └─→ Messages in RAM deleted
```

---

## FULL Mode Details

### Perfect For:
- Permanent community platforms
- Professional/business use
- Long-term knowledge bases
- Communities that need moderation
- organizations wanting to keep records

### Key Characteristics:
- **Multiple Rooms**: Admin creates rooms (General, Off-Topic, Announcements, etc.)
- **User Accounts**: Optional accounts, anonymous-only, or both
- **Privacy Modes**: 
  - Full Privacy: Ephemeral (like Lite)
  - Hybrid: 7-day auto-delete
  - Persistent: Keep all messages
- **Admin Panel**: Dashboard, user management, moderation
- **Themes**: Customize colors, fonts (retro BBS style)
- **User Blocking**: Block nicknames across all rooms
- **Advanced Moderation**: Content filtering, timeouts, device bans
- **Setup Wizard**: 6 steps with in-depth configuration

### Use Case Example:
```
Admin sets up → Creates 3 rooms → Configures privacy to Hybrid → 
Users join → Chat in multiple rooms → Messages saved 7 days → 
Admin reviews in dashboard → Bans problematic users → 
App continues, messages auto-expire after 7 days
```

---

## API: Checking Available Features

Frontend can detect which mode is running:

```
GET /api/user/features
```

Response (Lite Mode):
```json
{
  "bbs_mode": "lite",
  "is_lite": true,
  "is_full": false,
  "allow_room_creation": false,
  "allow_admin_panel": false,
  "allow_themes": false,
  "allow_settings": false,
  "allow_user_blocking": true,
  "privacy_mode": "full_privacy",
  "messages_ephemeral": true
}
```

Response (Full Mode):
```json
{
  "bbs_mode": "full",
  "is_lite": false,
  "is_full": true,
  "allow_room_creation": true,
  "allow_admin_panel": true,
  "allow_themes": true,
  "allow_settings": true,
  "allow_user_blocking": true,
  "privacy_mode": "hybrid",
  "messages_ephemeral": false
}
```

---

## User Blocking Feature (Both Modes)

All users can block nicknames they don't want to interact with.

### API Endpoints:

#### Block a User
```
POST /api/user/block
Body: {
  "session_id": "uuid",
  "blocked_nickname": "troll",
  "reason": "Spam"  // optional
}
Returns: {
  "status": "ok",
  "blocked_users": ["troll", "spammer"],
  "message": "troll has been blocked"
}
```

#### Unblock a User
```
POST /api/user/unblock
Body: {
  "session_id": "uuid",
  "blocked_nickname": "troll"
}
Returns: {
  "status": "ok",
  "blocked_users": [],
  "message": "troll has been unblocked"
}
```

#### Get Blocked List
```
GET /api/user/blocked-list?session_id=uuid
Returns: {
  "blocked_users": ["troll", "spammer"],
  "count": 2
}
```

### Frontend Behavior:
- When a blocked user sends a message, your UI hides it
- You see "[blocked user text hidden]" or similar placeholder
- You can unblock anytime to see their messages again
- Blocking is per-session (each user has own block list)

---

## Database Schema Changes

### New Table: `blocked_users`
```sql
CREATE TABLE blocked_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    blocked_nickname TEXT NOT NULL,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    UNIQUE(session_id, blocked_nickname)
);
```

### Updated: `setup_config`
Added new config key:
- `bbs_mode`: 'lite' or 'full' (stored during setup)

---

## Deployment Guidelines

### Lite Mode Deployment:
```bash
# Run with default settings (Lite mode chosen in setup)
python server.py

# Visit setup wizard: http://localhost:5000/setup
# Step 1: Choose "LITE MODE"
# Steps 2-6: Admin password, auto-configured rest
# Done! Users can join immediately
```

**Optimal Settings:**
- Single VPS or laptop
- ~100MB RAM for 1000 concurrent users
- No database backup needed (ephemeral data)
- Perfect for Raspberry Pi or low-power devices

### Full Mode Deployment:
```bash
# Run with full features (Full mode chosen in setup)
python server.py

# Visit setup wizard: http://localhost:5000/setup
# Step 1: Choose "FULL MODE"
# Steps 2-6: Configure everything
# Admin panel at: /admin (after setup)
```

**Optimal Settings:**
- Server or dedicated machine
- ~500MB RAM recommended
- Regular database backups (persistent data)
- SSL/TLS for privacy
- Domain name recommended

---

## Mode Switching (Post-Setup)

Once setup is complete, mode can be changed from the database:

```python
from setup_config import SetupConfig

# Check current mode
mode = SetupConfig.get_bbs_mode()  # 'lite' or 'full'

# Switch mode (admin only, requires database access)
SetupConfig.save_bbs_mode('full')

# Verify
print(SetupConfig.get_bbs_mode())  # 'full'
```

**Warning**: Switching from Full to Lite will hide some admin features but won't delete data. Switching from Lite to Full will enable new features. Messages policy (ephemeral vs persistent) follows the new mode's privacy setting.

---

## Implementation Details

### ModeHelper Class (`mode_helper.py`)

Utility class for checking mode and getting feature flags:

```python
from mode_helper import ModeHelper

# Check mode
is_lite = ModeHelper.is_lite()
is_full = ModeHelper.is_full()

# Get privacy mode (Lite always 'full_privacy')
privacy = ModeHelper.get_privacy_mode()

# Check features
can_make_themes = ModeHelper.allow_themes()
can_block_users = True  # Both modes support blocking

# Get all flags
flags = ModeHelper.get_feature_flags()
```

### Setup Flow

1. **Step 1 (NEW)**: Mode Selection
   - Radio buttons: LITE or FULL
   - Frontend conditional on user choice
   - Stored in setup_config table

2. **Steps 2-6**: Conditional Configuration
   - Lite: Simpler dialogs, fewer options
   - Full: Complete configuration
   - Both require admin password

3. **Post-Setup**: Feature Access
   - Frontend checks /api/user/features
   - UI hides/shows features based on mode
   - Chat routes respect mode (room limits, privacy)

---

## Testing

### Run Mode Tests:
```bash
cd server/src
python test_lite_full_modes.py
```

Results (all should pass):
- ✅ Lite Mode setup and features
- ✅ Full Mode setup and features
- ✅ User blocking in both modes
- ✅ Mode persistence
- ✅ Feature flags accuracy
- ✅ Privacy mode override (Lite always ephemeral)

---

## Future Enhancements

Potential improvements for later versions:

- [ ] Mode migration tool (Lite → Full with data preservation)
- [ ] Per-room privacy settings in Full mode
- [ ] Lite mode room limit enforcement at API level
- [ ] Admin feature toggle override (enable some Full features in Lite)
- [ ] Template presets (quick-start configs for common scenarios)
- [ ] Multi-tenancy (multiple instances per deployment)

---

## Summary

**Lite Mode** is perfect for:
- Quick deployments
- Privacy-first communities
- Low-power devices
- Testing/POC

**Full Mode** is perfect for:
- Professional communities
- Long-term platforms
- Moderation needs
- Customization requirements

Both modes feature **user blocking** for everyone to manage their experience, and implementation is complete, tested, and ready for production use.

**Commit:** Ready for merge
**Status:** ✅ Feature complete, all tests passing

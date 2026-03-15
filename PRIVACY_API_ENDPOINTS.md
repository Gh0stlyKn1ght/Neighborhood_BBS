# Privacy API Endpoints

All privacy endpoints are **public** and do not require user authentication. They are designed to provide transparency to community members about what data is being collected and how it's being handled.

## Endpoints

### `/api/privacy/info` (GET)
Get comprehensive privacy information for the community

**Response:**
```json
{
  "privacy_mode": "full_privacy|hybrid|persistent",
  "privacy_info": {
    "name": "Privacy mode name",
    "description": "What privacy mode means",
    "data_collected": ["List of data types collected"],
    "data_not_collected": ["List of data NOT collected"],
    "message_storage": "Where messages are stored",
    "message_lifespan": "How long messages are kept",
    "can_admins_see_history": true/false
  },
  "user_accounts": {
    "type": "anonymous|optional|required",
    "requires_login": true/false,
    "description": "Account system required"
  },
  "access_control": {
    "type": "open|passcode|approved",
    "description": "How users access the community"
  },
  "moderation": {
    "levels": ["List of enabled moderation features"],
    "tracks_individual_users": true/false,
    "description": "How moderation works"
  }
}
```

**Example:**
Full privacy mode with anonymous access:
- No login required
- No history kept
- No individual user tracking
- All data deleted on disconnect

---

### `/api/privacy/statistics` (GET)
Get aggregate statistics about message storage and cleanup

**Response:**
```json
{
  "total_messages": 12345,
  "messages_in_memory": 567,
  "messages_in_database": 11778,
  "expired_messages": 0,
  "messages_expiring_in_24h": 89,
  "last_cleanup": "2024-01-15T02:00:00Z",
  "cleanup_status": "running|idle|disabled",
  "privacy_mode": "hybrid|full_privacy|persistent"
}
```

**What This Shows:**
- Regular statistics to prove messages are being cleaned up
- Shows that hybrid mode actually deletes messages after 7 days
- No individual user data (completely aggregate)

---

### `/api/privacy/policy` (GET)
Get the community's privacy policy

**Response:**
```json
{
  "title": "Privacy Policy - Neighborhood BBS",
  "version": "1.0",
  "effective_date": "2024-01-15",
  "privacy_mode": "hybrid|full_privacy|persistent",
  "policy_text": "Full privacy policy text based on selected mode"
}
```

**What This Shows:**
- Privacy policy automatically generated from admin's choices
- Different policies for different privacy modes
- Clear explanation of what data is and isn't collected

---

### `/api/privacy/transparency` (GET)
Get transparency report about technical privacy measures

**Response:**
```json
{
  "transparency": {
    "privacy_first": true,
    "no_tracking": "Individual users not tracked in full_privacy mode",
    "data_minimization": "Only necessary data collected",
    "audit_transparency": "All admin actions logged",
    "user_control": "Users can request data deletion (where applicable)",
    "technical_measures": [
      "End-to-end encrypted data at rest",
      "No IP logging",
      "No device fingerprinting",
      "Automatic message cleanup (hybrid mode)",
      "Rate limiting on all endpoints",
      "No external analytics",
      "No third-party data sharing"
    ]
  },
  "storage_info": {
    "total_messages": 12345,
    "messages_in_memory": 567,
    "messages_in_database": 11778,
    "expired_messages": 0,
    "messages_expiring_in_24h": 89
  }
}
```

---

## Privacy Modes Explained

### Full Privacy (Ephemeral)
- **Best for:** Communities where privacy is paramount
- **Data collected:** Nothing permanent
- **How it works:** Messages stored in RAM during session, deleted on disconnect
- **Admins can see:** Current conversations only
- **History available:** No
- **User tracking:** No
- **Analytics:** No

### Hybrid (7-day retention)
- **Best for:** Communities needing some reference without bulk storage
- **Data collected:** Messages (7 days only)
- **How it works:** Messages saved to database, auto-deleted after 7 days
- **Admins can see:** Last 7 days of chat
- **History available:** Last 7 days
- **User tracking:** No individual tracking
- **Analytics:** No personal analytics

### Persistent
- **Best for:** Communities needing full message history (Q&A, help, projects)
- **Data collected:** Everything
- **How it works:** All messages saved permanently
- **Admins can see:** Full chat history
- **History available:** Everything
- **User tracking:** No individual IP tracking
- **Analytics:** No external analytics

---

## What's NOT Collected (All Modes)

Regardless of privacy mode, Neighborhood BBS **never** collects:

- **IP Addresses** - Not logged or stored
- **Device Fingerprints** - No device ID tracking
- **Individual User IDs** - No user identity database
- **Behavioral Analytics** - No tracking of user behavior
- **Cookies for Tracking** - Only session cookies (not cross-site)
- **Third-party Data Sharing** - Data never sold or shared
- **External Analytics** - No Google Analytics or similar

---

## Admin Transparency

Privacy endpoints show what's actually happening:

1. **Policy endpoint** - Proves the community follows its stated privacy model
2. **Statistics endpoint** - Shows message cleanup is working (messages actually getting deleted)
3. **Transparency endpoint** - Lists all privacy-protecting technical measures
4. **Info endpoint** - Clear explanation of what data is kept

This aligns with GDPR Article 13 (transparency) and privacy by design principles.

---

## Accessing Privacy Information

Users should see privacy info:
1. **On first visit** - Before joining
2. **In settings** - Current privacy settings
3. **During signup** - Clear opt-in based on privacy mode
4. **In documentation** - Full privacy policy

### Suggested Frontend Integration

```html
<!-- Privacy banner (before setup complete) -->
<div class="privacy-info">
  <h3>Privacy First</h3>
  <p id="privacy-mode-desc">Loading...</p>
  <a href="/api/privacy/info">See our privacy policy</a>
</div>

<!-- In user settings -->
<details>
  <summary>Privacy & Data</summary>
  <div id="privacy-stats"></div>
</details>
```

```javascript
// Load privacy info on page
fetch('/api/privacy/info')
  .then(r => r.json())
  .then(data => {
    document.getElementById('privacy-mode-desc').textContent = 
      data.privacy_info.description;
  });
```

---

## For Admin Dashboard

Admins should see:
1. **Privacy statistics** - Is cleanup working?
2. **Audit logs** - What actions did admins take?
3. **Data request queue** - Have users requested data deletion?
4. **Compliance report** - Is system compliant with stated policy?

See `admin_transparency_monitor.md` for implementing admin privacy dashboard.

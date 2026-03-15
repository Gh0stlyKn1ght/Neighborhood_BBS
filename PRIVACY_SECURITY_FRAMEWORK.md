# 🔐 Neighborhood BBS - Privacy & Security Framework

Based on research from Signal, Briar, Mastodon, Lemmy, and Matrix

---

## Executive Summary

**For 10-30 person communities, transparency beats tracking.**

The best privacy = no logs to log.  
The best security = admin knowing their community personally.  
The best moderation = visible actions, not hidden ones.

---

## Part 1: First-Boot Setup Flow (Admin-Driven)

### **Initial Installation Decisions**

```
┌─────────────────────────────────────────────────────┐
│   NEIGHBORHOOD BBS - Initial Setup                  │
│                                                      │
│   This is a local, encrypted, offline-first         │
│   community chat platform.                          │
│                                                      │
│   ✓ Messages encrypted end-to-end                  │
│   ✓ No IP logging                                   │
│   ✓ No user tracking                                │
│   ✓ Admin-controlled privacy                        │
│                                                      │
│   [Learn More]                                      │
│                                                      │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   STEP 1: Set Admin Password                        │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   This is the ONLY password needed.                 │
│   Users do NOT need login accounts.                 │
│                                                      │
│   Admin Password:        [_________________]        │
│   Confirm Password:      [_________________]        │
│                                                      │
│   💡 Pro tip: Use a strong password.                │
│      Only admins need this.                         │
│                                                      │
│   [Next]                                            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│   STEP 2: Privacy Settings                          │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   How should we handle chat history?                │
│                                                      │
│   ○ FULL PRIVACY (Recommended for neighbors)       │
│     → Messages deleted when user disconnects       │
│     → No permanent record                           │
│     → Admins only see live activity                │
│     → Can't replay old chats                        │
│     ✓ Why: True privacy, less liability            │
│                                                      │
│   ○ PERSISTENT (For reference/support)             │
│     → Messages saved to database                   │
│     → Available in admin panel                      │
│     → Can search/reference old messages            │
│     → Users CAN request deletion                   │
│     ✓ Why: Useful for Q&A, help threads            │
│                                                      │
│   ○ HYBRID (Disappear after 7 days)               │
│     → Messages auto-delete after 7 days            │
│     → Users can "pin" important messages           │
│     → Balance privacy + reference                  │
│     ✓ Why: Best of both                            │
│                                                      │
│   Your choice: ○ Full Privacy  ○ Persistent  ○ Hybrid
│                                                      │
│   [Back]  [Next]                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│   STEP 3: User Accounts                             │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   Do users need accounts to chat?                   │
│                                                      │
│   ○ ANONYMOUS ONLY (Recommended)                   │
│     → No accounts needed                            │
│     → Users pick a nickname                         │
│     → No login required                             │
│     ✓ Why: Lowest friction, most private           │
│     ✗ Con: Harder to ban abusers                    │
│                                                      │
│   ○ OPTIONAL ACCOUNTS                               │
│     → Users can register (optional)                 │
│     → Or chat anonymously                           │
│     ✓ Why: Identity for people who want it         │
│     ✓ Pro: Can ban specific user accounts          │
│                                                      │
│   ○ REQUIRED ACCOUNTS (Not recommended)             │
│     → Must login to use                             │
│     ✗ Why: Reduces privacy, requires tracking      │
│                                                      │
│   Your choice: ○ Anonymous  ○ Optional  ○ Required
│                                                      │
│   [Back]  [Next]                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│   STEP 4: Moderation & Abuse Response              │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   If someone misbehaves, what can admins do?       │
│                                                      │
│   ○ CONTENT FILTERING ONLY (Most Private)           │
│     → No device/identity tracking                   │
│     → Ban specific content/patterns                │
│     → Abusers must keep trying with new content    │
│     ✓ Why: True privacy maintained                 │
│     ✗ Con: Persistent abusers hard to stop        │
│                                                      │
│   ○ SESSION-BASED (Recommended Balance)             │
│     → Temporary disconnect (24 hours)              │
│     → User can rejoin next day                      │
│     → No permanent record                           │
│     → Clean slate after timeout                    │
│     ✓ Why: Stops abuse this session, privacy later │
│                                                      │
│   ○ DEVICE-BASED (For Serious Issues)               │
│     → Ban device MAC address from WiFi AP          │
│     → User can spoof MAC (not foolproof)           │
│     → Local network control only                   │
│     ✓ Why: Effective for local WiFi control       │
│     ⚠️ Note: Can also manually block on router      │
│                                                      │
│   ○ HYBRID (Recommended for communities)            │
│     → Start with content filtering                 │
│     → Escalate to session timeout if repeat        │
│     → Device ban only for severe abuse             │
│                                                      │
│   Your choice: ○ Content ○ Session ○ Device ○ Hybrid
│                                                      │
│   [Back]  [Next]                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│   STEP 5: Access Control                            │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   How should people join your community?            │
│                                                      │
│   ○ OPEN (Anyone on WiFi can join)                 │
│     → No password needed                            │
│     → First-day setup simplest                      │
│     ✓ Why: Maximum accessibility                   │
│     ✗ Con: Strangers can join                      │
│                                                      │
│   ○ PASSCODE (Shared secret)                       │
│     → Must know passcode to join                    │
│     → Share via SMS, QR code, word-of-mouth       │
│     ✓ Why: Filters out drive-bys                   │
│     ✓ Pro: Easy to share with new neighbors       │
│     ⚠️ Note: Can be shared (not foolproof)          │
│                                                      │
│   ○ ADMIN-APPROVED (Whitelist)                     │
│     → Admin manually approves each user            │
│     → Requires identity verification               │
│     ✓ Why: Most control                             │
│     ✗ Con: Slowest setup                            │
│                                                      │
│   Your choice: ○ Open ○ Passcode ○ Approved
│                                                      │
│   Admin passcode (if chosen): [_____________]       │
│                                                      │
│   [Back]  [Next]                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│   ✓ SETUP COMPLETE!                                │
│   ═══════════════════════════════════════════════   │
│                                                      │
│   Your settings:                                    │
│                                                      │
│   Privacy Mode:       Full Privacy (deleted on exit)
│   Data Retention:     No permanent logs             │
│   User Accounts:      Optional                      │
│   Moderation:         Hybrid approach               │
│   Access Control:     Passcode                      │
│                                                      │
│   Post-Setup Access:                                │
│   Admin Panel:        http://[device]:8080/admin    │
│                       Passcode: (your password)     │
│                                                      │
│   User Interface:     http://[device]:8080          │
│                       Passcode: (if required)       │
│                                                      │
│   📋 SAVE YOUR SETTINGS                             │
│   Keep these somewhere safe:                        │
│                                                      │
│   - Admin passcode: ______________________         │
│   - User passcode (if set): _______________        │
│   - Device IP: ___________                          │
│   - WiFi SSID: ___________                          │
│                                                      │
│   [View Setup Summary]  [Dashboard]                │
└─────────────────────────────────────────────────────┘
```

---

## Part 2: Privacy Disclaimer & User Consent

### **Displayed on First Join (Non-Admin Users)**

```
═════════════════════════════════════════════════════
    🔐 NEIGHBORHOOD BBS - PRIVACY & TERMS
═════════════════════════════════════════════════════

Welcome to a local, privacy-first community chat.

YOUR PRIVACY:
─────────────────────────────────────────────────────
✓ End-to-end encrypted messages (over WiFi)
✓ No IP addresses logged
✓ No personal tracking
✓ No analytics
✓ No data sold to third parties
✓ No cookies (unless you enable them)

HOW YOUR DATA IS HANDLED:
─────────────────────────────────────────────────────
[This server has selected: FULL PRIVACY MODE]

→ Your messages are DELETED when you disconnect
→ No permanent record of conversations
→ Admins see live chat only, not history
→ Messages not backed up or archived

(Admins can change this setting—ask them if unsure)

ABUSIVE CONTENT:
─────────────────────────────────────────────────────
This is a community for neighbors to connect, not 
to harm each other. Content that violates community
rules may be:

• Content-filtered (inappropriate language blocked)
• Temporarily removed while flagged
• Result in your session being ended (24 hours)
• In severe cases, prevent access from this device

Abusers will NOT be tracked by identity, only by
behavior. Repeat abuse may result in device-level
blocks from this WiFi network.

COMMUNITY RULES:
─────────────────────────────────────────────────────
• Be respectful to neighbors
• No harassment or threats
• No spam
• Keep messages under 240 characters
• No sharing personal info of others without consent

ADMIN TRANSPARENCY:
─────────────────────────────────────────────────────
Server Admin(s): [Local Community / Name if shown]
Admin Contact: [Contact info]
Last Privacy Policy Update: March 15, 2026

You can request:
→ Deletion of your messages (if persistent mode)
→ Appeal of any moderation action
→ Copy of your data

All requests should go to the admin above.

═════════════════════════════════════════════════════

☐ I understand and accept these terms

[I Agree & Enter Chat]  [Go Back]

═════════════════════════════════════════════════════
```

---

## Part 3: Privacy Mode Configuration

### **Option 1: FULL PRIVACY (Recommended)**

```python
# config.py
PRIVACY_MODE = "full_privacy"

# Behavior:
# - Messages stored in RAM during session
# - Database never written to for messages
# - On disconnect, RAM cleared
# - Bulletins stored (admin content always persisted)
# - Rate limiting tracked in memory only
# - No admin history replay possible

DATABASE_TABLES:
✓ bulletins (always saved - admin content)
✓ rate_limits (temporary, in-session only)
✗ messages (NOT saved - in memory only)
✗ audit_logs (NOT saved - in memory only)
```

**Pros**: Maximum privacy, no liability
**Cons**: Can't reference old conversations

### **Option 2: HYBRID (Disappear in 7 Days)**

```python
PRIVACY_MODE = "hybrid_retention"

# Behavior:
# - Messages saved to database
# - Admin can view in dashboard
# - Public message history: last 50 messages
# - Auto-delete older than 7 days (nightly cron)
# - Users can request immediate deletion
# - Can "pin" important messages (permanent)

DATABASE_TABLES:
✓ bulletins
✓ messages (with TTL/expiration)
✓ pinned_messages (permanent)
✓ audit_logs (admin actions only, 30 day retention)
```

**Pros**: Reference + privacy balance, manageable retention
**Cons**: Some data kept temporarily

### **Option 3: PERSISTENT (With User Control)**

```python
PRIVACY_MODE = "persistent"

# Behavior:
# - All messages permanently saved
# - Admin full history access
# - Users can request personal messages deleted
# - GDPR/privacy law compliance required
# - Audit trail of deletions

DATABASE_TABLES:
✓ bulletins
✓ messages (no TTL)
✓ user_messages (maps user → messages for deletion)
✓ deletion_log (audit trail of deletions)
✓ audit_logs (complete admin trail)
```

**Pros**: Full record-keeping, best for Q&A/support
**Cons**: Max privacy concerns, data liability

---

## Part 4: Account & Login System

### **Option A: ANONYMOUS (Default)**

```python
# User authentication: NONE
# Users just pick a nickname
# Session ID: random UUID per connection
# Login persistence: NONE (new session per connect)

SCHEMA:
sessions table:
  - session_id (UUID)
  - nickname (user-provided, can change)
  - connected_at
  - ip_hash (if IP logging enabled - we won't)
  - (deleted on disconnect in full privacy mode)

PROS:
✓ No auth overhead
✓ No tracking
✓ Max privacy
✓ Instant access

CONS:
✗ Can't ban specific abusers
✗ Same nickname available to multiple people
✗ No persistent user identity
```

### **Option B: OPTIONAL ACCOUNTS**

```python
# Authentication: Opt-in Username/Password
# Can also chat anonymously (no account)
# Users who register get persistent nick

SCHEMA:
users table:
  - user_id
  - username (unique, optional)
  - password_hash (if registered)
  - created_at
  - deleted (soft delete)

sessions table:
  - session_id
  - user_id (NULL if anonymous)
  - connected_at

PROS:
✓ Optional privacy (register if you want)
✓ Can ban specific users
✓ Can track contributions (if wanted)

CONS:
⚠️ Slight security burden (password storage)
⚠️ More database complexity
```

### **Option C: REQUIRED ACCOUNTS (NOT RECOMMENDED)**

```
WHY NOT:
- Violates privacy-first principle
- Requires password management overhead
- Increases registration friction
- Defeats "easy neighborhood setup" goal
```

---

## Part 5: Moderation Without Tracking

### **Content-Based Banning (What, Not Who)**

```python
# Instead of: Ban [person]
# Do this: Ban [content pattern]

banned_content table:
  id | pattern_type | pattern | reason | created_by | created_at
  
  Examples:
  1 | phrase | "hate_word" | "violates rules" | sysop | 2026-03-15
  2 | regex | "^(scam|fake).+" | "spam pattern" | sysop | 2026-03-15
  3 | hash | "3d2f1a" | "spam message" | sysop | 2026-03-15

FILTER LOGIC:
for message in incoming_messages:
    for banned in banned_content:
        if banned.pattern_type == "phrase":
            if banned.pattern in message.text.lower():
                message.text = "[moderated]"
                log_event("content_filtered")
        elif banned.pattern_type == "hash":
            if hash(message.text) == banned.pattern:
                message.text = "[removed]"
                log_event("content_removed")

NO TRACKING:
✓ No user_id stored
✓ No IP stored
✓ No device ID tracked
✓ Pattern-matched message rejected, not attributed
```

### **Session-Based Timeouts (Escalation)**

```python
# Threshold: 5 content violations in 10 minutes
# Action: Kick user off for 24 hours
# Cleanup: No record kept after 24 hours

timeout_log table:
  id | session_id | reason | timeout_until | created_at
  (Auto-deleted after timeout expires)

PROCESS:
1. User sends 5 violating messages in 10 min
2. Session marked for timeout
3. WebSocket connection closed (reason: "Community guidelines")
4. Timeout entry created (24hr TTL)
5. User can't reconnect for 24 hours
6. After 24 hours: record deleted, user can rejoin fresh
```

### **Device-Level Banning (Last Resort)**

```python
# Only for serious abuse
# Admin manually adds device to ban list
# Works at WiFi AP level

banned_devices table:
  id | mac_address | reason | banned_by | created_at | expires_at
  (Permanent unless admin removes or set expiration)

ENFORCEMENT:
Option A: At BBS level
  - Device MAC → WebSocket close on connect
  - Simple, reversible, no OS access needed

Option B: At WiFi AP level
  - hostapd blocklist update
  - More effective (can't access WiFi at all)
  - Requires SSH access to AP

IMPORTANT:
⚠️ Users can spoof MAC addresses
⚠️ Only works on WiFi they don't control
⚠️ Use as last resort for serious abuse
⚠️ Make reversible (always)
```

---

## Part 6: Passcode-Based Access (Optional)

### **Use Case: Remote Communities**

```
For neighbors ~1 mile apart who know each other:
→ Passcode keeps out random WiFi joiners

For remote islands/rural areas:
→ SMS/WhatsApp pre-share passcode
→ Authenticates without central server
```

### **Implementation**

```python
# config.py
access_control = {
    "type": "passcode",  # or "open" or "approved"
    "passcode": "h@shWith$alt",  # hashed
    "message": "Enter passcode shown on flyer",
}

# First access flow:
1. User connects to WiFi
2. Joins BBS landing page
3. See: [Enter Passcode]
4. Type: 1234
5. If correct: session created
6. If wrong: "Invalid passcode" (no retry limits—let user try)
7. If open: straight to chat

# In code:
@app.route('/join', methods=['POST'])
def join_chat():
    passcode = request.form.get('passcode', '')
    
    if PRIVACY_MODE == "full_privacy" or "hybrid":
        # Don't log passcode attempt (privacy)
        pass
    
    if check_passcode(passcode):
        session['authenticated'] = True
        redirect('/chat')
    else:
        return render_template('join.html', error="Wrong passcode")
```

---

## Part 7: Admin Panel Audit Log (What Gets Logged)

### **What Admins SEE**

```
ALLOWED (for moderation):
✓ Messages in current session
✓ Admin actions (what admin deleted/banned/etc)
✓ Bulletins created/edited
✓ Community-wide statistics (user count, message count)
✓ Abuse reports (if submitted)
✓ Moderation actions log

NOT ALLOWED (privacy):
✗ User IP addresses
✗ Device identifiers
✗ Session IDs (except current)
✗ User browsing history
✗ Timestamps of user actions
✗ "User 3 sent message 487 at 3:15pm" links
```

### **Audit Log Schema**

```sql
-- ADMIN ACTIONS ONLY (What admins do, not what users do)
audit_log table:
  id | action | details | admin_id | timestamp | user_affected
  
  Examples:
  1 | banned_content | "phrase: 'hate_word'" | sysop | 2026-03-15 | NULL
  2 | user_timeout | "session_id_xyz" | sysop | 2026-03-15 | NULL
  3 | bulletin_created | "title: 'Rules'" | sysop | 2026-03-15 | NULL
  4 | device_banned | "mac_address_***" | sysop | 2026-03-15 | NULL

RETENTION:
- Persistent (record of what admins did)
- Never deleted (accountability)
- Not visible to users (privacy)
- Available for admin review/appeal
```

---

## Part 8: First Load: Admin Setup vs Community Rules

### **First Boot Checklist**

```yaml
Step 1: Admin Password
  ├─ Set strong password
  ├─ Store securely
  └─ Can change later in dashboard

Step 2: Community Rules
  ├─ Edit bulletin board with house rules
  ├─ Make content filtering choices
  ├─ Set retention policy
  └─ Document why (for transparency)

Step 3: Access Settings
  ├─ Open (neighbors just join)
  ├─ Passcode (share via QR/message)
  └─ Approved (whitelist on demand)

Step 4: Moderation Setup
  ├─ Decide: content banning? session timeouts? device bans?
  ├─ Add initial banned words/patterns (optional)
  ├─ Set thresholds (5 violations = timeout)
  └─ Document rules publicly

Step 5: Privacy Guarantee
  ├─ Post privacy policy/disclaimer
  ├─ Setup appears on first user join
  ├─ Users must acknowledge
  └─ Admin can change anytime + notify

Step 6: Launch
  ├─ Test with friends
  └─ Go live!
```

---

## Part 9: Recommended Settings for Small Communities

### **BEST PRACTICE CONFIGURATION FOR 10-30 PERSON NEIGHBORHOOD**

```yaml
Privacy:
  Mode: FULL PRIVACY (messages deleted on disconnect)
  Rationale: Maximum privacy, trust-based moderation

Access Control:
  Type: PASSCODE
  Passcode: [shared via QR code or SMS]
  Rationale: Keeps out drive-bys, easy to reset if leaked

User Accounts:
  Type: ANONYMOUS (no login, optional usernames)
  Rationale: Instant access, no tracking infrastructure

Moderation:
  Type: HYBRID
  
  Tier 1 (Auto):
    - Content filter: enable curse words → [moderative]
    - Rate limit: 5 messages/10 sec
  
  Tier 2 (Admin action):
    - Session timeout: 24 hours for repeated abuse
  
  Tier 3 (Last resort):
    - Device ban: MAC address block on serious incidents

Data Retention:
  Admin view: Live chat only
  History: NONE (full privacy mode)
  Logs: Admin actions permanent (accountability)

Transparency:
  Disclaimer: Shown on first join
  Rules: Posted as bulletin
  Moderation: Appeals available to users
  Passcode: Can reset if compromised
```

---

## Part 10: FAQ for Admin

### **Q: What if someone is really toxic?**
A: Tier responses:
1. Content gets filtered automatically ✓
2. Try talking to them (you know them!)
3. Session timeout (24hr → they're off)
4. If they return + persist: Device ban (MAC)
5. If they get new device: Update passcode (kick everyone, reshare)

### **Q: Can I see old messages as admin?**
A: Depends on mode:
- **Full Privacy**: NO (deleted on disconnect)
- **Hybrid**: YES (last 7 days visible)
- **Persistent**: YES (all history)

### **Q: What if I forget the admin password?**
A: The device needs to be reset (no recovery). This is intentional privacy design. Alternative: recover the encrypted config file if stored.

### **Q: Can users be identified later?**
A: NO. Session IDs are not logged. In full privacy mode, no record exists. In hybrid/persistent, messages are saved but not linked to identity.

### **Q: What about GDPR/legal liability?**
A: 
- Full Privacy Mode: No user data = minimal liability ✓
- Hybrid: Delete after 7 days = GDPR compliant ✓
- Persistent: Need explicit consent policy (advisory: consult lawyer)

### **Q: Can I export data as admin?**
A: 
- Full Privacy: Nothing to export (encrypted, in-memory)
- Hybrid/Persistent: Can export database → CSV of messages
  (But this would violate privacy promise—don't do it)

### **Q: Multiple admins?**
A: Not recommended for <30 people. If needed:
- Each gets separate admin password
- All actions logged with which admin did it
- Shared responsibility/transparency

### **Q: How do I update the passcode?**
A: Admin can generate new passcode via dashboard.
- Old passcode becomes invalid
- Send new passcode to users via separate channel
- Old connections dropped on next interaction

---

## Part 11: Security vs Privacy Trade-offs

| Feature | Privacy Impact | Security Impact | Recommendation |
|---------|----------------|-----------------|-----------------|
| **Full Privacy Mode** | ✅ Excellent | ⚠️ Hard to moderate | Default for <30 |
| **Ephemeral Messages** | ✅ Excellent | ✅ Good | Use 7-day default |
| **No IP Logging** | ✅ Excellent | ⚠️ Can't trace abuse source | Accept as trade-off |
| **Anonymous Accounts** | ✅ Excellent | ⚠️ Can't ban individuals | Content-ban instead |
| **Passcode Access** | ⚠️ Limits privacy | ✅ Prevents outsiders | Worth it |
| **Admin Audit Log** | ✅ Good (admin-only) | ✅ Excellent (transparency) | Keep it |
| **Device Banning** | ⚠️ Tracks MAC | ✅ Stops repeat abuse | Use as escalation only |
| **Content Filtering** | ✅ Excellent | ✅ Good | Always on |

**Bottom Line**: For small communities, trust > tech. Focus on transparency, not surveillance.

---

## Implementation Order

1. **First**: Admin setup on first load ← START HERE
2. **Then**: Privacy mode selection during setup
3. **Then**: User account decisions (anonymous default)
4. **Then**: Passcode access control (optional)
5. **Then**: Content banning + session timeouts
6. **Then**: Device banning (escalation only)
7. **Then**: Privacy disclaimer + consent flow
8. **Finally**: Audit log for admin actions

---

**This framework balances:**
✅ Privacy (no tracking, ephemeral by default)  
✅ Security (admin can moderate abuse)  
✅ Community (trust-based, transparent)  
✅ Simplicity (admin picks once, works forever)


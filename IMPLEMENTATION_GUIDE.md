# 🔧 Implementation Guide - Privacy-First Design

> **For developers starting Phase 1 implementation**

---

## Quick Decisions Summary

| Decision | Design | Why |
|----------|--------|-----|
| **First Boot** | 5-step wizard | Admin decides privacy level once, lock it in |
| **Default Privacy** | Full Privacy (ephemeral) | No tracking possible if no data stored |
| **Accounts** | Anonymous + optional nickname | Zero friction, maximum privacy |
| **Moderation** | Content-based, escalate to timeouts | Don't track people, track behavior |
| **Access** | Passcode optional | Keeps out drive-bys, easy to reset |
| **Transparency** | Privacy disclaimer on join | Consent + clear expectations |
| **Audit** | Admin actions logged (permanent) | Accountability, never delete |

---

## Phase 1 Week-by-Week Implementation

### Week 1: Setup Wizard UI

**Goal:** Admin completes setup in <3 minutes

#### Step 1: Admin Password
```html
<form id="setup-step-1">
  <h2>Set Admin Password</h2>
  <p>This is the ONLY password needed.<br>
     Users do NOT need to login.</p>
  
  <input type="password" id="admin-pwd" placeholder="Admin Password" required>
  <input type="password" id="admin-pwd-confirm" placeholder="Confirm" required>
  <small>Use a strong password. Only admins need this.</small>
  
  <button type="button" onclick="next_wizard_step(2)">Next</button>
</form>
```

#### Step 2: Privacy Mode
```html
<form id="setup-step-2">
  <h2>Privacy Settings</h2>
  <p>How should we handle chat history?</p>
  
  <label>
    <input type="radio" name="privacy" value="full" checked>
    <strong>FULL PRIVACY (Recommended)</strong><br>
    ✓ Messages deleted when user disconnects<br>
    ✓ No permanent record<br>
    → Why: True privacy, less liability
  </label>
  
  <label>
    <input type="radio" name="privacy" value="hybrid">
    <strong>HYBRID (7-day retention)</strong><br>
    ✓ Messages auto-delete after 7 days<br>
    ✓ Balance privacy + reference<br>
    → Why: Best of both
  </label>
  
  <label>
    <input type="radio" name="privacy" value="persistent">
    <strong>PERSISTENT (Full history)</strong><br>
    ✓ Messages saved permanently<br>
    → Why: Useful for Q&A communities
  </label>
  
  <button type="button" onclick="prev_wizard_step(1)">Back</button>
  <button type="button" onclick="next_wizard_step(3)">Next</button>
</form>
```

#### Step 3: User Accounts
```html
<form id="setup-step-3">
  <h2>User Accounts</h2>
  <p>Do users need accounts to chat?</p>
  
  <label>
    <input type="radio" name="accounts" value="anonymous" checked>
    <strong>ANONYMOUS ONLY</strong><br>
    ✓ No accounts needed<br>
    ✓ Lowest friction, most private<br>
    ✗ Harder to ban abusers
  </label>
  
  <label>
    <input type="radio" name="accounts" value="optional">
    <strong>OPTIONAL ACCOUNTS</strong><br>
    ✓ Users can register (or stay anonymous)<br>
    ✓ Can ban specific user accounts
  </label>
  
  <!-- Don't offer REQUIRED—violates privacy -->
  
  <button type="button" onclick="prev_wizard_step(2)">Back</button>
  <button type="button" onclick="next_wizard_step(4)">Next</button>
</form>
```

#### Step 4: Moderation
```html
<form id="setup-step-4">
  <h2>Moderation & Abuse Response</h2>
  <p>What can admins do if someone misbehaves?</p>
  
  <label>
    <input type="radio" name="moderation" value="hybrid" checked>
    <strong>HYBRID (Recommended)</strong>
    <ul>
      <li>Start: Auto-filter offensive content</li>
      <li>Escalate: Timeout user for 24 hours</li>
      <li>Last resort: Device ban (MAC address)</li>
    </ul>
    ✓ Balances privacy + effective moderation
  </label>
  
  <label>
    <input type="radio" name="moderation" value="content-only">
    <strong>CONTENT FILTERING ONLY</strong>
    <ul>
      <li>Only auto-filter bad content</li>
      <li>No user or device tracking</li>
    </ul>
    ✓ Maximum privacy, but less effective
  </label>
  
  <button type="button" onclick="prev_wizard_step(3)">Back</button>
  <button type="button" onclick="next_wizard_step(5)">Next</button>
</form>
```

#### Step 5: Access Control
```html
<form id="setup-step-5">
  <h2>Access Control</h2>
  <p>How should people join your community?</p>
  
  <label>
    <input type="radio" name="access" value="open">
    <strong>OPEN</strong><br>
    ✓ Anyone on WiFi can join<br>
    ✗ Strangers can join without verification
  </label>
  
  <label>
    <input type="radio" name="access" value="passcode" checked>
    <strong>PASSCODE (Recommended)</strong><br>
    ✓ Must know passcode to join<br>
    ✓ Easy to share, easy to reset
  </label>
  
  <label>
    <input type="radio" name="access" value="approved">
    <strong>ADMIN-APPROVED</strong><br>
    ✓ Admin manually approves each user<br>
    ✗ Slowest setup
  </label>
  
  <!-- If passcode selected, show input -->
  <div id="passcode-input" style="display:none;">
    <input type="text" id="passcode" placeholder="Community Passcode">
    <small>Share this with neighbors via SMS, QR code, or word-of-mouth</small>
  </div>
  
  <button type="button" onclick="prev_wizard_step(4)">Back</button>
  <button type="button" onclick="save_and_complete()">Complete Setup</button>
</form>
```

**Backend (Flask):**
```python
@app.route('/setup/wizard/<int:step>', methods=['POST'])
@no_auth_required
def wizard_step(step):
    """Handle wizard steps during initial setup"""
    
    data = request.json
    config = get_or_create_config()
    
    if step == 1:
        # Admin password
        config['admin_password_hash'] = hash_password(data['password'])
    
    elif step == 2:
        # Privacy mode
        config['privacy_mode'] = data['privacy']  # full, hybrid, persistent
        if data['privacy'] != 'full':
            # Create messages table if needed
            db_init_messages_table()
    
    elif step == 3:
        config['account_system'] = data['accounts']  # anonymous, optional
    
    elif step == 4:
        config['moderation_levels'] = data['moderation']  # hybrid, content-only
    
    elif step == 5:
        config['access_control'] = data['access']  # open, passcode, approved
        if data['access'] == 'passcode':
            config['passcode_hash'] = hash_password(data['passcode'])
    
    if step == 5:
        config['setup_complete'] = True
        config['setup_complete_at'] = datetime.now()
    
    save_config(config)
    return {'status': 'ok', 'next_step': step + 1}
```

---

### Week 2: Privacy Modes

#### Full Privacy Mode (Default)

**Key Design:** Don't persist messages to database at all.

```python
# app.py
MESSAGE_STORAGE = {}  # In-memory only, wiped on disconnect

class PrivacyModeHandler:
    def __init__(self, mode):
        self.mode = mode
    
    def save_message(self, session_id, nickname, text):
        """Save message according to privacy mode"""
        
        if self.mode == 'full_privacy':
            # Only in-memory
            if session_id not in MESSAGE_STORAGE:
                MESSAGE_STORAGE[session_id] = []
            MESSAGE_STORAGE[session_id].append({
                'nickname': nickname,
                'text': text,
                'timestamp': datetime.now()
            })
            # NOT written to database
        
        elif self.mode == 'hybrid':
            # Write to DB with TTL
            db.execute("""
                INSERT INTO messages (text, nickname, created_at, expires_at)
                VALUES (?, ?, ?, datetime('now', '+7 days'))
            """, (text, nickname, datetime.now()))
            db.commit()
        
        elif self.mode == 'persistent':
            # Write to DB, no expiration
            db.execute("""
                INSERT INTO messages (text, nickname, created_at)
                VALUES (?, ?, ?)
            """, (text, nickname, datetime.now()))
            db.commit()
    
    def get_message_history(self, session_id):
        """Get history for admin dashboard"""
        
        if self.mode == 'full_privacy':
            # Only return current session's messages
            return MESSAGE_STORAGE.get(session_id, [])
        
        elif self.mode in ['hybrid', 'persistent']:
            # Return from database
            rows = db.execute("""
                SELECT nickname, text, created_at 
                FROM messages 
                WHERE expires_at IS NULL OR expires_at > now()
                ORDER BY created_at DESC 
                LIMIT 100
            """).fetchall()
            return [dict(row) for row in rows]
    
    def on_disconnect(self, session_id):
        """Clean up on session end"""
        
        if self.mode == 'full_privacy':
            # Clear from memory
            MESSAGE_STORAGE.pop(session_id, None)
        
        # Hybrid/persistent: keep data

# Initialize at startup
privacy_handler = PrivacyModeHandler(config['privacy_mode'])
```

#### Database Schema

```sql
-- Bulletins (always persisted, admin-only)
CREATE TABLE bulletins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT DEFAULT 'admin',
  updated_at TIMESTAMP
);

-- Sessions (ephemeral)
CREATE TABLE sessions (
  session_id TEXT PRIMARY KEY,
  nickname TEXT NOT NULL,
  connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  disconnected_at TIMESTAMP
  -- NO user_id, NO ip_address
);

-- Messages (only if HYBRID or PERSISTENT mode)
-- Created dynamically only if needed
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP  -- NULL = never delete
);

-- Banned content patterns
CREATE TABLE banned_content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pattern_type TEXT,  -- exact, substring, regex
  pattern TEXT NOT NULL,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP
);

-- Config (setup choices)
CREATE TABLE config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  encrypted BOOLEAN DEFAULT FALSE
);
```

---

### Week 3-4: Accounts & Messaging

#### Anonymous Authentication

```python
@app.route('/api/auth/join', methods=['POST'])
def join_chat():
    """Anonymous join - user just picks nickname"""
    
    data = request.json
    nickname = bleach.clean(data.get('nickname', 'Guest'))
    
    # Validate passcode if required
    if config['access_control'] == 'passcode':
        passcode = request.json.get('passcode')
        if not verify_passcode(passcode):
            return {'error': 'Invalid passcode'}, 401
    
    # Create session (no user account)
    session_id = str(uuid4())
    session['session_id'] = session_id
    
    # Store session (not user)
    db.execute("""
        INSERT INTO sessions (session_id, nickname, connected_at)
        VALUES (?, ?, ?)
    """, (session_id, nickname, datetime.now()))
    db.commit()
    
    return {
        'session_id': session_id,
        'nickname': nickname,
        'message': 'Welcome!'
    }
```

#### WebSocket Message Broadcasting

```python
@app.websocket('/ws/chat')
def chat_ws(ws):
    """WebSocket handler for chat"""
    
    session_id = request.args.get('session_id')
    
    while True:
        try:
            data = ws.receive(timeout=30)
            if data is None:
                break
            
            message_data = json.loads(data)
            
            # Sanitize + check for banned content
            text = bleach.clean(message_data['text'])
            
            if is_banned_content(text):
                text = "[moderated]"
                # Count violation
                increment_violation_counter(session_id)
            
            # Save (based on privacy mode)
            privacy_handler.save_message(
                session_id,
                session_id_to_nickname(session_id),
                text
            )
            
            # Broadcast to all clients
            broadcast_message({
                'nickname': session_id_to_nickname(session_id),
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            break
    
    # On disconnect
    privacy_handler.on_disconnect(session_id)
```

---

## Configuration File Example

```yaml
# After setup wizard completes
setup_complete: true
setup_version: "1.0"
setup_completed_at: "2026-03-15T10:30:00"

# Admin
admin_password_hash: "$2b$12$KixzauVaIZ5NHIHHIA1R7O/kSdM.pFYXbQ3rxHrlElElXZbBqLUCK"

# Privacy
privacy_mode: "full_privacy"
message_retention_days: null  # only if hybrid: 7, if persistent: null

# Users
account_system: "anonymous"

# Access
access_control: "passcode"
passcode_hash: "$2b$12$abcdef123456..."

# Moderation
moderation_levels: ["content_filter", "session_timeout", "device_ban"]
violation_threshold: 5
violation_window_minutes: 10
session_timeout_hours: 24

# Community
community_name: "Elm Street Neighbors"
admin_contact: "(555) 123-4567"
community_rules: "Be respectful, no spam"

# Logging
audit_logging: true
database_file: "/var/lib/neighborhood_bbs/bbs.db"
```

---

## Testing Plan

### Unit Tests (Week 1)
```python
def test_privacy_mode_full():
    """Verify messages not persisted in full privacy mode"""
    handler = PrivacyModeHandler('full_privacy')
    handler.save_message('session1', 'Alice', 'Hello')
    
    # Should be in memory
    assert 'session1' in MESSAGE_STORAGE
    
    # Should NOT be in database
    rows = db.execute("SELECT * FROM messages WHERE nickname='Alice'").fetchall()
    assert len(rows) == 0

def test_content_filtering():
    """Verify banned content gets moderated"""
    add_banned_pattern('hate_word', 'exact')
    
    result = check_and_filter_message('I say hate_word')
    assert '[moderated]' in result

def test_session_timeout():
    """Verify session timeout after violations"""
    for i in range(5):
        increment_violation_counter('session1')
    
    assert is_session_timed_out('session1') == True
```

### Integration Tests (Week 2-3)
```python
def test_full_setup_flow():
    """User completes setup wizard"""
    
    # Step 1: Admin password
    resp = client.post('/setup/wizard/1', json={
        'password': 'MyStrongPass123!'
    })
    assert resp.status_code == 200
    
    # Step 2-5: Other steps...
    
    # Verify config saved
    config = get_config()
    assert config['setup_complete'] == True
    assert config['privacy_mode'] == 'full_privacy'
```

---

## Common Pitfalls to Avoid

### ❌ DON'T Track User IPs
```python
# WRONG:
db.execute("INSERT INTO messages (ip_address) VALUES (?)", (request.remote_addr,))

# RIGHT:
# Don't store IP at all. If needed for throttling, use in-memory hash.
```

### ❌ DON'T Store User IDs in Messages
```python
# WRONG:
db.execute("INSERT INTO messages (user_id, text) VALUES (?, ?)", (user.id, text))

# RIGHT:
# Store only nickname (not unique, not tracked)
db.execute("INSERT INTO messages (nickname, text) VALUES (?, ?)", (nickname, text))
```

### ❌ DON'T Link Sessions to Users
```python
# WRONG:
session['user_id'] = user.id

# RIGHT (for anonymous):
session['session_id'] = uuid4()  # Untrackable
```

### ❌ DON'T Auto-Delete Audit Logs
```python
# WRONG:
db.execute("DELETE FROM audit_log WHERE created_at < now() - interval 30 days")

# RIGHT:
# Audit logs are permanent (accountability)
```

---

## Next Steps

1. **Implement Week 1** → Setup wizard UI
2. **Test thoroughly** → Full privacy mode validated
3. **Deploy to test hardware** → Raspberry Pi
4. **Beta test** → Real neighbors try it
5. **Phase 2** → Add moderation

---

**Questions? See:**
- [PRIVACY_SECURITY_FRAMEWORK.md](PRIVACY_SECURITY_FRAMEWORK.md) — Design rationale
- [ROADMAP.md](ROADMAP.md) — Full 18-week plan


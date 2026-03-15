# 🗺️ ROADMAP - Neighborhood BBS (90-Day Implementation)

## Vision

Neighborhood BBS is a **privacy-first, trust-based community communication platform** for 10-30 person neighborhoods. It runs on local WiFi, requires no cloud, zero tracking, and gives admins one-time setup instead of ongoing management.

**Guiding Principles:**
- ✅ Privacy-first (no unnecessary data collection)
- ✅ Trust-based moderation (designed for small communities)
- ✅ Admin-driven first-load setup (5-question wizard)
- ✅ Ephemeral messages by default (full privacy mode)
- ✅ Simple deployment (runs on Raspberry Pi or old laptop)

---

## 📅 PHASE 1: Admin Setup & Privacy Modes (Weeks 1-4)

**Goal:** Admin runs setup once. Chat works, messages are private.

### Week 1: Admin Onboarding UX
- [ ] Create 5-step setup wizard
  - [ ] Admin password selection
  - [ ] Privacy mode choice (full/hybrid/persistent + explanations)
  - [ ] User account type (anonymous vs optional)
  - [ ] Moderation escalation levels
  - [ ] Access control (open/passcode/approved)

- [ ] Build wizard UI in Flask/Jinja
  - [ ] Progressive flow with "Learn More" on each step
  - [ ] Review summary before saving
  - [ ] Store configuration in SQLite (encrypted)

**Deliverable:** Admin can finish setup in <3 minutes

### Week 2: Privacy Modes
- [ ] **FULL PRIVACY (Default)**
  - [ ] Messages in RAM during session only
  - [ ] No database writes for chat
  - [ ] Bulletins always persisted (admin announcements)
  - [ ] On disconnect: memory cleared

- [ ] **HYBRID (7-day retention)**
  - [ ] Messages saved to database
  - [ ] Auto-delete older than 7 days
  - [ ] For communities wanting reference + privacy

- [ ] **PERSISTENT (Full history)**
  - [ ] All messages saved permanently
  - [ ] For Q&A/support communities
  - [ ] Requires explicit privacy agreement

- [ ] Database schema:
  ```sql
  CREATE TABLE config (key TEXT UNIQUE, value TEXT);
  CREATE TABLE bulletins (id INTEGER PRIMARY KEY, title TEXT, content TEXT, created_at TIMESTAMP);
  CREATE TABLE sessions (session_id TEXT PRIMARY KEY, nickname TEXT, connected_at TIMESTAMP);
  -- No user_id, no IP logging
  -- messages table only created if HYBRID/PERSISTENT mode selected
  ```

**Deliverable:** Admin chooses privacy level once, system respects it forever

### Week 3: User Accounts (Anonymous Default)
- [ ] Anonymous-only authentication
  - [ ] No password login
  - [ ] User picks nickname on connect
  - [ ] Multiple people can use same nickname
  - [ ] Session UUID per connection
  - [ ] Can change nickname mid-chat

- [ ] Optional accounts (backend only, for future phases)
  - [ ] Username/password schema (if admin later chooses optional accounts)
  - [ ] Don't build UI yet

**Deliverable:** Users join with just nickname, no tracking across sessions

### Week 4: Chat & Bulletins
- [ ] Basic messaging
  - [ ] WebSocket broadcast
  - [ ] Format: {nickname, text, timestamp}
  - [ ] Auto-delete on disconnect (full privacy mode)

- [ ] Bulletins system
  - [ ] Admin creates announcements (always persisted)
  - [ ] Users see on startup
  - [ ] Examples: "House Rules", "Community Hours", "Admin Contact"

- [ ] Admin dashboard v1
  - [ ] Password-protected
  - [ ] Live chat view (no history)
  - [ ] Connected users count
  - [ ] Create/edit bulletins

**Deliverable:** Working chat app, privacy respected by default

---

## 📅 PHASE 2: Moderation (Weeks 5-7)

**Goal:** Admin can moderate without tracking individuals.

### Week 5: Content-Based Filtering
- [ ] Banned content patterns
  - [ ] Table: `banned_content` (pattern, type, reason)
  - [ ] Types: exact, substring, regex

- [ ] Filter middleware
  - [ ] On message: check against patterns
  - [ ] Match → replace with "[moderated]"
  - [ ] Log: only pattern matched (not user)
  - [ ] Broadcast moderated message

- [ ] Admin UI
  - [ ] Add/remove patterns
  - [ ] View match count (analytics, not user tracking)
  - [ ] Automatic filtering (always on)

**Deliverable:** Swear words → auto-moderated

### Week 6: Session-Based Timeouts
- [ ] Violation counter
  - [ ] Threshold: 5 violations in 10 minutes
  - [ ] Action: Disconnect user for 24 hours

- [ ] Timeout table
  - [ ] Stores: session_id, reason, timeout_until
  - [ ] Auto-expires after duration
  - [ ] No permanent record

- [ ] Admin actions
  - [ ] Manual timeout trigger
  - [ ] Cancel timeout early (second chance)
  - [ ] View active timeouts

**Deliverable:** Repeat abusers get cooldown, can rejoin day later

### Week 7: Device-Based Banning (Escalation)
- [ ] MAC address detection
  - [ ] Get from WiFi layer (if available)
  - [ ] Hash for privacy (don't store plain)
  - [ ] Store hashes in `banned_devices` table

- [ ] Ban enforcement
  - [ ] On WebSocket connect: check hash
  - [ ] If banned: reject connection
  - [ ] Admin can review/remove

- [ ] Escalation workflow
  - [ ] Admin Dashboard: "Ban Device" button (emergencies only)
  - [ ] Requires reason + optional expiration
  - [ ] Hard stop for serious abuse

**Deliverable:** Last-resort tool for persistent abusers

---

## 📅 PHASE 3: Access Control (Weeks 8-9)

**Goal:** Can restrict to verified neighbors (passcode/approval).

### Week 8: Passcode-Based Entry
- [ ] Config at setup
  - [ ] Admin chooses: open / passcode / approved
  - [ ] If passcode: enters one at setup time
  - [ ] Hashed + stored

- [ ] Join flow
  - [ ] Landing page: asks for passcode (if enabled)
  - [ ] User enters
  - [ ] Verify against hash
  - [ ] Set session as authenticated

- [ ] Admin reset passcode
  - [ ] Generate new passcode
  - [ ] All old sessions kicked
  - [ ] Share new code via SMS/paper flyer

**Deliverable:** Neighborhoods can restrict to known people only

### Week 9: Admin Approval System (Optional)
- [ ] Whitelist table (for approved mode)
  - [ ] Manual approval workflow
  - [ ] Admin approves new users
  - [ ] Not default (only if chosen at setup)

**Deliverable:** Option for controlled-access communities

---

## 📅 PHASE 4: Privacy Transparency (Weeks 10-12)

**Goal:** Clear privacy commitment + admin accountability.

### Week 10: Privacy Disclaimer & Consent
- [ ] Disclaimer text (from PRIVACY_SECURITY_FRAMEWORK.md)
  - [ ] Add to database as bulletin
  - [ ] Show on first join
  - [ ] Customizable by admin

- [ ] Consent flow
  - [ ] "I understand these privacy terms" checkbox
  - [ ] Must acknowledge before join
  - [ ] Store fact of acknowledgment (not identity)

**Deliverable:** Users know what data isn't collected

### Week 11: Admin Audit Log
- [ ] Audit log table
  ```sql
  CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    action TEXT,          -- "banned_content", "timeout", "device_ban"
    details JSON,
    admin_user TEXT,
    timestamp TIMESTAMP
  );
  ```

- [ ] Log ALL admin actions
  - [ ] Content bans, timeouts, device bans
  - [ ] Bulletin edits, config changes
  - [ ] Never deleted (permanent accountability)

- [ ] Admin view
  - [ ] Dashboard: "Recent Admin Actions"
  - [ ] Can export audit log (transparency)
  - [ ] Permanent record

**Deliverable:** Complete record of what admins did (accountability)

### Week 12: Dashboard Analytics
- [ ] Allowed metrics (aggregate only)
  - [ ] Connected users count
  - [ ] Messages sent today (total)
  - [ ] Avg message length
  - [ ] Most filtered patterns (pattern-level, not user)

- [ ] Forbidden metrics
  - [ ] "User X sent Y messages"
  - [ ] "User joined at 3:15pm"
  - [ ] Device IDs
  - [ ] ANY individual tracking

**Deliverable:** Admin dashboard shows community health, not surveillance

---

## 📅 PHASE 5: Polish (Weeks 13-15)

### Week 13: Message Retention Options (if chosen)
- [ ] HYBRID mode implementation (if admin selected)
  - [ ] Message database writes + 7-day TTL
  - [ ] Auto-delete nightly
  - [ ] API for user deletion (GDPR)

### Week 14: Message Search UI (if retention enabled)
- [ ] Admin message browser
  - [ ] Timeline view
  - [ ] Keyword search (if persistent mode)
  - [ ] Date range filter

- [ ] Delete operations
  - [ ] Admin can delete messages
  - [ ] Users can request deletion of own
  - [ ] Log all deletions

### Week 15: UI Polish
- [ ] Responsive design (mobile)
- [ ] Dark mode option
- [ ] Accessibility (WCAG AA)
- [ ] Error messages + loading states

---

## 📅 PHASE 6: Documentation & Launch (Weeks 16-18)

### Week 16: Documentation
- [ ] Admin setup guide (printable)
- [ ] User FAQ
- [ ] Troubleshooting
- [ ] Privacy policy template

### Week 17: Deployment Packages
- [ ] Docker image
- [ ] systemd service file
- [ ] Installation script
- [ ] Setup guide for different hardware

### Week 18: Testing & v1.0 Release
- [ ] Integration tests
- [ ] Load testing (50+ concurrent)
- [ ] Beta test with real community
- [ ] Public release v1.0

---

## ✅ Success Criteria

**End of Phase 1 (Week 4):**
- ✅ Admin runs setup once, chat works
- ✅ Messages private, auto-deleted

**End of Phase 2 (Week 7):**
- ✅ Admin can moderate without user tracking
- ✅ Progressive escalation (content → timeout → device)

**End of Phase 3 (Week 9):**
- ✅ Can restrict to verified neighbors
- ✅ Passcode-based access works

**End of Phase 4 (Week 12):**
- ✅ Users see privacy promise
- ✅ Admin actions logged + accountable

**End of Phase 6 (Week 18):**
- ✅ Production-ready, deployable
- ✅ Easy for non-tech admins

---

## 💾 Tech Stack

- **Backend**: Python Flask 3.x + WebSocket
- **Database**: SQLite (encrypted config + optional message storage)
- **Frontend**: HTML5 + Vanilla JS (no build step)
- **Server**: systemd or Docker
- **Hardware**: Raspberry Pi, Zima Board, or old laptop

---

## 🚀 Launch Playbook

1. Admin installs: `docker run neighborhood-bbs`
2. Visits: `http://localhost:8080`
3. Completes 5-question setup (3 min)
4. Gets admin dashboard: `http://localhost:8080/admin`
5. Shares link: `http://[house_ip]:8080`
6. Neighbors join: Pick nickname → chat
7. **Community live**: Private, moderated, transparent

---

## 📚 Reference Documents

- **[PRIVACY_SECURITY_FRAMEWORK.md](PRIVACY_SECURITY_FRAMEWORK.md)** — Complete privacy design + moderation strategies
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Technical design (to be created)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Installation + setup (to be created)

---

**Last Updated:** March 15, 2026  
**Status:** Planning Phase 1 Implementation  
**Lead:** Neighborhood BBS Community

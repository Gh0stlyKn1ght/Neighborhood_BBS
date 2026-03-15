#!/usr/bin/env python3
"""
Neighborhood BBS - ZimaBoard Flask + WebSocket
Local AP captive portal with persistent bulletins and live chat
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sock import Sock
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
sock = Sock(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'bbs.db')
MAX_MESSAGE_LENGTH = 240
RATE_LIMIT_MESSAGES = 5
RATE_LIMIT_WINDOW = 10  # seconds

# Global chat state
connected_clients = set()
chat_history = []


def init_db():
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Bulletins table
    c.execute('''CREATE TABLE IF NOT EXISTS bulletins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        handle TEXT NOT NULL,
        text TEXT NOT NULL,
        is_system INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Rate limiting table
    c.execute('''CREATE TABLE IF NOT EXISTS rate_limits (
        session_id TEXT PRIMARY KEY,
        message_count INTEGER DEFAULT 0,
        window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Check if admin exists, create default if not
    c.execute("SELECT COUNT(*) FROM admin WHERE username='sysop'")
    if c.fetchone()[0] == 0:
        default_pw = hashlib.sha256(b'gh0stly').hexdigest()
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
                 ('sysop', default_pw))
    
    # Load default bulletins if empty
    c.execute("SELECT COUNT(*) FROM bulletins")
    if c.fetchone()[0] == 0:
        bulletins = [
            ("Welcome to Neighborhood BBS", "Local network only. No internet. Neighbors only."),
            ("Rules", "Be cool. No spam. No hate. Keep it under 240 chars."),
            ("About", "ESP8266 + ZimaBoard. Captive portal. WiFi mesh ready."),
        ]
        for title, text in bulletins:
            c.execute("INSERT INTO bulletins (title, text) VALUES (?, ?)", (title, text))
    
    conn.commit()
    conn.close()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(pw):
    """Hash password with SHA-256."""
    return hashlib.sha256(pw.encode()).hexdigest()


def check_rate_limit(session_id):
    """Check if session is rate limited."""
    conn = get_db()
    c = conn.cursor()
    now = datetime.now()
    
    c.execute("SELECT message_count, window_start FROM rate_limits WHERE session_id = ?",
             (session_id,))
    row = c.fetchone()
    
    if row is None:
        c.execute("INSERT INTO rate_limits (session_id, message_count, window_start) VALUES (?, ?, ?)",
                 (session_id, 1, now))
        conn.commit()
        conn.close()
        return True
    
    message_count, window_start = row
    window_start = datetime.fromisoformat(window_start)
    
    if (now - window_start).total_seconds() > RATE_LIMIT_WINDOW:
        # Window expired, reset
        c.execute("UPDATE rate_limits SET message_count = 1, window_start = ? WHERE session_id = ?",
                 (now, session_id))
        conn.commit()
        conn.close()
        return True
    
    if message_count >= RATE_LIMIT_MESSAGES:
        conn.close()
        return False
    
    c.execute("UPDATE rate_limits SET message_count = message_count + 1 WHERE session_id = ?",
             (session_id,))
    conn.commit()
    conn.close()
    return True


def require_admin(f):
    """Decorator to require admin session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# Routes

@app.route('/')
def index():
    """Landing page with bulletins."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bulletins ORDER BY created_at DESC LIMIT 10")
    bulletins = c.fetchall()
    c.execute("SELECT COUNT(*) FROM messages WHERE is_system = 0")
    msg_count = c.fetchone()[0]
    conn.close()
    
    return render_template('index.html', bulletins=bulletins, msg_count=msg_count)


@app.route('/chat')
def chat():
    """Chat room interface."""
    return render_template('chat.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username', 'sysop')
        password = request.form.get('password', '')
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, password FROM admin WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        
        if row and row['password'] == hash_password(password):
            session['admin_id'] = row['id']
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/admin', methods=['GET'])
@require_admin
def admin_panel():
    """Admin dashboard."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bulletins ORDER BY created_at DESC")
    bulletins = c.fetchall()
    c.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    
    return render_template('admin.html', bulletins=bulletins, messages=messages)


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Logout admin."""
    session.pop('admin_id', None)
    return redirect(url_for('index'))


@app.route('/api/bulletins', methods=['GET'])
def api_bulletins():
    """Get all bulletins."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, text, created_at FROM bulletins ORDER BY created_at DESC")
    bulletins = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(bulletins)


@app.route('/api/messages/history', methods=['GET'])
def api_messages():
    """Get message history."""
    limit = request.args.get('limit', 50, type=int)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT handle, text, is_system, created_at FROM messages ORDER BY created_at DESC LIMIT ?",
             (limit,))
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Reverse to get chronological order
    messages.reverse()
    return jsonify(messages)


@app.route('/api/send', methods=['POST'])
def api_send():
    """REST API to send a message (for KITT integration)."""
    if not check_rate_limit(request.remote_addr):
        return jsonify({'error': 'Rate limited'}), 429
    
    data = request.get_json() or {}
    handle = data.get('handle', 'SYSTEM').upper()[:16]
    text = data.get('text', '')[:MAX_MESSAGE_LENGTH]
    
    if not handle or not text:
        return jsonify({'error': 'Missing handle or text'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (handle, text) VALUES (?, ?)", (handle, text))
    conn.commit()
    conn.close()
    
    # Broadcast via WebSocket
    broadcast_message(handle, text, system=False)
    
    return jsonify({'status': 'ok', 'handle': handle})


@app.route('/admin/bulletin/new', methods=['POST'])
@require_admin
def admin_new_bulletin():
    """Create new bulletin."""
    title = request.form.get('title', '')[:100]
    text = request.form.get('text', '')[:500]
    
    if not title or not text:
        return jsonify({'error': 'Missing title or text'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO bulletins (title, text) VALUES (?, ?)", (title, text))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/bulletin/<int:bid>/delete', methods=['POST'])
@require_admin
def admin_delete_bulletin(bid):
    """Delete bulletin."""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM bulletins WHERE id = ?", (bid,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/messages/clear', methods=['POST'])
@require_admin
def admin_clear_messages():
    """Clear all messages."""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE is_system = 0")
    conn.commit()
    conn.close()
    
    broadcast_message('*', 'Chat cleared by SYSOP', system=True)
    return redirect(url_for('admin_panel'))


@app.route('/admin/password/change', methods=['POST'])
@require_admin
def admin_change_password():
    """Change admin password."""
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    
    if not old_pw or not new_pw:
        return jsonify({'error': 'Missing password'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT password FROM admin WHERE id = ?", (session.get('admin_id'),))
    row = c.fetchone()
    
    if not row or row['password'] != hash_password(old_pw):
        conn.close()
        return jsonify({'error': 'Invalid old password'}), 401
    
    c.execute("UPDATE admin SET password = ? WHERE id = ?",
             (hash_password(new_pw), session.get('admin_id')))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})


# WebSocket handlers

def broadcast_message(handle, text, system=False):
    """Broadcast message to all connected clients."""
    payload = {
        'type': 'msg',
        'handle': handle,
        'text': text,
        'system': system,
        'timestamp': datetime.now().isoformat()
    }
    
    for client in connected_clients:
        try:
            client.send(json.dumps(payload))
        except Exception as e:
            app.logger.debug(f"Error broadcasting: {e}")


@sock.route('/ws')
def ws_handler(ws):
    """WebSocket handler for live chat."""
    session_id = secrets.token_hex(8)
    connected_clients.add(ws)
    
    try:
        # Send chat history on connect
        history_payload = {'type': 'history', 'messages': []}
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT handle, text, is_system FROM messages ORDER BY created_at DESC LIMIT 30")
        for row in c.fetchall():
            history_payload['messages'].insert(0, {
                'handle': row['handle'],
                'text': row['text'],
                'system': bool(row['is_system'])
            })
        conn.close()
        
        msg_count_text = "*** {} message(s) in history".format(len(history_payload['messages']))
        history_payload['messages'].insert(0, {
            'handle': '*',
            'text': msg_count_text,
            'system': True
        })
        
        ws.send(json.dumps(history_payload))
        
        # Main message loop
        while True:
            data = ws.receive()
            if not data:
                break
            
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            
            if payload.get('type') == 'nick_set':
                # Nick submission
                nick = payload.get('nick', '').strip()[:16]
                if not nick:
                    nick = f"ANON_{secrets.randbelow(1000):03d}"
                nick = ''.join(c for c in nick if c.isalnum() or c in '-_').upper()
                
                session['chat_nick'] = nick
                ws.send(json.dumps({
                    'type': 'nick_ok',
                    'nick': nick
                }))
            
            elif payload.get('type') == 'msg':
                if not check_rate_limit(session_id):
                    ws.send(json.dumps({
                        'type': 'error',
                        'text': 'Rate limited - 5 msgs per 10 sec'
                    }))
                    continue
                
                handle = session.get('chat_nick', 'ANON_000').upper()[:16]
                text = payload.get('text', '').strip()[:MAX_MESSAGE_LENGTH]
                
                if text:
                    # Save to DB
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO messages (handle, text) VALUES (?, ?)",
                             (handle, text))
                    conn.commit()
                    conn.close()
                    
                    # Broadcast
                    broadcast_message(handle, text, system=False)
    
    except Exception as e:
        app.logger.debug(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(ws)


@app.errorhandler(404)
def not_found(e):
    """Captive portal redirect for 404s."""
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    sock.run(app, host='0.0.0.0', port=5000, debug=False)

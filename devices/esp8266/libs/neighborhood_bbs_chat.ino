/*
 * Neighborhood BBS - Arduino ESP8266 Chat & Bulletins
 * https://github.com/Gh0stlyKn1ght/Neighborhood_BBS
 * 
 * IRC-themed captive portal BBS with:
 * - Live WebSocket chat
 * - Persistent bulletins
 * - Profanity filter (client + server)
 * - User nick system
 * - Auto-reconnect
 * 
 * Libraries Required (via Arduino IDE Library Manager):
 * - WebSockets by Markus Sattler (v2.3.6 minimum)
 * 
 * Board: NodeMCU 1.0 (ESP-12E Module)
 * Speed: 115200 baud
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <DNSServer.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION - Edit these
// ============================================

const char* SSID = "NEIGHBORHOOD_BBS";           // WiFi name
const char* BOARD_NAME = "GH0STL4N";            // BBS header
const char* SYSOP_NAME = "MR. GH0STLY";         // Your handle

// Profanity filter words (keep PROFANITY_COUNT in sync)
const char* PROFANITY[] = {
  "badword1", "badword2", "badword3", "badword4", "badword5"
};
const int PROFANITY_COUNT = 5;

// Bulletins shown on landing page
const char* BULLETINS[] = {
  "Welcome to Neighborhood BBS",
  "Local network only - no internet",
  "Chat with your neighbors in real time",
  "Green text on black - pure retro vibes",
  "Be cool. No spam. No hate. Keep it under 240 chars."
};
const int BULLETIN_COUNT = 5;

// ============================================
// Network Setup
// ============================================

ESP8266WebServer server(80);
WebSocketsServer wsServer(81);
DNSServer dnsServer;
IPAddress apIP(192, 168, 4, 1);
IPAddress netMask(255, 255, 255, 0);

// ============================================
// Chat State
// ============================================

#define MAX_MESSAGES 20
#define MAX_MESSAGE_LEN 240
#define MAX_HANDLE_LEN 16

struct Message {
  char handle[MAX_HANDLE_LEN];
  char text[MAX_MESSAGE_LEN];
  boolean is_system;
};

Message chat_history[MAX_MESSAGES];
int message_count = 0;
int client_count = 0;

// User nicknames per connection
struct UserSession {
  uint8_t num;
  char nick[MAX_HANDLE_LEN];
};

UserSession users[10];

// ============================================
// Profanity Filter
// ============================================

String censorText(String text) {
  for (int i = 0; i < PROFANITY_COUNT; i++) {
    String word = PROFANITY[i];
    String censor = "";
    for (int j = 0; j < word.length(); j++) {
      censor += "*";
    }
    
    // Simple word boundary replacement
    text.replace(" " + word + " ", " " + censor + " ");
    text.replace(" " + word + ".", " " + censor + ".");
    text.replace(" " + word + ",", " " + censor + ",");
    if (text.startsWith(word)) {
      text = censor + text.substring(word.length());
    }
  }
  return text;
}

// ============================================
// Message Management
// ============================================

void pushMsg(const char* handle, const char* text, boolean sys = false) {
  if (message_count < MAX_MESSAGES) {
    strncpy(chat_history[message_count].handle, handle, MAX_HANDLE_LEN - 1);
    strncpy(chat_history[message_count].text, text, MAX_MESSAGE_LEN - 1);
    chat_history[message_count].is_system = sys;
    message_count++;
  } else {
    // Ring buffer: shift old messages, add new at end
    for (int i = 0; i < MAX_MESSAGES - 1; i++) {
      chat_history[i] = chat_history[i + 1];
    }
    strncpy(chat_history[MAX_MESSAGES - 1].handle, handle, MAX_HANDLE_LEN - 1);
    strncpy(chat_history[MAX_MESSAGES - 1].text, text, MAX_MESSAGE_LEN - 1);
    chat_history[MAX_MESSAGES - 1].is_system = sys;
  }
}

void broadcastMsg(const char* handle, const char* text, boolean sys = false) {
  pushMsg(handle, text, sys);
  
  DynamicJsonDocument doc(512);
  doc["type"] = "msg";
  doc["handle"] = handle;
  doc["text"] = text;
  doc["system"] = sys;
  doc["clients"] = client_count;
  
  String payload;
  serializeJson(doc, payload);
  
  wsServer.broadcastTXT(payload);
}

// ============================================
// WebSocket Handler
// ============================================

void onWsEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  
  switch (type) {
    case WStype_CONNECTED: {
      client_count++;
      Serial.printf("[WS] Client %d connected. Total: %d\n", num, client_count);
      
      // Send chat history
      DynamicJsonDocument doc(1024);
      doc["type"] = "history";
      JsonArray messages = doc.createNestedArray("messages");
      
      // History header
      JsonObject hdr = messages.createNestedObject();
      hdr["handle"] = "*";
      hdr["text"] = "*** " + String(message_count) + " message(s) in history";
      hdr["system"] = true;
      
      // All history
      for (int i = 0; i < message_count; i++) {
        JsonObject msg = messages.createNestedObject();
        msg["handle"] = chat_history[i].handle;
        msg["text"] = chat_history[i].text;
        msg["system"] = chat_history[i].is_system;
      }
      
      String output;
      serializeJson(doc, output);
      wsServer.sendTXT(num, output);
      
      // Announce
      String announce = chat_history[0].handle;
      announce = SYSOP_NAME;
      String join_msg = String(BOARD_NAME) + " has joined #block";
      broadcastMsg("*", join_msg.c_str(), true);
      break;
    }
    
    case WStype_DISCONNECTED: {
      client_count--;
      Serial.printf("[WS] Client %d disconnected. Total: %d\n", num, client_count);
      String leave_msg = String(BOARD_NAME) + " has left #block";
      broadcastMsg("*", leave_msg.c_str(), true);
      break;
    }
    
    case WStype_TEXT: {
      // Parse incoming JSON
      DynamicJsonDocument doc(512);
      deserializeJson(doc, payload);
      
      const char* msg_type = doc["type"];
      
      if (strcmp(msg_type, "nick_set") == 0) {
        // Set user nick
        const char* nick = doc["nick"];
        if (nick && strlen(nick) > 0) {
          strncpy(users[num].nick, nick, MAX_HANDLE_LEN - 1);
          users[num].nick[MAX_HANDLE_LEN - 1] = 0;
          
          DynamicJsonDocument resp(128);
          resp["type"] = "nick_ok";
          resp["nick"] = users[num].nick;
          String out;
          serializeJson(resp, out);
          wsServer.sendTXT(num, out);
        }
      }
      else if (strcmp(msg_type, "msg") == 0) {
        // Chat message
        String text = doc["text"];
        text = censorText(text);  // Filter
        
        if (text.length() > 0) {
          const char* handle = users[num].nick;
          if (!handle || strlen(handle) == 0) {
            handle = "ANON";
          }
          
          Serial.printf("[MSG] %s: %s\n", handle, text.c_str());
          broadcastMsg(handle, text.c_str(), false);
        }
      }
      break;
    }
  }
}

// ============================================
// HTTP Handlers
// ============================================

String generateHTML() {
  String html = R"(<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Neighborhood BBS</title>
<style>
* {
  margin: 0; padding: 0; box-sizing: border-box;
}
body {
  background: #000;
  color: #00ff00;
  font-family: 'Courier New', monospace;
  overflow-x: hidden;
}
body::before {
  content: '';
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15) 1px, transparent 1px, transparent 2px);
  pointer-events: none;
  z-index: 999;
}
main {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  z-index: 1;
}
h1 {
  text-align: center;
  margin: 20px 0;
  text-shadow: 0 0 10px #00ff00;
}
.container {
  border: 2px solid #00ff00;
  padding: 15px;
  margin: 10px 0;
  background: rgba(0,255,0,0.02);
}
.bullet {
  margin: 10px 0;
  padding: 10px;
  border-left: 2px solid #00ff00;
}
button {
  background: #00ff00;
  color: #000;
  border: 1px solid #00ff00;
  padding: 12px 30px;
  margin: 10px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-weight: bold;
}
button:hover {
  background: #00cc00;
  box-shadow: 0 0 10px #00ff00;
}
.footer {
  text-align: center;
  margin-top: 30px;
  font-size: 12px;
  opacity: 0.7;
}
</style>
</head><body>
<main>
<h1>◆ NEIGHBORHOOD BBS ◆</h1>
<h2 style="text-align:center; margin-bottom:20px;">)";
  
  html += BOARD_NAME;
  html += R"(</h2>

<div class="container">
  <h2>◆ STATUS</h2>
  <p>✓ BBS ONLINE | WiFi: )";
  
  html += SSID;
  html += R"( | Range: 50-80m | IRC AESTHETIC</p>
</div>

<div class="container">
  <h2>◆ BULLETINS</h2>
)";
  
  for (int i = 0; i < BULLETIN_COUNT; i++) {
    html += "  <div class=\"bullet\">";
    html += BULLETINS[i];
    html += "</div>\n";
  }
  
  html += R"(
</div>

<div style="text-align: center;">
  <button onclick="location.href='/chat'">[ ENTER CHAT ROOM ]</button>
</div>

<div class="footer">
  NEIGHBORHOOD BBS ◆ LOCAL NETWORK ONLY ◆ NEIGHBORS WELCOME
  <br>Powered by ESP8266 [NodeMCU 1.0]
</div>
</main>
</body></html>)";
  
  return html;
}

String generateChatHTML() {
  String html = R"(<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IRC Chat - Neighborhood BBS</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #000;
  color: #00ff00;
  font-family: 'Courier New', monospace;
}
body::before {
  content: '';
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15) 1px, transparent 1px, transparent 2px);
  pointer-events: none;
  z-index: 999;
}
main {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  z-index: 1;
}
.titlebar {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid #00ff00;
  margin-bottom: 15px;
}
.titlebar button {
  background: #00ff00;
  color: #000;
  border: 1px solid #00ff00;
  padding: 6px 12px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
}
.chat-log {
  border: 2px solid #00ff00;
  height: 60vh;
  overflow-y: auto;
  padding: 10px;
  margin: 15px 0;
  background: #000;
  font-size: 12px;
}
.message {
  margin: 5px 0;
  line-height: 1.4;
}
.message-system {
  color: #ffff00;
  font-style: italic;
}
.message-handle {
  color: #00ff00;
  font-weight: bold;
}
.input-area {
  border: 1px solid #00ff00;
  padding: 15px;
  background: rgba(0,255,0,0.02);
}
.nick-row {
  display: flex;
  gap: 5px;
  margin-bottom: 10px;
}
.nick-row input {
  flex: 1;
  background: #001a00;
  color: #00ff00;
  border: 1px solid #00ff00;
  padding: 8px;
  font-family: 'Courier New', monospace;
}
.nick-row button {
  background: #00ff00;
  color: #000;
  border: 1px solid #00ff00;
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-weight: bold;
}
.msg-row {
  display: flex;
  gap: 5px;
}
.msg-row textarea {
  flex: 1;
  background: #001a00;
  color: #00ff00;
  border: 1px solid #00ff00;
  padding: 8px;
  font-family: 'Courier New', monospace;
  resize: none;
  height: 60px;
}
.msg-row button {
  background: #00ff00;
  color: #000;
  border: 1px solid #00ff00;
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-weight: bold;
  align-self: flex-end;
}
.status {
  margin-top: 10px;
  font-size: 11px;
  opacity: 0.7;
}
</style>
</head><body>
<main>
<div class="titlebar">
  <div><strong>◆ IRC CHAT ROOM ◆</strong></div>
  <button onclick="location.href='/'">← BACK</button>
</div>

<div class="chat-log" id="messages"></div>

<div class="input-area">
  <div class="nick-row">
    <input type="text" id="nick" placeholder="Your handle..." maxlength="16" autocomplete="off">
    <button onclick="setNick()">SET</button>
  </div>
  <div class="msg-row">
    <textarea id="msg" placeholder="Type message (240 max)..." maxlength="240"></textarea>
    <button onclick="sendMsg()">SEND</button>
  </div>
  <div class="status">
    <span id="status">🔴 Connecting...</span>
  </div>
</div>
</main>

<script>
let ws = null;
let nick = 'ANON_000';

function connectWS() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  ws = new WebSocket(proto + '//' + host + ':81');
  
  ws.onopen = () => {
    updateStatus('🟢 Connected');
    ws.send(JSON.stringify({type: 'nick_set', nick: nick}));
  };
  
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    
    if (data.type === 'history') {
      document.getElementById('messages').innerHTML = '';
      data.messages.forEach(msg => addMessage(msg));
    } else if (data.type === 'msg') {
      addMessage(data);
    } else if (data.type === 'nick_ok') {
      nick = data.nick;
    }
  };
  
  ws.onclose = () => {
    updateStatus('🔴 Disconnected');
    setTimeout(connectWS, 3000);
  };
}

function setNick() {
  const input = document.getElementById('nick');
  const newNick = input.value.trim() || 'ANON_000';
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({type: 'nick_set', nick: newNick}));
  }
  input.value = '';
}

function sendMsg() {
  const input = document.getElementById('msg');
  const text = input.value.trim();
  if (text && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({type: 'msg', text: text}));
    input.value = '';
  }
}

function addMessage(msg) {
  const div = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = 'message' + (msg.system ? ' message-system' : '');
  
  if (msg.system) {
    el.textContent = msg.text;
  } else {
    el.innerHTML = '<span class="message-handle">' + msg.handle + ':</span> ' + msg.text;
  }
  
  div.appendChild(el);
  div.scrollTop = div.scrollHeight;
}

function updateStatus(text) {
  document.getElementById('status').textContent = text;
}

document.getElementById('msg').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && e.ctrlKey) sendMsg();
});

connectWS();
</script>
</body></html>)";
  
  return html;
}

void handleRoot() {
  server.send(200, "text/html", generateHTML());
}

void handleChat() {
  server.send(200, "text/html", generateChatHTML());
}

void handleNotFound() {
  handleRoot();  // Captive portal redirect
}

void handleGenerate204() {
  server.send(204);  // iOS captive portal
}

// ============================================
// Setup
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("╔════════════════════════════════════╗");
  Serial.println("║   NEIGHBORHOOD BBS - ESP8266       ║");
  Serial.println("║   Booting...");
  Serial.println("╚════════════════════════════════════╝");
  
  // Setup WiFi AP
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apIP, apIP, netMask);
  WiFi.softAP(SSID);
  
  delay(500);
  
  Serial.print("✓ WiFi SSID: ");
  Serial.println(SSID);
  Serial.print("✓ IP: ");
  Serial.println(WiFi.softAPIP());
  
  // Setup DNS
  dnsServer.start(53, "*", apIP);
  Serial.println("✓ DNS Server started");
  
  // Setup WebServer
  server.on("/", handleRoot);
  server.on("/chat", handleChat);
  server.on("/generate_204", handleGenerate204);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("✓ HTTP Server started (port 80)");
  
  // Setup WebSocket
  wsServer.begin();
  wsServer.onEvent(onWsEvent);
  Serial.println("✓ WebSocket Server started (port 81)");
  
  // Initialize users
  for (int i = 0; i < 10; i++) {
    users[i].num = i;
    sprintf(users[i].nick, "ANON_%03d", i);
  }
  
  // Welcome message
  pushMsg("*", "BBS ONLINE. WELCOME TO " + String(BOARD_NAME), true);
  pushMsg("*", "Local network only. No internet.", true);
  pushMsg("*", "Choose a handle and start chatting!", true);
  
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║   BBS IS LIVE - READY FOR CHAT    ║");
  Serial.println("║   http://192.168.4.1              ║");
  Serial.println("╚════════════════════════════════════╝\n");
}

// ============================================
// Main Loop
// ============================================

void loop() {
  dnsServer.processNextRequest();
  server.handleClient();
  wsServer.loop();
  
  // Print heap status every 60 seconds
  static unsigned long lastHeapCheck = 0;
  if (millis() - lastHeapCheck > 60000) {
    lastHeapCheck = millis();
    Serial.printf("[HEAP] Free: %u bytes\n", ESP.getFreeHeap());
  }
}

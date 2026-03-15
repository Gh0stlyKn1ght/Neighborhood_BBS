# API Testing Guide

## Quick Start

### 1. Install REST Client Extension
```bash
code --install-extension humao.rest-client
```

### 2. Start the Server
```bash
python src/main.py
```

### 3. Open `test_api.rest`
- File is located in project root: `test_api.rest`
- Click any "Send Request" link to execute the test
- Results appear in the Response panel on the right

---

## Test Coverage

The `test_api.rest` file includes **80+ API test requests** organized by category:

### ✅ Health & Status (3 tests)
- Health check endpoint
- Home page load
- 404 error handling

### ✅ Chat Rooms (7 tests)
- Get all rooms
- Create room (basic)
- Create room (missing fields)
- Create room (empty name)
- Create room (with XSS)
- Create room (duplicate - should fail)
- Pagination

### ✅ Chat Messages (7 tests)
- Send message (basic)
- Send without author (anonymous)
- Send without content (fail case)
- Send with XSS attempt
- Send long content (max length)
- Send empty content (fail case)

### ✅ Chat History (5 tests)
- Get history (basic)
- With limit parameter
- With offset parameter
- Limit over max (caps at 100)
- Negative offset (corrected)

### ✅ Board Posts (15 tests)
- Get all posts
- Get with pagination
- Get specific post
- Get non-existent post (404)
- Create post (basic)
- Create post (all fields)
- Create post (marketplace)
- Create post (help)
- Missing title (fail)
- Missing content (fail)
- Invalid category (defaults to general)
- With XSS attempt
- Delete post
- Delete non-existent post

### ✅ Post Replies (5 tests)
- Add reply (basic)
- Reply without author
- Reply without content (fail)
- Reply to non-existent post (404)
- Reply with XSS attempt

### ✅ Error Handling (3 tests)
- Invalid endpoint
- Invalid JSON
- Missing Content-Type

### ✅ Security & Validation (4 tests)
- HTML sanitization (room name)
- HTML sanitization (message)
- HTML sanitization (post)
- Category whitelisting

### ✅ Rate Limiting (2 tests)
- Message rate limit (30/min)
- Room creation rate limit (10/min)

### ✅ Pagination (3 tests)
- Large limit cap
- Offset handling
- Combined limit + offset

---

## How to Use REST Client Extension

### Sending a Request
1. Open `test_api.rest` in VS Code
2. Look for the blue **Send Request** link above each test block
3. Click it to execute the request
4. View response in the **Response** tab (right panel)

### Reading Responses
- **Status Code**: Displayed in top-right (200, 201, 400, etc.)
- **Headers**: HTTP response headers
- **Body**: JSON response data
- **Time**: How long the request took

### Tips & Tricks
- **Duplicate Request**: Ctrl+Shift+D to copy a request
- **Format JSON**: Ctrl+Alt+L to prettify JSON
- **Comment Out**: Use `//` or `#` to disable a request
- **Variables**: Use `@baseUrl` and `@contentType` throughout

### Keyboard Shortcuts
- `Ctrl+Alt+R` - Send all requests in file
- `Ctrl+Alt+L` - Format current request
- `Ctrl+Shift+D` - Duplicate request
- `Shift+Ctrl+E` - Switch between request sections

---

## Expected Results

### ✅ Success Responses (should see 200/201)
```json
{
  "status": "ok",
  "app": "Neighborhood BBS"
}
```

```json
{
  "status": "ok",
  "room_id": 1
}
```

### ❌ Error Responses (expected failures)
```json
400 Bad Request
{
  "error": "Room name required"
}
```

```json
404 Not Found
{
  "error": "Post not found"
}
```

```json
409 Conflict
{
  "error": "Room already exists"
}
```

---

## Testing Workflow

### Fresh Start (Recommended for First Run)
```bash
# Delete old database
rm data/neighborhood.db

# Start server (creates fresh DB)
python src/main.py
```

Then run tests in order:
1. **Health Check** - Verify server responds
2. **Create Chat Room** - Verify POST works
3. **Get Rooms** - Verify rooms were created
4. **Send Message** - Verify message posting
5. **Get History** - Verify message retrieval
6. **Create Board Post** - Verify POST works
7. **Error Tests** - Verify error handling
8. **Security Tests** - Verify XSS protection

### Rate Limiting Test
To test rate limiting (30 requests/minute on messages):
```
1. Select the "Rate Limit Test - Send Message" request
2. Press Ctrl+Alt+R to send all requests at once
3. After ~30 requests in short time, should see 429 error
```

### XSS Prevention Test
Check that HTML tags are stripped:
```
1. Send the "Create Post - With XSS Attempt" request
2. In response, verify post was created
3. Get the post to confirm <script> and <img> tags were removed
```

---

## Troubleshooting

### "Connection Refused"
- Make sure server is running: `python src/main.py`
- Check it's listening on http://localhost:8080

### "400 Bad Request"
- Verify JSON is valid (use Ctrl+Alt+L to format)
- Check Content-Type header is set
- Ensure required fields are present

### "429 Too Many Requests"
- You've hit the rate limit
- This is **expected behavior** - indicates rate limiting is working!
- Wait 1 minute and try again

### Response Shows Database Error
- Database might be locked
- Stop server (Ctrl+C)
- Delete `data/neighborhood.db`
- Restart server

---

## Integration with CI/CD

The `test_api.rest` file can be converted to automated tests:

### Using Newman (Postman CLI)
```bash
# Export as Postman collection
# Then run with Newman:
npm install -g newman
newman run collection.json
```

### Using curl
```bash
# Extract requests and run as curl commands
curl -X GET http://localhost:8080/health
curl -X POST http://localhost:8080/api/chat/rooms \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'
```

### Using pytest (Python)
Tests can be converted to `requests` library calls for automated testing.

---

## Testing Checklist

Before deployment, verify:

- [ ] All 25 unit tests pass: `pytest tests/test_basic.py -v`
- [ ] Server starts without errors: `python src/main.py`
- [ ] Health endpoint responds: `GET /health` → 200 OK
- [ ] Create room works: `POST /api/chat/rooms` → 201 Created
- [ ] Send message works: `POST /api/chat/send` → 201 Created
- [ ] Get rooms returns data: `GET /api/chat/rooms` → 200 OK
- [ ] Create post works: `POST /api/board/posts` → 201 Created
- [ ] XSS is prevented: HTML tags stripped from input
- [ ] Rate limiting works: >30 requests/min returns 429
- [ ] 404 errors handled: Invalid routes return 404
- [ ] CORS headers present: Response shows security headers

---

## Additional Resources

- **REST Client Extension**: https://marketplace.visualstudio.com/items?itemName=humao.rest-client
- **HTTP Status Codes**: https://httpwg.org/specs/rfc9110.html#status.codes
- **JSON Format**: https://www.json.org/
- **Flask Documentation**: https://flask.palletsprojects.com/

---

## Next Steps

1. ✅ Run the automated tests (pytest)
2. ✅ Test with REST Client (this file)
3. ✅ Test frontend in browser
4. ✅ Test WebSocket real-time chat
5. ✅ Test Docker deployment
6. ✅ Test on Raspberry Pi hardware

---

**Questions?** Check the DEVELOPMENT.md or API.md documentation files.

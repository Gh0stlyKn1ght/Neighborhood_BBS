# Neighborhood BBS - API Documentation

## Base URL

```
http://localhost:8080/api
```

## Endpoints

### Health Check

**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "ok",
  "app": "Neighborhood BBS"
}
```

### Chat API

#### Get Chat Rooms

**GET** `/chat/rooms`

Get list of active chat rooms.

**Response:**
```json
{
  "rooms": [
    {
      "id": "general",
      "name": "General",
      "users": 5,
      "created_at": "2026-03-14T10:00:00Z"
    }
  ]
}
```

#### Get Chat History

**GET** `/chat/history/<room_id>`

Get message history for a specific room.

**Query Parameters:**
- `limit` (optional): Maximum number of messages (default: 50)
- `offset` (optional): Message offset for pagination (default: 0)

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "author": "John",
      "content": "Hello everyone!",
      "timestamp": "2026-03-14T10:05:00Z",
      "room_id": "general"
    }
  ]
}
```

#### Send Message

**POST** `/chat/send`

Send a message to a chat room.

**Request Body:**
```json
{
  "room_id": "general",
  "author": "John",
  "content": "Hello everyone!"
}
```

**Response:**
```json
{
  "status": "ok",
  "message_id": "msg_123"
}
```

### Board API

#### Get All Posts

**GET** `/board/posts`

Get all community board posts.

**Query Parameters:**
- `limit` (optional): Maximum number of posts (default: 30)
- `offset` (optional): Post offset for pagination (default: 0)
- `sort` (optional): Sort by "recent" or "popular" (default: "recent")

**Response:**
```json
{
  "posts": [
    {
      "id": "post_123",
      "title": "Lost cat in the neighborhood",
      "content": "Orange tabby, answer to Whiskers...",
      "author": "Jane",
      "created_at": "2026-03-14T09:00:00Z",
      "category": "lost-and-found",
      "replies": 2
    }
  ]
}
```

#### Create Post

**POST** `/board/posts`

Create a new community board post.

**Request Body:**
```json
{
  "title": "Lost cat in the neighborhood",
  "content": "Orange tabby, answer to Whiskers...",
  "author": "Jane",
  "category": "lost-and-found"
}
```

**Response:**
```json
{
  "status": "ok",
  "post_id": "post_123"
}
```

#### Get Specific Post

**GET** `/board/posts/<post_id>`

Get details of a specific board post.

**Response:**
```json
{
  "post": {
    "id": "post_123",
    "title": "Lost cat in the neighborhood",
    "content": "Orange tabby, answer to Whiskers...",
    "author": "Jane",
    "created_at": "2026-03-14T09:00:00Z",
    "category": "lost-and-found",
    "replies": [
      {
        "author": "Bob",
        "content": "I saw an orange cat near Main Street!",
        "created_at": "2026-03-14T09:30:00Z"
      }
    ]
  }
}
```

#### Delete Post

**DELETE** `/board/posts/<post_id>`

Delete a board post (admin only).

**Response:**
```json
{
  "status": "ok"
}
```

## WebSocket Events

### Connected

On successful connection:
```
Event: 'connect'
Data: { sid: 'your_session_id' }
```

### Join Room

```javascript
socket.emit('join_room', { room_id: 'general' })
```

### Receive Message

```javascript
socket.on('new_message', {
  message_id: 'msg_123',
  author: 'John',
  content: 'Hello!',
  timestamp: '2026-03-14T10:05:00Z'
})
```

### Send Message (Real-time)

```javascript
socket.emit('send_message', {
  room_id: 'general',
  author: 'John',
  content: 'Hello everyone!'
})
```

## Error Responses

### 404 Not Found

```json
{
  "error": "Not found"
}
```

### 400 Bad Request

```json
{
  "error": "Invalid request",
  "details": "Missing required field: author"
}
```

### 500 Server Error

```json
{
  "error": "Internal server error"
}
```

## Rate Limiting

- Chat: 100 messages per minute per user
- Board: 10 posts per hour per user
- Exceeding limits returns: `429 Too Many Requests`

## Authentication

Currently, Neighborhood BBS supports anonymous usage. Future versions will include:
- JWT token authentication
- Admin authorization
- User profiles

---

For more information, visit the [main README](../README.md).

# API Reference

Complete reference for the Chatbot REST API.

## Base URL

```
http://localhost:8000
```

In production: `https://your-domain.com`

## Authentication

Currently, the API is open. For production, implement authentication:

```bash
# Example with Bearer token
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "Hello"}'
```

## Endpoints

### POST /chat

Send a message to the chatbot.

**Request:**

```json
{
	"user_id": "string (required, 1-100 chars)",
	"message": "string (required, 1-2000 chars)",
	"session_id": "string (optional)",
	"metadata": {
		"key": "value"
	}
}
```

**Response:**

```json
{
	"text": "Bot's response message",
	"user_id": "user_123",
	"session_id": "session_456",
	"detected_tone": "happy",
	"response_time_ms": 1245.67,
	"metadata": {}
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "message": "Hey! How are you doing?",
    "session_id": "session_456"
  }'
```

**Response Codes:**

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: System not initialized

---

### POST /start

Start a new conversation with a greeting.

**Request:**

```json
{
	"user_id": "string (required)",
	"session_id": "string (optional)"
}
```

**Response:**

```json
{
	"text": "Hey! What's up?",
	"user_id": "user_123",
	"session_id": "session_456",
	"detected_tone": "casual",
	"response_time_ms": 234.56,
	"metadata": {}
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}'
```

---

### GET /users/{user_id}/stats

Get statistics and profile for a user.

**Parameters:**

- `user_id` (path): User identifier

**Response:**

```json
{
	"user_id": "user_123",
	"name": "Alex",
	"interaction_count": 47,
	"first_seen": "2026-01-01T10:00:00Z",
	"last_seen": "2026-01-10T15:30:00Z",
	"interests": ["anime", "gaming", "music"],
	"past_conversations": 12
}
```

**Example:**

```bash
curl "http://localhost:8000/users/user_123/stats"
```

---

### GET /health

Check system health status.

**Response:**

```json
{
	"status": "healthy",
	"checks": {
		"gemini_api": true,
		"redis": true,
		"persona": true,
		"overall": true
	}
}
```

**Status Values:**

- `healthy`: All systems operational
- `unhealthy`: One or more systems down
- `error`: Critical error

**Example:**

```bash
curl "http://localhost:8000/health"
```

---

### GET /stats

Get system-wide statistics.

**Response:**

```json
{
	"total_conversations": 1523,
	"total_tokens": 234567,
	"persona_name": "Luna",
	"model": "gemini-2.0-flash-exp",
	"safety_enabled": true,
	"tone_adaptation_enabled": true
}
```

**Example:**

```bash
curl "http://localhost:8000/stats"
```

---

### GET /

Root endpoint - API information.

**Response:**

```json
{
	"message": "Human-like Chatbot API",
	"version": "1.0.0",
	"docs": "/docs"
}
```

---

## Data Models

### ChatRequest

```typescript
interface ChatRequest {
	user_id: string; // Required, 1-100 characters
	message: string; // Required, 1-2000 characters
	session_id?: string; // Optional, auto-generated if omitted
	metadata?: {
		[key: string]: any;
	};
}
```

### ChatResponse

```typescript
interface ChatResponse {
	text: string; // Bot's response
	user_id: string; // User identifier
	session_id: string; // Session identifier
	detected_tone?: string; // Detected emotional tone
	response_time_ms: number; // Response time in milliseconds
	metadata?: {
		[key: string]: any;
	};
}
```

### UserStats

```typescript
interface UserStats {
	user_id: string;
	name?: string;
	interaction_count: number;
	first_seen: string; // ISO 8601 timestamp
	last_seen: string; // ISO 8601 timestamp
	interests: string[];
	past_conversations: number;
}
```

### HealthResponse

```typescript
interface HealthResponse {
	status: "healthy" | "unhealthy" | "error";
	checks: {
		gemini_api: boolean;
		redis: boolean;
		persona: boolean;
		overall: boolean;
	};
}
```

---

## Error Handling

### Error Response Format

```json
{
	"detail": "Error message describing what went wrong"
}
```

### Common Errors

**400 Bad Request**

```json
{
	"detail": "Message too long (max 2000 characters)"
}
```

**500 Internal Server Error**

```json
{
	"detail": "Error in chat: [error details]"
}
```

**503 Service Unavailable**

```json
{
	"detail": "Chatbot not initialized"
}
```

---

## Rate Limiting

Default rate limits:

- 60 requests per minute per user
- 10 burst allowance

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1641398400
```

**Rate Limit Exceeded Response:**

```json
{
	"detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Usage Examples

### Python

```python
import httpx
import asyncio

async def chat_example():
    async with httpx.AsyncClient() as client:
        # Start conversation
        response = await client.post(
            "http://localhost:8000/start",
            json={"user_id": "user_123"}
        )
        print(response.json())

        # Send message
        response = await client.post(
            "http://localhost:8000/chat",
            json={
                "user_id": "user_123",
                "message": "Hey! What's up?",
                "session_id": "session_456"
            }
        )
        print(response.json())

asyncio.run(chat_example())
```

### JavaScript/Node.js

```javascript
const axios = require("axios");

async function chatExample() {
	// Start conversation
	let response = await axios.post("http://localhost:8000/start", {
		user_id: "user_123",
	});
	console.log(response.data);

	// Send message
	response = await axios.post("http://localhost:8000/chat", {
		user_id: "user_123",
		message: "Hey! What's up?",
		session_id: "session_456",
	});
	console.log(response.data);
}

chatExample();
```

### cURL

```bash
# Start conversation
curl -X POST "http://localhost:8000/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}'

# Send message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "message": "Hey! What is up?",
    "session_id": "session_456"
  }'

# Get user stats
curl "http://localhost:8000/users/user_123/stats"

# Health check
curl "http://localhost:8000/health"
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:

- View all endpoints
- Test API calls directly
- See request/response schemas
- Download OpenAPI specification

---

## WebSocket Support (Future)

Coming soon: Real-time streaming responses via WebSocket.

```javascript
// Future API
const ws = new WebSocket("ws://localhost:8000/ws/chat");

ws.onopen = () => {
	ws.send(
		JSON.stringify({
			user_id: "user_123",
			message: "Hello!",
		})
	);
};

ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log("Bot:", data.text);
};
```

---

## Best Practices

### 1. Session Management

Always use the same `session_id` within a conversation:

```python
# Good
session_id = "session_123"
for message in messages:
    response = await chat(user_id, message, session_id)

# Bad - creates new session each time
for message in messages:
    response = await chat(user_id, message, new_session_id())
```

### 2. Error Handling

Always handle errors gracefully:

```python
try:
    response = await client.post("/chat", json=data)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    print(f"Error: {e.response.json()['detail']}")
except httpx.RequestError as e:
    print(f"Connection error: {e}")
```

### 3. User Identification

Use consistent user IDs:

- Authenticated users: Use their account ID
- Anonymous users: Generate persistent UUID
- Don't create new ID per session

### 4. Metadata Usage

Use metadata for tracking:

```python
response = await chat(
    user_id="user_123",
    message="Hello",
    session_id="session_456",
    metadata={
        "source": "mobile_app",
        "version": "2.1.0",
        "platform": "ios"
    }
)
```

---

## Changelog

### v1.0.0 (2026-01-10)

- Initial release
- Core chat functionality
- Memory management
- Tone adaptation
- Safety validation

---

For more information, see:

- [README.md](README.md) - Overview and features
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment

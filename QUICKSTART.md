# Quick Start Guide

Get your chatbot running in 5 minutes!

## Prerequisites

- Python 3.11+
- Redis (or Docker)
- Google Gemini API key ([Get one here](https://ai.google.dev/))

## Step 1: Install Dependencies

```bash
# Clone/download the project
cd chatbot_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Start Redis

**Option A: Using Docker (Recommended)**

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Option B: Local Installation**

```bash
# macOS
brew install redis
redis-server

# Ubuntu
sudo apt install redis-server
sudo service redis-server start

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

## Step 3: Configure API Key

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379/0
```

Or export directly:

```bash
export GEMINI_API_KEY=your_api_key
export REDIS_URL=redis://localhost:6379/0
```

## Step 4: Run Your First Conversation

```bash
python examples/basic_conversation.py
```

You should see:

```
Initializing chatbot...
Checking system health...
Health status: {'gemini_api': True, 'redis': True, 'persona': True, 'overall': True}

==================================================
CONVERSATION START
==================================================

Bot: Hey! What's up?

User: Hey! How's it going?
Bot: Yo! I'm good, just vibing. How about you? What's new?
[Detected tone: casual, Tokens: 142, Time: 1247ms]
...
```

## Step 5: Start the API Server

```bash
python examples/api_server.py
```

Access the API:

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Test the API

```bash
# Start a conversation
curl -X POST "http://localhost:8000/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user_123"}'

# Send a message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Hey! How are you?",
    "session_id": "session_456"
  }'

# Get user stats
curl "http://localhost:8000/users/test_user_123/stats"
```

## Step 6: Customize Your Bot

Edit `config/persona.yaml` to change:

```yaml
name: "Your Bot Name"
personality:
  core_traits:
    - "your trait here"
    - "another trait"
speaking_style:
  characteristics:
    - "your speaking style"
```

Restart the application to apply changes.

## Next Steps

### Explore Examples

```bash
# Multi-session conversation with memory
python examples/multi_session.py

# Stress test with multiple users
python examples/stress_test.py
```

### Customize Persona

See `config/persona.yaml` for complete customization options:

- Personality traits
- Speaking style
- Response strategies
- Quirks and mannerisms

### Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Common Issues

### "Gemini API Error"

- Check your API key is correct
- Verify you have API credits
- Check network connectivity

### "Redis Connection Failed"

- Ensure Redis is running: `redis-cli ping`
- Check Redis URL is correct
- Verify port 6379 is not blocked

### "Module Not Found"

- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Using with Docker

For a complete setup with all dependencies:

```bash
# Set your API key
export GEMINI_API_KEY=your_key

# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chatbot-api

# Stop
docker-compose down
```

## Code Example

```python
import asyncio
from chatbot_system import ChatbotEngine

async def chat():
    # Initialize
    bot = ChatbotEngine(
        persona_config_path="config/persona.yaml",
        redis_url="redis://localhost:6379/0",
        gemini_api_key="your_key"
    )

    # Chat
    response = await bot.chat(
        user_id="user_123",
        message="Hey! What's up?",
        session_id="session_456"
    )

    print(f"Bot: {response.text}")

asyncio.run(chat())
```

## Need Help?

- 📖 Full documentation: [README.md](README.md)
- 🚀 Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- 💡 API reference: http://localhost:8000/docs
- 🐛 Issues: Check logs and health endpoint

## What's Next?

1. **Test Different Personas**: Modify `persona.yaml` to create different characters
2. **Build a UI**: Integrate with web/mobile interface
3. **Add Features**: Implement voice mode, image understanding, etc.
4. **Scale Up**: Deploy to cloud for production use

Happy chatting! 🤖✨

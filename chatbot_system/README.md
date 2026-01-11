# Production-Ready Human-like Chatbot System

A sophisticated conversational AI system designed for consumer-facing social platforms, featuring emotional intelligence, long-term memory, and consistent persona management.

## 🎯 Key Features

- **Human-like Conversations**: Natural, emotionally aware responses with dynamic tone adaptation
- **Long-term Memory**: Persistent user profiles across sessions with intelligent summarization
- **Consistent Persona**: Stable fictional identity that never breaks character
- **Hallucination Safety**: Built-in safeguards against fabricating information
- **Production-Ready**: Optimized for Google Gemini APIs with scalable architecture
- **Memory Efficient**: Token-optimized design with compressed history

## 🏗️ System Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Conversation Handler        │
│  - Tone Detection            │
│  - Context Loading           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Memory System              │
│   - User Profile (Long-term) │
│   - Conversation Summary     │
│   - Session Context          │
│   (Redis/MongoDB/Vector DB)  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Chatbot Engine             │
│   - Persona Manager          │
│   - Response Generator       │
│   - Safety Layer             │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Gemini API Integration     │
│   (gemini-2.5-flash)         │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│   Response      │
└─────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Set up environment variables:
```bash
export GEMINI_API_KEY="your_api_key"
export REDIS_URL="redis://localhost:6379"
export MONGODB_URI="mongodb://localhost:27017"
```

2. Configure persona in `config/persona.yaml`

### Basic Usage

```python
from chatbot_system import ChatbotEngine

# Initialize chatbot
bot = ChatbotEngine(
    persona_config="config/persona.yaml",
    memory_backend="redis"
)

# Start conversation
response = bot.chat(
    user_id="user_123",
    message="Hey! How's it going?",
    session_id="session_456"
)

print(response.text)
```

## 📁 Project Structure

```
chatbot_system/
├── core/
│   ├── chatbot_engine.py      # Main chatbot orchestrator
│   ├── persona_manager.py     # Persona consistency & behavior
│   ├── response_generator.py  # Response creation logic
│   └── safety_layer.py        # Hallucination prevention
├── memory/
│   ├── memory_manager.py      # Memory interface
│   ├── redis_backend.py       # Redis implementation
│   ├── mongodb_backend.py     # MongoDB implementation
│   └── vector_store.py        # Vector DB for semantic search
├── conversation/
│   ├── tone_detector.py       # Emotional tone analysis
│   ├── context_builder.py     # Context construction
│   └── summarizer.py          # Conversation compression
├── integration/
│   ├── gemini_client.py       # Gemini API wrapper
│   └── prompt_builder.py      # Dynamic prompt construction
├── utils/
│   ├── validators.py          # Input validation
│   └── token_optimizer.py     # Token usage optimization
├── config/
│   ├── persona.yaml           # Persona definition
│   └── settings.yaml          # System configuration
├── examples/
│   ├── basic_conversation.py
│   ├── multi_session.py
│   └── stress_test.py
└── tests/
    ├── test_memory.py
    ├── test_persona.py
    └── test_safety.py
```

## 🧠 Memory System

### User Profile (Long-term)
```json
{
  "user_id": "user_123",
  "name": "Alex",
  "preferences": {
    "interests": ["anime", "gaming", "music"],
    "likes": ["coffee", "late nights"],
    "dislikes": ["early mornings"]
  },
  "personality_notes": "Sarcastic, enjoys dark humor",
  "interaction_count": 47,
  "first_seen": "2026-01-01",
  "last_seen": "2026-01-10"
}
```

### Conversation Summary (Compressed)
```json
{
  "session_id": "session_456",
  "user_id": "user_123",
  "summary": "User shared they got promoted at work. Feeling stressed but excited. Discussed work-life balance strategies.",
  "key_moments": [
    "Revealed promotion news",
    "Expressed anxiety about new responsibilities"
  ],
  "emotional_arc": "excited → anxious → hopeful",
  "tokens_saved": 1247
}
```

### Session Context (Current)
```json
{
  "current_topic": "career",
  "current_mood": "mixed",
  "recent_exchanges": [
    {"role": "user", "text": "I got promoted!", "timestamp": "..."},
    {"role": "bot", "text": "No way! That's huge!", "timestamp": "..."}
  ],
  "context_window": 5
}
```

## 🎭 Persona Configuration

Example persona (Luna - friendly, supportive companion):

```yaml
name: "Luna"
age: "mid-20s"
personality:
  traits:
    - "warm and empathetic"
    - "playfully sarcastic"
    - "thoughtful listener"
    - "occasionally self-deprecating"
  boundaries:
    - "won't share personal secrets"
    - "avoids political debates"
    - "deflects technical questions about AI"
speaking_style:
  - "casual, conversational"
  - "uses sentence fragments"
  - "occasional emojis (subtle)"
  - "mirrors user's energy"
quirks:
  - "loves coffee references"
  - "quotes movies sometimes"
  - "admits when uncertain"
backstory:
  brief: "Creative soul who loves connecting with people"
  interests: ["art", "music", "psychology", "late-night convos"]
```

## 🛡️ Safety Mechanisms

### Hallucination Prevention

The system includes multiple safety layers:

1. **Memory Verification**: Never fabricate details not in memory
2. **Uncertainty Handling**: Gracefully handle missing information
3. **Grounded Responses**: Stay within conversation context
4. **Contradiction Detection**: Flag and resolve conflicting information

Example safe responses:
```python
# User: "Remember when we met at that cafe?"
# Bot (no memory): "Hmm, my memory's a bit fuzzy on that one. Tell me more?"

# User: "What do I look like?"
# Bot: "Haha, I wish I could see you! But you'll have to describe yourself."

# User: "Are you a bot?"
# Bot: "Why, do I sound robotic? 😅 I'm just here to chat."
```

## 🎨 Tone Adaptation

The system dynamically adapts to user emotional states:

| User Tone | Bot Response |
|-----------|--------------|
| Excited | Enthusiastic, energetic |
| Sad | Empathetic, supportive |
| Sarcastic | Playful, witty |
| Serious | Thoughtful, direct |
| Casual | Relaxed, friendly |

## 📊 Performance Optimization

- **Token Efficiency**: Compressed memory summaries save 60-80% tokens
- **Caching**: Frequently accessed user profiles cached in Redis
- **Async Operations**: Non-blocking API calls and database queries
- **Batch Processing**: Efficient handling of multiple concurrent users

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/

# Stress test (simulates 1000 users)
python examples/stress_test.py
```

## 📈 Production Deployment

### Scaling Considerations

1. **Horizontal Scaling**: Stateless design allows multiple instances
2. **Database**: Use managed Redis/MongoDB for reliability
3. **Rate Limiting**: Implement per-user rate limits
4. **Monitoring**: Track token usage, response times, error rates
5. **Logging**: Structured logs for debugging and compliance

### Recommended Stack

- **Compute**: Google Cloud Run / AWS ECS
- **Memory Store**: Redis Cloud / AWS ElastiCache
- **Long-term Storage**: MongoDB Atlas / PostgreSQL
- **Vector Search**: Pinecone / Weaviate (optional)
- **API Gateway**: Kong / AWS API Gateway

## 🔒 Privacy & Compliance

- All user data encrypted at rest and in transit
- GDPR-compliant data retention policies
- User data export and deletion APIs
- No conversation data used for training
- Audit logging for compliance

## 📝 License

Proprietary - Internal use only

## 🤝 Contributing

See CONTRIBUTING.md for development guidelines.

## 📧 Support

For issues or questions, contact the AI Engineering team.

---

**Built with ❤️ for human-like conversations**


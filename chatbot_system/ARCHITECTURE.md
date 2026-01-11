# System Architecture

Detailed technical architecture of the chatbot system.

## Overview

The system follows a modular, layered architecture designed for:

- **Scalability**: Stateless design for horizontal scaling
- **Maintainability**: Clear separation of concerns
- **Reliability**: Safety checks at multiple levels
- **Performance**: Token optimization and caching

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
│              (FastAPI REST API)                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                 Chatbot Engine                           │
│         (Main Orchestrator)                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  • Request Validation                            │   │
│  │  • Component Coordination                        │   │
│  │  • Response Assembly                             │   │
│  └─────────────────────────────────────────────────┘   │
└──┬──────────┬──────────┬──────────┬──────────┬─────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Persona│ │Memory│ │Conver│ │Safety│ │Integration│
│Manager│ │System│ │sation│ │Layer │ │  Layer   │
└───────┘ └──┬───┘ └──────┘ └──────┘ └─────┬────┘
             │                               │
             ▼                               ▼
    ┌────────────────┐            ┌──────────────┐
    │  Redis/Memory  │            │ Gemini API   │
    │    Backend     │            │   Client     │
    └────────────────┘            └──────────────┘
```

## Component Details

### 1. API Layer

**Technology**: FastAPI with async support

**Responsibilities**:

- HTTP request handling
- Request validation (Pydantic)
- Response formatting
- CORS handling
- Rate limiting
- Authentication (future)

**Endpoints**:

- `POST /chat` - Main chat endpoint
- `POST /start` - Start conversation
- `GET /users/{id}/stats` - User statistics
- `GET /health` - Health check
- `GET /stats` - System statistics

### 2. Chatbot Engine

**Core Component**: `ChatbotEngine` class

**Responsibilities**:

- Orchestrates all subsystems
- Manages request flow
- Handles errors gracefully
- Tracks metrics

**Key Methods**:

- `chat()` - Process user message
- `start_conversation()` - Initialize session
- `get_user_stats()` - Retrieve user data
- `health_check()` - System health

**Flow**:

1. Validate input
2. Detect tone
3. Load memory context
4. Build prompt
5. Generate response
6. Validate safety
7. Update memory
8. Return response

### 3. Persona Manager

**Purpose**: Maintain consistent character identity

**Components**:

- Persona configuration (YAML)
- Response validation
- Deflection strategies
- Style consistency

**Key Features**:

- Never breaks character
- Consistent personality traits
- Natural response patterns
- Bot question deflection

**Configuration**:

```yaml
name: "Luna"
personality:
  core_traits: [...]
speaking_style:
  characteristics: [...]
quirks:
  phrases: [...]
```

### 4. Memory System

**Architecture**: Three-tier memory

#### Tier 1: Session Context (Short-term)

- **Storage**: Redis (TTL: 24 hours)
- **Content**: Recent message exchanges (last 8)
- **Purpose**: Immediate conversation context

#### Tier 2: User Profile (Long-term)

- **Storage**: Redis (TTL: 90 days)
- **Content**: Name, interests, preferences, personality notes
- **Purpose**: Persistent user information

#### Tier 3: Conversation Summaries (Compressed)

- **Storage**: Redis lists
- **Content**: Compressed past conversations
- **Purpose**: Long-term context without token bloat

**Optimization**:

- Summarization after 10 messages
- 60-80% token reduction
- Semantic preservation
- Key moment extraction

**Backend Interface**:

```python
class MemoryManager:
    async def get_user_profile(user_id) -> UserProfile
    async def save_user_profile(profile)
    async def get_session_context(session_id, user_id) -> SessionContext
    async def save_session_context(session)
    async def get_conversation_summaries(user_id) -> List[Summary]
```

### 5. Conversation Handler

**Components**:

#### Tone Detector

- Pattern-based emotion detection
- Energy level analysis
- Formality assessment
- Confidence scoring

**Detected Tones**:

- Sad, excited, angry, anxious
- Sarcastic, happy, casual

#### Context Builder

- Combines memory sources
- Token optimization
- Relevance filtering
- Natural language formatting

#### Summarizer

- Extractive summarization
- Key moment identification
- Topic extraction
- Emotional arc detection

### 6. Safety Layer

**Purpose**: Prevent hallucinations and unsafe responses

**Checks**:

1. **Forbidden Pattern Detection**

   - AI/technical terminology
   - System details exposure

2. **Robotic Language Detection**

   - Unnatural phrasing
   - Template patterns

3. **Fabrication Detection**

   - Ungrounded memory claims
   - Invented details

4. **Grounding Verification**
   - Context-based validation
   - Memory verification

**Safety Flow**:

```
Response Generation
        ↓
Forbidden Patterns? → Reject
        ↓
Robotic Language? → Sanitize
        ↓
Memory Grounded? → Verify
        ↓
Safe Response ✓
```

### 7. Integration Layer

#### Gemini Client

- API communication
- Retry logic (exponential backoff)
- Error handling
- Token tracking
- Streaming support (future)

**Configuration**:

- Model: gemini-2.0-flash-exp
- Temperature: 0.9 (high variability)
- Max tokens: 500
- Top-p: 0.95, Top-k: 40

#### Prompt Builder

- System prompt construction
- Context integration
- Tone guidance injection
- Safety constraints

**Prompt Structure**:

```
[System Prompt]
  - Persona definition
  - Core rules
  - Safety constraints

[User Context]
  - Profile information
  - Past summaries

[Tone Guidance]
  - Detected mood
  - Adaptation rules

[Conversation History]
  - Recent exchanges
```

## Data Flow

### Incoming Request Flow

```
1. User sends message → API endpoint
                          ↓
2. Validate input (Pydantic)
                          ↓
3. ChatbotEngine.chat()
                          ↓
4. Detect tone (ToneDetector)
                          ↓
5. Load memory (MemoryManager)
                          ↓
6. Build context (ContextBuilder)
                          ↓
7. Generate prompt (PromptBuilder)
                          ↓
8. Call Gemini API (GeminiClient)
                          ↓
9. Validate response (SafetyLayer)
                          ↓
10. Save to memory (MemoryManager)
                          ↓
11. Return response → API response
```

### Memory Update Flow

```
User message received
        ↓
Extract information
  - Name
  - Interests
  - Preferences
  - Personality traits
        ↓
Update user profile
        ↓
Add to session context
        ↓
Check if should summarize (>10 messages)
        ↓
If yes: Create summary
        ↓
Compress session
        ↓
Save all changes
```

## Scalability Design

### Stateless Application

- No session state in application
- All state in Redis
- Enables horizontal scaling

### Connection Pooling

- Redis connection pool (50 connections)
- Async I/O throughout
- Non-blocking operations

### Caching Strategy

```
Level 1: In-memory (Python dict)
  - Persona config
  - Common patterns
  - TTL: Application lifetime

Level 2: Redis (distributed)
  - User profiles
  - Session contexts
  - TTL: Hours to days
```

### Load Distribution

```
                Load Balancer
                     |
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Instance 1   Instance 2   Instance 3
        |            |            |
        └────────────┼────────────┘
                     ▼
                 Redis Cluster
```

## Security Architecture

### Defense in Depth

1. **Input Validation**

   - Length limits
   - Character filtering
   - PII detection

2. **Business Logic**

   - Rate limiting
   - User quotas
   - Request throttling

3. **Output Validation**

   - Safety layer checks
   - Response sanitization
   - Content filtering

4. **Infrastructure**
   - Network isolation
   - TLS encryption
   - Secret management

### Data Privacy

- **In Transit**: TLS 1.3
- **At Rest**: Redis encryption (optional)
- **Access**: Role-based (future)
- **Retention**: Configurable TTLs
- **Compliance**: GDPR-ready

## Monitoring & Observability

### Metrics

**Application Metrics**:

- Requests per second
- Response latency (p50, p95, p99)
- Error rate
- Active sessions

**Business Metrics**:

- Total conversations
- Token usage
- User engagement
- Tone distribution

**Infrastructure Metrics**:

- CPU/Memory usage
- Redis operations/sec
- Network throughput
- Disk I/O

### Logging

**Structured Logging** (JSON):

```json
{
	"timestamp": "2026-01-10T12:00:00Z",
	"level": "INFO",
	"component": "chatbot_engine",
	"event": "message_processed",
	"user_id": "user_123",
	"session_id": "session_456",
	"response_time_ms": 1245,
	"tokens_used": 187,
	"detected_tone": "happy"
}
```

**Log Levels**:

- DEBUG: Detailed debugging
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Failures requiring attention
- CRITICAL: System-wide failures

### Health Checks

**Endpoint**: `GET /health`

**Checks**:

1. Gemini API connectivity
2. Redis connectivity
3. Persona configuration loaded
4. Memory subsystem operational

**Response**:

```json
{
	"status": "healthy",
	"checks": {
		"gemini_api": true,
		"redis": true,
		"persona": true,
		"overall": true
	},
	"timestamp": "2026-01-10T12:00:00Z"
}
```

## Technology Stack

**Core**:

- Python 3.11+
- FastAPI (async web framework)
- Pydantic (data validation)
- Google Generative AI (LLM)

**Storage**:

- Redis (primary memory store)
- MongoDB (optional, analytics)

**Async**:

- asyncio (concurrency)
- aioredis (async Redis)
- httpx (async HTTP)

**Utilities**:

- PyYAML (config parsing)
- tenacity (retry logic)
- structlog (structured logging)

## Performance Characteristics

**Target Metrics**:

- Response time: < 2s (p95)
- Throughput: 100+ req/s per instance
- Memory: < 500MB per instance
- Token efficiency: 200-400 per exchange

**Bottlenecks**:

1. Gemini API latency (1-2s)
2. Redis network I/O (< 10ms)
3. Prompt construction (< 50ms)

**Optimizations**:

- Async everywhere
- Connection pooling
- Prompt compression
- Response caching

## Future Enhancements

### Phase 2

- WebSocket support for streaming
- Vector database for semantic search
- Multi-language support
- Voice input/output

### Phase 3

- Fine-tuned models
- Multi-modal (image understanding)
- Advanced analytics dashboard
- A/B testing framework

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0

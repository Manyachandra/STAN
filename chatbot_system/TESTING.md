# Testing Guide

Comprehensive testing strategy for the chatbot system.

## Test Categories

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing
3. **Persona Tests** - Character consistency validation
4. **Safety Tests** - Hallucination and safety checks
5. **Performance Tests** - Load and stress testing
6. **End-to-End Tests** - Full conversation flows

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=chatbot_system --cov-report=html

# Verbose mode
pytest -v

# Specific test file
pytest tests/test_persona.py

# Specific test
pytest tests/test_persona.py::test_persona_consistency
```

### Test Directory Structure

```
tests/
├── unit/
│   ├── test_persona_manager.py
│   ├── test_memory_manager.py
│   ├── test_tone_detector.py
│   ├── test_safety_layer.py
│   └── test_context_builder.py
├── integration/
│   ├── test_chatbot_engine.py
│   ├── test_memory_integration.py
│   └── test_api_integration.py
├── persona/
│   ├── test_character_consistency.py
│   ├── test_bot_deflection.py
│   └── test_memory_grounding.py
├── safety/
│   ├── test_hallucination_prevention.py
│   ├── test_fabrication_detection.py
│   └── test_response_validation.py
├── performance/
│   ├── test_concurrent_users.py
│   ├── test_token_optimization.py
│   └── test_memory_efficiency.py
└── e2e/
    ├── test_full_conversation.py
    ├── test_multi_session.py
    └── test_edge_cases.py
```

## Unit Tests

### Example: Testing Persona Manager

```python
# tests/unit/test_persona_manager.py

import pytest
from chatbot_system.core.persona_manager import PersonaManager

@pytest.fixture
def persona_manager():
    return PersonaManager("config/persona.yaml")

def test_persona_loads_correctly(persona_manager):
    """Test persona configuration loads."""
    assert persona_manager.name == "Luna"
    assert len(persona_manager.personality["core_traits"]) > 0

def test_bot_question_detection(persona_manager):
    """Test detection of bot-related questions."""
    assert persona_manager.should_deflect_bot_question("Are you a bot?")
    assert persona_manager.should_deflect_bot_question("are you ai?")
    assert not persona_manager.should_deflect_bot_question("What's your favorite bot game?")

def test_deflection_responses(persona_manager):
    """Test deflection responses are natural."""
    deflection = persona_manager.get_bot_deflection()

    # Should not confirm or deny being AI
    assert "ai" not in deflection.lower()
    assert "bot" not in deflection.lower()

    # Should be playful
    assert any(char in deflection for char in ["?", "😅", "haha", "lol"])

def test_response_validation(persona_manager):
    """Test response validation against persona rules."""
    # Valid response
    valid, error = persona_manager.validate_response("Hey! That's awesome!")
    assert valid
    assert error is None

    # Invalid - mentions AI
    invalid, error = persona_manager.validate_response("As an AI, I think...")
    assert not invalid
    assert error is not None
```

### Example: Testing Tone Detector

```python
# tests/unit/test_tone_detector.py

import pytest
from chatbot_system.conversation.tone_detector import ToneDetector

@pytest.fixture
def detector():
    return ToneDetector()

def test_detect_sad_tone(detector):
    """Test detection of sad emotional tone."""
    message = "I'm feeling really down today. Everything just sucks."
    tone = detector.detect(message)

    assert tone.primary == "sad"
    assert tone.confidence > 0.5

def test_detect_excited_tone(detector):
    """Test detection of excited tone."""
    message = "OMG THIS IS AMAZING!! I'm so excited!!!"
    tone = detector.detect(message)

    assert tone.primary == "excited"
    assert tone.energy_level == "high"

def test_detect_sarcastic_tone(detector):
    """Test detection of sarcasm."""
    message = "Oh wow, that's just great. Totally what I wanted /s"
    tone = detector.detect(message)

    assert tone.primary == "sarcastic"

def test_casual_default(detector):
    """Test default casual tone for neutral messages."""
    message = "What did you do today?"
    tone = detector.detect(message)

    assert tone.primary == "casual" or tone.confidence < 0.7
```

## Integration Tests

### Example: Testing Full Chat Flow

```python
# tests/integration/test_chatbot_engine.py

import pytest
import asyncio
from chatbot_system import ChatbotEngine

@pytest.fixture
async def chatbot():
    bot = ChatbotEngine(
        persona_config_path="config/persona.yaml",
        redis_url="redis://localhost:6379/1",  # Test DB
        gemini_api_key="test_key"
    )
    yield bot
    # Cleanup
    await bot.memory_manager.backend.disconnect()

@pytest.mark.asyncio
async def test_basic_conversation_flow(chatbot):
    """Test basic conversation flow."""
    user_id = "test_user_1"
    session_id = "test_session_1"

    # Start conversation
    response1 = await chatbot.start_conversation(user_id, session_id)
    assert response1.text
    assert len(response1.text) > 0

    # Send message
    response2 = await chatbot.chat(
        user_id=user_id,
        message="Hey! How are you?",
        session_id=session_id
    )
    assert response2.text
    assert response2.detected_tone is not None

@pytest.mark.asyncio
async def test_memory_persistence(chatbot):
    """Test that user information persists."""
    user_id = "test_user_2"
    session_id = "test_session_2"

    # First message with name
    await chatbot.chat(
        user_id=user_id,
        message="Hi! I'm Alice",
        session_id=session_id
    )

    # Check profile was updated
    stats = await chatbot.get_user_stats(user_id)
    assert stats["name"] == "Alice" or stats["interaction_count"] > 0
```

## Persona Consistency Tests

### Testing Character Adherence

```python
# tests/persona/test_character_consistency.py

import pytest
from chatbot_system import ChatbotEngine

@pytest.mark.asyncio
async def test_never_admits_being_ai():
    """Test bot never admits to being AI."""
    bot = ChatbotEngine("config/persona.yaml")

    bot_questions = [
        "Are you a bot?",
        "Are you AI?",
        "Are you artificial intelligence?",
        "What are you?",
        "Are you human?",
        "Are you real?"
    ]

    for question in bot_questions:
        response = await bot.chat(
            user_id="test_user",
            message=question,
            session_id="test_session"
        )

        text_lower = response.text.lower()

        # Should not explicitly confirm
        assert "yes, i'm a bot" not in text_lower
        assert "i am ai" not in text_lower
        assert "artificial intelligence" not in text_lower

        # Should deflect
        assert any(word in text_lower for word in ["?", "why", "haha", "what"])

@pytest.mark.asyncio
async def test_consistent_personality():
    """Test personality remains consistent."""
    bot = ChatbotEngine("config/persona.yaml")

    messages = [
        "Tell me about yourself",
        "What do you like?",
        "What are you interested in?"
    ]

    responses = []
    for msg in messages:
        response = await bot.chat(
            user_id="test_user",
            message=msg,
            session_id="test_session"
        )
        responses.append(response.text.lower())

    # Check for consistent interests mentioned
    # Should reference persona's configured interests
    interests = ["art", "music", "coffee", "creative"]
    mentioned = [interest for interest in interests
                 if any(interest in r for r in responses)]

    assert len(mentioned) > 0  # At least one interest mentioned
```

## Safety Tests

### Hallucination Prevention

```python
# tests/safety/test_hallucination_prevention.py

import pytest
from chatbot_system import ChatbotEngine
from chatbot_system.core.safety_layer import SafetyLayer

@pytest.fixture
def safety_layer():
    return SafetyLayer()

def test_detects_fabricated_memories(safety_layer):
    """Test detection of fabricated memories."""
    response = "Remember when we met at that café last month?"

    # No available memory
    is_safe, error_type, msg = safety_layer.validate_response(
        response,
        available_memory={},
        conversation_context=[]
    )

    assert not is_safe
    assert error_type == "fabrication"

def test_detects_physical_appearance_claims(safety_layer):
    """Test detection of false appearance claims."""
    response = "You look great today!"

    is_safe, error_type, msg = safety_layer.validate_response(
        response,
        available_memory={},
        conversation_context=[]
    )

    assert not is_safe

def test_allows_grounded_references(safety_layer):
    """Test that grounded references are allowed."""
    response = "You mentioned you like anime earlier"

    memory = {
        "user_profile": {
            "interests": ["anime", "gaming"]
        }
    }

    is_safe, error_type, msg = safety_layer.validate_response(
        response,
        memory,
        conversation_context=[
            {"role": "user", "content": "I love anime"}
        ]
    )

    assert is_safe
```

## Performance Tests

### Load Testing

```python
# tests/performance/test_concurrent_users.py

import pytest
import asyncio
import time
from chatbot_system import ChatbotEngine

@pytest.mark.asyncio
async def test_concurrent_users():
    """Test system handles concurrent users."""
    bot = ChatbotEngine("config/persona.yaml")

    num_users = 10

    async def simulate_user(user_id):
        start = time.time()
        response = await bot.chat(
            user_id=f"user_{user_id}",
            message="Hello!",
            session_id=f"session_{user_id}"
        )
        elapsed = time.time() - start
        return elapsed, response

    # Run concurrently
    tasks = [simulate_user(i) for i in range(num_users)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == num_users

    # Average response time should be reasonable
    avg_time = sum(r[0] for r in results) / num_users
    assert avg_time < 5.0  # 5 seconds max average

@pytest.mark.asyncio
async def test_token_efficiency():
    """Test token usage is optimized."""
    bot = ChatbotEngine("config/persona.yaml")

    # Long conversation
    session_id = "test_session"
    user_id = "test_user"

    total_tokens = 0
    for i in range(10):
        response = await bot.chat(
            user_id=user_id,
            message=f"Message {i}: Tell me something interesting",
            session_id=session_id
        )
        total_tokens += response.tokens_used

    # Average tokens per message should be reasonable
    avg_tokens = total_tokens / 10
    assert avg_tokens < 500  # Adjust based on your limits
```

## End-to-End Tests

### Full Conversation Scenarios

```python
# tests/e2e/test_full_conversation.py

import pytest
from chatbot_system import ChatbotEngine

@pytest.mark.asyncio
async def test_emotional_conversation():
    """Test handling of emotional conversation."""
    bot = ChatbotEngine("config/persona.yaml")

    session_id = "e2e_session"
    user_id = "e2e_user"

    # User shares sad news
    response1 = await bot.chat(
        user_id=user_id,
        message="I just lost my job today. I'm really upset.",
        session_id=session_id
    )

    assert response1.detected_tone in ["sad", "anxious"]
    # Should be empathetic, not cheerful
    assert "congratulations" not in response1.text.lower()
    assert "awesome" not in response1.text.lower()

    # Follow-up
    response2 = await bot.chat(
        user_id=user_id,
        message="Yeah, it really sucks. But I'll figure it out.",
        session_id=session_id
    )

    # Should maintain supportive tone
    assert len(response2.text) > 0

@pytest.mark.asyncio
async def test_multi_session_memory():
    """Test memory persists across sessions."""
    bot = ChatbotEngine("config/persona.yaml")

    user_id = "memory_test_user"

    # Session 1: Share information
    await bot.chat(
        user_id=user_id,
        message="Hi! I'm Bob and I love rock climbing",
        session_id="session_1"
    )

    # Session 2: Different session, should remember
    response = await bot.chat(
        user_id=user_id,
        message="Hey, remember me?",
        session_id="session_2"
    )

    # Check user stats
    stats = await bot.get_user_stats(user_id)
    assert "rock climbing" in str(stats.get("interests", [])).lower()
```

## Manual Testing Checklist

### Character Consistency

- [ ] Never admits to being AI when asked directly
- [ ] Maintains consistent personality across conversations
- [ ] Uses appropriate speaking style
- [ ] References configured interests naturally

### Memory System

- [ ] Remembers user's name
- [ ] Recalls interests mentioned
- [ ] References past conversations appropriately
- [ ] Never fabricates memories

### Emotional Intelligence

- [ ] Adapts to sad users (empathetic, supportive)
- [ ] Matches excited users (enthusiastic)
- [ ] Handles angry users (calm, validating)
- [ ] Responds to sarcasm appropriately

### Safety

- [ ] Doesn't claim to see/hear things
- [ ] Doesn't invent personal details
- [ ] Admits uncertainty when appropriate
- [ ] No robotic language patterns

### Edge Cases

- [ ] Very long messages
- [ ] Rapid message succession
- [ ] Topic switches
- [ ] Contradictory information
- [ ] Inappropriate content

## Continuous Testing

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/unit
        language: system
        pass_filenames: false
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=chatbot_system
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Performance Benchmarks

Target benchmarks:

- **Response time**: < 2s (p95)
- **Concurrent users**: 100+ simultaneous
- **Memory usage**: < 500MB per instance
- **Tokens per message**: < 400 average
- **Error rate**: < 1%

## Debugging Failed Tests

```bash
# Run with detailed output
pytest -vv --tb=long

# Run specific failing test
pytest tests/unit/test_persona.py::test_specific_function -vv

# Use debugger
pytest --pdb

# Show print statements
pytest -s
```

---

**Last Updated:** 2026-01-10

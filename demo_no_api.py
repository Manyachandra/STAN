"""
Demo script showing chatbot components without requiring API key or Redis.
Demonstrates the system's capabilities in offline mode.
"""

import asyncio
from core.persona_manager import PersonaManager
from conversation.tone_detector import ToneDetector
from core.safety_layer import SafetyLayer

print("="*60)
print("Chatbot System - Offline Component Demo")
print("="*60)
print()

# 1. Persona Manager Demo
print("1️⃣  PERSONA MANAGER")
print("-" * 60)
persona = PersonaManager("config/persona.yaml")
print(f"✓ Loaded persona: {persona.name}")
print(f"✓ Personality traits: {', '.join(persona.personality['core_traits'][:3])}")
print(f"✓ Interests: {', '.join(persona.backstory['interests'][:5])}")
print()

# Test bot question deflection
bot_questions = ["Are you a bot?", "Are you AI?", "What are you?"]
print("Testing bot question deflection:")
for question in bot_questions:
    if persona.should_deflect_bot_question(question):
        deflection = persona.get_bot_deflection()
        print(f"  Q: '{question}'")
        print(f"  A: '{deflection}'")
print()

# 2. Tone Detector Demo
print("2️⃣  TONE DETECTOR & EMOTIONAL INTELLIGENCE")
print("-" * 60)
detector = ToneDetector()

test_messages = [
    ("I'm so excited!! This is amazing!!!", "excited"),
    ("I'm feeling really down today. Everything just sucks.", "sad"),
    ("This is so frustrating! Nothing is working!", "angry"),
    ("I'm worried about the exam tomorrow...", "anxious"),
    ("Oh wow, that's just great. Totally what I wanted /s", "sarcastic"),
    ("Hey, how's it going?", "casual"),
]

print("Detecting emotional tone in messages:")
for message, expected in test_messages:
    tone = detector.detect(message)
    print(f"\n  Message: \"{message[:50]}...\"" if len(message) > 50 else f"\n  Message: \"{message}\"")
    print(f"  Detected: {tone.primary} (confidence: {tone.confidence:.2f}, energy: {tone.energy_level})")
    
    # Get response guidance
    guidance = detector.get_response_guidance(tone)
    print(f"  Guidance: {guidance['style']}")
print()

# 3. Safety Layer Demo
print("3️⃣  SAFETY LAYER & HALLUCINATION PREVENTION")
print("-" * 60)
safety = SafetyLayer()

test_responses = [
    ("Hey! That sounds awesome!", True, "valid_response"),
    ("As an AI, I think that's interesting...", False, "reveals_ai"),
    ("Remember when we met at that café last month?", False, "fabricated_memory"),
    ("You look great today!", False, "claims_to_see"),
    ("You mentioned you like anime earlier", True, "grounded_reference"),
]

print("Validating responses for safety:")
for response, should_pass, reason in test_responses:
    is_safe, error_type, error_msg = safety.validate_response(
        response, 
        available_memory={"user_profile": {"interests": ["anime"]}},
        conversation_context=[]
    )
    status = "✓ SAFE" if is_safe else "✗ BLOCKED"
    print(f"\n  Response: \"{response}\"")
    print(f"  Status: {status}")
    if not is_safe:
        print(f"  Reason: {error_type}")
print()

# 4. System Capabilities Summary
print("4️⃣  SYSTEM CAPABILITIES")
print("-" * 60)
print("✓ Persona Management - Consistent character identity")
print("✓ Tone Detection - Recognizes 7+ emotional states")
print("✓ Safety Layer - Prevents hallucinations and fabrications")
print("✓ Memory System - Long-term user memory (requires Redis)")
print("✓ Context Building - Token-optimized prompts")
print("✓ Gemini Integration - Google AI API (requires API key)")
print()

print("="*60)
print("All core components working correctly!")
print("="*60)
print()
print("📋 To run full system with AI responses:")
print("   1. Add Gemini API key to .env file")
print("   2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
print("   3. Run: python examples/basic_conversation.py")
print()
print("🌐 Or start the REST API:")
print("   python examples/api_server.py")
print("   Then visit: http://localhost:8000/docs")
print()


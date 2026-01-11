"""
Demo script showing the chatbot system working with MongoDB.
This demonstrates memory persistence, persona, and conversation flow.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Direct imports without package prefix
import memory.mongodb_backend as mongodb_module
import memory.memory_manager as memory_module
import core.persona_manager as persona_module
import conversation.tone_detector as tone_module
import conversation.context_builder as context_module

MongoDBBackend = mongodb_module.MongoDBBackend
MemoryManager = memory_module.MemoryManager
PersonaManager = persona_module.PersonaManager
ToneDetector = tone_module.ToneDetector
ContextBuilder = context_module.ContextBuilder


async def simulate_conversation():
    """Simulate a conversation with memory persistence."""
    
    print("=" * 80)
    print("🤖 Human-Like Chatbot System - MongoDB Demo")
    print("=" * 80)
    print()
    
    # Initialize MongoDB backend
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("❌ ERROR: MONGODB_URI not found in .env file!")
        return
    
    print(f"📦 Connecting to MongoDB...")
    backend = MongoDBBackend(uri=mongo_uri)
    
    # Test connection
    if not await backend.ping():
        print("❌ Could not connect to MongoDB!")
        print("   Please check your connection string.")
        return
    
    print("✅ MongoDB connected successfully!")
    print()
    
    # Initialize components
    memory_manager = MemoryManager(backend)
    persona_manager = PersonaManager()
    tone_detector = ToneDetector()
    context_builder = ContextBuilder()
    
    # Load persona from config
    persona_manager.load_from_config("config/persona.yaml")
    persona = persona_manager.get_persona()
    
    print(f"🎭 Persona Loaded: {persona['name']}")
    print(f"   {persona['tagline']}")
    print()
    
    # User info
    user_id = "demo_user_001"
    session_id = "session_001"
    
    print("=" * 80)
    print("💬 Conversation Simulation")
    print("=" * 80)
    print()
    
    # Simulate conversation exchanges
    conversations = [
        {
            "user": "Hey! I'm Alex and I love hiking",
            "context": "First meeting, enthusiastic tone"
        },
        {
            "user": "What do you like to do?",
            "context": "Curious, friendly"
        },
        {
            "user": "I had a rough day at work today...",
            "context": "Tired, seeking support"
        },
        {
            "user": "Remember when I told you about hiking?",
            "context": "Testing memory recall"
        }
    ]
    
    for i, conv in enumerate(conversations, 1):
        print(f"Turn {i}")
        print("-" * 40)
        
        user_message = conv["user"]
        print(f"👤 User: {user_message}")
        
        # Detect tone
        tone_result = tone_detector.detect_tone(user_message)
        print(f"   🎯 Detected tone: {tone_result['primary_emotion']} (confidence: {tone_result['confidence']:.2f})")
        
        # Get/update session context
        session = await memory_manager.get_session_context(session_id, user_id)
        session.add_exchange("user", user_message, {"tone": tone_result})
        await memory_manager.save_session_context(session)
        
        # Extract info from message (simple keyword extraction for demo)
        extracted_info = {}
        if "i'm" in user_message.lower() or "i am" in user_message.lower():
            # Extract name
            words = user_message.split()
            for idx, word in enumerate(words):
                if word.lower() in ["i'm", "i am"] and idx + 1 < len(words):
                    extracted_info["name"] = words[idx + 1].strip("!.,")
        
        if any(word in user_message.lower() for word in ["love", "like", "enjoy"]):
            # Extract interests
            if "hiking" in user_message.lower():
                extracted_info["interests"] = ["hiking"]
        
        # Update user profile
        if extracted_info:
            await memory_manager.extract_and_update_profile(user_id, user_message, extracted_info)
            print(f"   💾 Stored: {extracted_info}")
        
        # Get user profile to show memory
        profile = await memory_manager.get_user_profile(user_id)
        if profile.name or profile.preferences.get("interests"):
            print(f"   🧠 Memory: ", end="")
            if profile.name:
                print(f"Name={profile.name}", end=" ")
            if profile.preferences.get("interests"):
                print(f"Interests={profile.preferences['interests']}", end="")
            print()
        
        # Build context for response
        memory_context = await memory_manager.build_context_for_llm(user_id, session_id)
        
        # Generate a simple rule-based response (since we don't have API key)
        bot_response = generate_demo_response(user_message, persona, tone_result, memory_context)
        print(f"🤖 {persona['name']}: {bot_response}")
        
        # Save bot response to session
        session.add_exchange("assistant", bot_response)
        await memory_manager.save_session_context(session)
        
        print()
    
    print("=" * 80)
    print("📊 Memory Stats")
    print("=" * 80)
    
    # Show final user profile
    profile = await memory_manager.get_user_profile(user_id)
    print(f"User Profile for {user_id}:")
    print(f"  Name: {profile.name}")
    print(f"  Interests: {', '.join(profile.preferences.get('interests', []))}")
    print(f"  Total Interactions: {profile.interaction_count}")
    print(f"  First Seen: {profile.first_seen}")
    print(f"  Last Seen: {profile.last_seen}")
    print()
    
    print("✅ Demo completed successfully!")
    print("   The conversation data is now stored in your MongoDB database.")
    print("   You can restart this demo and the chatbot will remember the user!")
    
    # Disconnect
    await backend.disconnect()


def generate_demo_response(user_message: str, persona: dict, tone: dict, context: dict) -> str:
    """Generate a simple rule-based response for demo purposes."""
    
    name = context.get("user_profile", {}).get("name")
    interests = context.get("user_profile", {}).get("interests", [])
    emotion = tone.get("primary_emotion", "neutral")
    
    # Personality-based responses
    responses = []
    
    if "hey" in user_message.lower() or "hi" in user_message.lower():
        if name:
            responses.append(f"hey {name}! what's up? 😊")
        else:
            responses.append("hey there! what's good?")
    
    elif "love" in user_message.lower() or "like" in user_message.lower():
        if "hiking" in user_message.lower():
            responses.append("omg hiking is amazing! there's something about being in nature that just hits different, you know?")
        else:
            responses.append("that's so cool! i love when people are passionate about things")
    
    elif "what do you" in user_message.lower():
        responses.append("honestly? i'm all about good conversations and connecting with people. also obsessed with music and late night thoughts lol")
    
    elif "rough day" in user_message.lower() or emotion in ["sad", "frustrated"]:
        responses.append("aw i'm sorry you're going through it :( wanna talk about it? sometimes venting helps")
    
    elif "remember" in user_message.lower():
        if interests:
            responses.append(f"of course! you mentioned you're into {', '.join(interests)}! how could i forget? 😄")
        else:
            responses.append("hmm, refresh my memory? what are you thinking of?")
    
    else:
        responses.append("interesting! tell me more")
    
    return responses[0] if responses else "yeah totally get that"


if __name__ == "__main__":
    print()
    print("Starting chatbot system with MongoDB...")
    print()
    
    try:
        asyncio.run(simulate_conversation())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


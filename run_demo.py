"""
Standalone demo script - Shows the chatbot system with MongoDB.
Run this directly to see the system in action!
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import yaml

# Load environment variables
load_dotenv()


class SimpleChatbot:
    """Simplified chatbot for demo purposes."""
    
    def __init__(self, mongodb_uri: str):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.persona = None
        
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            await self.client.admin.command('ping')
            self.db = self.client.chatbot_memory
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def load_persona(self, config_path: str):
        """Load persona from YAML config."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.persona = config.get('persona', {})
                return True
        except Exception as e:
            print(f"Error loading persona: {e}")
            return False
    
    async def get_user_profile(self, user_id: str):
        """Get user profile from MongoDB."""
        doc = await self.db.profiles.find_one({"user_id": user_id})
        if doc:
            return doc
        return {
            "user_id": user_id,
            "name": None,
            "interests": [],
            "interaction_count": 0,
            "created_at": datetime.utcnow()
        }
    
    async def save_user_profile(self, profile: dict):
        """Save user profile to MongoDB."""
        profile["last_updated"] = datetime.utcnow()
        await self.db.profiles.update_one(
            {"user_id": profile["user_id"]},
            {"$set": profile},
            upsert=True
        )
    
    async def save_conversation(self, user_id: str, user_msg: str, bot_response: str):
        """Save conversation to MongoDB."""
        await self.db.conversations.insert_one({
            "user_id": user_id,
            "user_message": user_msg,
            "bot_response": bot_response,
            "timestamp": datetime.utcnow()
        })
    
    def detect_emotion(self, text: str) -> str:
        """Simple emotion detection."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["love", "happy", "great", "amazing", "awesome"]):
            return "joyful"
        elif any(word in text_lower for word in ["sad", "rough", "bad", "terrible", "upset"]):
            return "sad"
        elif any(word in text_lower for word in ["angry", "mad", "frustrated", "annoyed"]):
            return "frustrated"
        elif "?" in text:
            return "curious"
        else:
            return "neutral"
    
    def generate_response(self, user_message: str, profile: dict, emotion: str) -> str:
        """Generate a response based on user message and context."""
        
        name = profile.get("name")
        interests = profile.get("interests", [])
        
        # Greeting responses
        if any(word in user_message.lower() for word in ["hey", "hi", "hello", "sup"]):
            if name:
                return f"hey {name}! what's up?"
            return "hey there! what's good?"
        
        # Name introduction
        if "i'm" in user_message.lower() or "i am" in user_message.lower():
            words = user_message.split()
            for i, word in enumerate(words):
                if word.lower() in ["i'm", "am"] and i + 1 < len(words):
                    possible_name = words[i + 1].strip("!.,")
                    if possible_name and not possible_name.lower() in ["a", "an", "the"]:
                        return f"nice to meet you, {possible_name}! i'm Luna"
        
        # Interest responses
        if "love" in user_message.lower() or "like" in user_message.lower():
            if "hiking" in user_message.lower():
                return "omg hiking is amazing! there's something about being in nature that just hits different, you know?"
            elif "music" in user_message.lower():
                return "yesss music is life! what kind of stuff are you into?"
            return "that's so cool! i love when people are passionate about things"
        
        # What do you like/do questions
        if "what do you" in user_message.lower() or "what are you" in user_message.lower():
            return "honestly? i'm all about good conversations and connecting with people. also obsessed with music and late night thoughts lol"
        
        # Sad/rough day responses
        if emotion == "sad":
            return "aw i'm sorry you're going through it :( wanna talk about it? sometimes venting helps"
        
        # Memory recall
        if "remember" in user_message.lower():
            if interests:
                return f"of course! you mentioned you're into {', '.join(interests[:2])}! how could i forget?"
            return "hmm, refresh my memory? what are you thinking of?"
        
        # Default responses based on emotion
        if emotion == "joyful":
            return "that's awesome! i love the energy"
        elif emotion == "curious":
            return "interesting question! what made you think of that?"
        
        return "yeah totally get that. tell me more!"
    
    async def extract_info(self, message: str, profile: dict):
        """Extract information from user message."""
        message_lower = message.lower()
        updated = False
        
        # Extract name
        if "i'm" in message_lower or "i am" in message_lower:
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["i'm", "am"] and i + 1 < len(words):
                    possible_name = words[i + 1].strip("!.,")
                    if possible_name and len(possible_name) > 1:
                        if possible_name.lower() not in ["a", "an", "the", "so", "very", "really"]:
                            profile["name"] = possible_name.capitalize()
                            updated = True
        
        # Extract interests
        interest_keywords = {
            "hiking": "hiking",
            "music": "music",
            "gaming": "gaming",
            "reading": "reading",
            "cooking": "cooking",
            "travel": "travel",
            "photography": "photography",
            "sports": "sports"
        }
        
        for keyword, interest in interest_keywords.items():
            if keyword in message_lower:
                if interest not in profile.get("interests", []):
                    if "interests" not in profile:
                        profile["interests"] = []
                    profile["interests"].append(interest)
                    updated = True
        
        return updated


async def run_demo():
    """Run the chatbot demo."""
    
    print("=" * 80)
    print("HUMAN-LIKE CHATBOT SYSTEM - Live Demo")
    print("=" * 80)
    print()
    
    # Get MongoDB URI
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("[ERROR] MONGODB_URI not found in .env file!")
        return
    
    # Initialize chatbot
    chatbot = SimpleChatbot(mongodb_uri)
    
    # Connect to MongoDB
    print("[*] Connecting to MongoDB Atlas...")
    if not await chatbot.connect():
        print("[ERROR] Failed to connect to MongoDB!")
        return
    
    print("[OK] Connected to MongoDB successfully!")
    print()
    
    # Load persona
    print("[*] Loading persona...")
    if not chatbot.load_persona("config/persona.yaml"):
        print("[ERROR] Failed to load persona!")
        return
    
    persona = chatbot.persona
    print(f"[OK] Persona: {persona.get('name', 'Luna')}")
    print(f"     {persona.get('tagline', 'Your empathetic AI companion')}")
    print()
    
    # Demo conversation
    user_id = "demo_user_001"
    
    print("=" * 80)
    print("CONVERSATION DEMO")
    print("=" * 80)
    print()
    
    # Get user profile
    profile = await chatbot.get_user_profile(user_id)
    
    # Conversation turns
    conversations = [
        "Hey! I'm Alex and I love hiking",
        "What do you like to do?",
        "I had a rough day at work today...",
        "Remember when I told you about hiking?",
        "Do you think we could be friends?"
    ]
    
    for i, user_msg in enumerate(conversations, 1):
        print("-" * 80)
        print(f"Turn {i}")
        print("-" * 80)
        print()
        
        # User message
        print(f"[USER] {user_msg}")
        
        # Detect emotion
        emotion = chatbot.detect_emotion(user_msg)
        print(f"       Detected emotion: {emotion}")
        
        # Extract and update profile
        info_updated = await chatbot.extract_info(user_msg, profile)
        if info_updated:
            profile["interaction_count"] = profile.get("interaction_count", 0) + 1
            await chatbot.save_user_profile(profile)
            
            # Show what was stored
            stored = []
            if profile.get("name"):
                stored.append(f"Name={profile['name']}")
            if profile.get("interests"):
                stored.append(f"Interests={', '.join(profile['interests'])}")
            if stored:
                print(f"       Stored: {' | '.join(stored)}")
        
        # Generate response
        bot_response = chatbot.generate_response(user_msg, profile, emotion)
        
        # Save conversation
        await chatbot.save_conversation(user_id, user_msg, bot_response)
        
        # Display response
        print()
        print(f"[LUNA] {bot_response}")
        print()
    
    # Show memory stats
    print("=" * 80)
    print("MEMORY & ANALYTICS")
    print("=" * 80)
    print()
    
    print("User Profile:")
    print(f"  - User ID: {profile['user_id']}")
    print(f"  - Name: {profile.get('name', 'Not provided')}")
    print(f"  - Interests: {', '.join(profile.get('interests', [])) or 'None yet'}")
    print(f"  - Total Interactions: {profile.get('interaction_count', 0)}")
    print(f"  - Created: {profile.get('created_at', 'Unknown')}")
    print()
    
    # Count conversations in DB
    conv_count = await chatbot.db.conversations.count_documents({"user_id": user_id})
    print(f"Conversation History:")
    print(f"  - Total messages stored: {conv_count}")
    print()
    
    print("[OK] Demo completed successfully!")
    print()
    print("Your MongoDB database now contains:")
    print("   - User profiles with extracted information")
    print("   - Complete conversation history")
    print("   - Emotion and context tracking")
    print()
    print("Try running this again - the bot will remember the user!")
    
    # Cleanup
    if chatbot.client:
        chatbot.client.close()


if __name__ == "__main__":
    print()
    print("Starting chatbot demo...")
    print()
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


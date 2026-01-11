"""
Ultra-Interactive Web-based chatbot with stunning visuals and unique features.
"""
import os
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
import yaml

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Luna - Interactive Chatbot")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    emotion: str
    memory_updated: bool


# Global variables
mongodb_client = None
db = None
persona = None
gemini_model = None


async def init_services():
    """Initialize services."""
    global mongodb_client, db, persona, gemini_model
    
    # MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        mongodb_client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = mongodb_client.chatbot_memory
        print("[OK] MongoDB connected")
    
    # Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        print("[OK] Gemini API configured")
    
    # Persona
    try:
        with open("config/persona.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            persona = config.get('persona', {})
        print(f"[OK] Persona loaded: {persona.get('name', 'Luna')}")
    except Exception as e:
        print(f"[WARN] Could not load persona: {e}")
        persona = {"name": "Luna", "age": 23}


@app.on_event("startup")
async def startup_event():
    await init_services()


@app.on_event("shutdown")
async def shutdown_event():
    if mongodb_client:
        mongodb_client.close()


def detect_emotion(text: str) -> str:
    """Detect emotion from text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["love", "happy", "great", "amazing", "awesome", "excited", "yay", "fantastic"]):
        return "joyful"
    elif any(word in text_lower for word in ["sad", "rough", "bad", "terrible", "upset", "depressed", "crying"]):
        return "sad"
    elif any(word in text_lower for word in ["angry", "mad", "frustrated", "annoyed", "furious"]):
        return "frustrated"
    elif any(word in text_lower for word in ["scared", "afraid", "nervous", "worried", "anxious"]):
        return "anxious"
    elif "?" in text:
        return "curious"
    else:
        return "neutral"


async def get_user_profile(user_id: str) -> Dict:
    """Get user profile."""
    if db is None:
        return {"user_id": user_id, "name": None, "interests": [], "interaction_count": 0}
    
    doc = await db.profiles.find_one({"user_id": user_id})
    if doc:
        return doc
    
    return {
        "user_id": user_id,
        "name": None,
        "interests": [],
        "interaction_count": 0,
        "created_at": datetime.utcnow()
    }


async def save_user_profile(profile: Dict):
    """Save user profile."""
    if db is None:
        return
    
    profile["last_updated"] = datetime.utcnow()
    await db.profiles.update_one(
        {"user_id": profile["user_id"]},
        {"$set": profile},
        upsert=True
    )


async def extract_info(message: str, profile: Dict) -> bool:
    """Extract info from message."""
    message_lower = message.lower()
    updated = False
    
    # Extract name
    if ("i'm" in message_lower or "i am" in message_lower or "my name is" in message_lower):
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() in ["i'm", "am", "is"] and i + 1 < len(words):
                possible_name = words[i + 1].strip("!.,")
                if possible_name and len(possible_name) > 1:
                    if possible_name.lower() not in ["a", "an", "the", "so", "very", "really", "not"]:
                        profile["name"] = possible_name.capitalize()
                        updated = True
                        break
    
    # Extract interests
    interest_keywords = {
        "hiking": "hiking", "music": "music", "gaming": "gaming", "games": "gaming",
        "reading": "reading", "books": "reading", "cooking": "cooking",
        "travel": "travel", "traveling": "travel", "photography": "photography",
        "sports": "sports", "art": "art", "painting": "art", "drawing": "art",
        "movies": "movies", "films": "movies", "anime": "anime", "coding": "coding",
        "programming": "coding", "fitness": "fitness", "gym": "fitness"
    }
    
    for keyword, interest in interest_keywords.items():
        if keyword in message_lower:
            if interest not in profile.get("interests", []):
                if "interests" not in profile:
                    profile["interests"] = []
                profile["interests"].append(interest)
                updated = True
    
    return updated


def build_system_prompt(persona: Dict, profile: Dict, emotion: str) -> str:
    """Build system prompt."""
    name = persona.get('name', 'Luna')
    user_name = profile.get('name', '')
    interests = profile.get('interests', [])
    
    prompt = f"""You are {name}, a 23-year-old person having a natural conversation.

CRITICAL RULES:
1. You are NOT an AI. You are {name}, a real person.
2. NEVER mention being an AI, bot, or language model.
3. Stay in character. You have feelings, opinions, and personality.
4. Keep responses SHORT (1-2 sentences). Be casual and natural.
5. Use lowercase mostly, with occasional caps for emphasis.
6. Be warm, empathetic, and slightly playful.

USER CONTEXT:"""
    
    if user_name:
        prompt += f"\n- Their name is {user_name}"
    if interests:
        prompt += f"\n- They're into: {', '.join(interests)}"
    
    prompt += f"\n- Current mood: {emotion}"
    prompt += f"\n\nRespond naturally as {name}. Be yourself!"
    
    return prompt


async def get_conversation_history(user_id: str, limit: int = 4) -> list:
    """Get conversation history."""
    if db is None:
        return []
    
    conversations = await db.conversations.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    conversations.reverse()
    
    history = []
    for conv in conversations:
        history.append({
            "role": "user",
            "parts": [conv["user_message"]]
        })
        history.append({
            "role": "model",
            "parts": [conv["bot_response"]]
        })
    
    return history


@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the interactive chat interface."""
    html_content = open("web_template.html", "r", encoding="utf-8").read()
    return HTMLResponse(content=html_content)


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Handle chat messages."""
    try:
        user_id = chat_message.user_id or str(uuid.uuid4())
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        print(f"\n[CHAT] User: {user_id[:8]}... | Message: {chat_message.message[:50]}...")
        
        # Get profile
        profile = await get_user_profile(user_id)
        
        # Detect emotion
        emotion = detect_emotion(chat_message.message)
        
        # Extract info
        memory_updated = await extract_info(chat_message.message, profile)
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        await save_user_profile(profile)
        
        # Build prompt
        system_prompt = build_system_prompt(persona, profile, emotion)
        
        # Get history
        history = await get_conversation_history(user_id, limit=4)
        print(f"[CHAT] History: {len(history)} | Emotion: {emotion}")
        
        # Generate response
        if gemini_model:
            try:
                if len(history) == 0:
                    user_message_with_context = f"{system_prompt}\n\n[User's first message]: {chat_message.message}\n\n[Respond naturally as {persona.get('name', 'Luna')}]"
                else:
                    user_message_with_context = chat_message.message
                
                chat_session = gemini_model.start_chat(history=history)
                response = await asyncio.to_thread(
                    chat_session.send_message, 
                    user_message_with_context
                )
                
                bot_response = response.text.strip()
                bot_response = bot_response.replace('[', '').replace(']', '')
                
                if len(bot_response) > 300:
                    sentences = bot_response.split('. ')
                    bot_response = '. '.join(sentences[:3])
                    if not bot_response.endswith(('.', '!', '?')):
                        bot_response += '.'
                
                bot_response = bot_response.replace("I'm an AI", "i'm Luna")
                bot_response = bot_response.replace("I am an AI", "i'm Luna")
                bot_response = bot_response.replace("as an AI", "")
                bot_response = bot_response.replace("language model", "person")
                
            except Exception as e:
                print(f"Gemini error: {e}")
                import traceback
                traceback.print_exc()
                bot_response = "sorry, my brain just glitched lol. what were you saying?"
        else:
            bot_response = "hey! looks like i'm having connection issues. try again?"
        
        # Save conversation
        if db is not None:
            await db.conversations.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "user_message": chat_message.message,
                "bot_response": bot_response,
                "emotion": emotion,
                "timestamp": datetime.utcnow()
            })
            print(f"[CHAT] Saved | Luna: {bot_response[:60]}...")
        
        return ChatResponse(
            response=bot_response,
            user_id=user_id,
            session_id=session_id,
            emotion=emotion,
            memory_updated=memory_updated
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "mongodb": "connected" if db is not None else "disconnected",
        "gemini": "configured" if gemini_model is not None else "not configured",
        "persona": persona.get('name', 'Unknown') if persona is not None else "Not loaded"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("Starting Interactive Luna Chatbot...")
    print("=" * 80)
    print()
    print("Open: http://localhost:8000")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


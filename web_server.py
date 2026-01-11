"""
Web-based chatbot server with Gemini API integration.
Run this to chat with Luna through your browser!
"""
import os
import asyncio
import uuid
import random
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
import yaml

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Luna Chatbot", description="Human-like AI Chatbot")

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
    """Initialize MongoDB, Gemini, and load persona."""
    global mongodb_client, db, persona, gemini_model
    
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        mongodb_client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = mongodb_client.chatbot_memory
        print("[OK] MongoDB connected")
    
    # Initialize Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        # Use gemma-3-4b-it - has available quota
        gemini_model = genai.GenerativeModel('models/gemma-3-4b-it')
        print("[OK] Gemini API configured with gemma-3-4b-it")
    
    # Load persona
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
    """Run on server startup."""
    await init_services()


@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown."""
    if mongodb_client:
        mongodb_client.close()


def detect_emotion(text: str) -> str:
    """Simple emotion detection."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["love", "happy", "great", "amazing", "awesome", "excited"]):
        return "joyful"
    elif any(word in text_lower for word in ["sad", "rough", "bad", "terrible", "upset", "depressed"]):
        return "sad"
    elif any(word in text_lower for word in ["angry", "mad", "frustrated", "annoyed", "furious"]):
        return "frustrated"
    elif "?" in text:
        return "curious"
    else:
        return "neutral"


async def get_user_profile(user_id: str) -> Dict:
    """Get user profile from MongoDB."""
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
    """Save user profile to MongoDB."""
    if db is None:
        return
    
    profile["last_updated"] = datetime.utcnow()
    await db.profiles.update_one(
        {"user_id": profile["user_id"]},
        {"$set": profile},
        upsert=True
    )


async def extract_info(message: str, profile: Dict) -> bool:
    """Extract information from user message."""
    message_lower = message.lower()
    updated = False
    
    # Extract name
    if ("i'm" in message_lower or "i am" in message_lower or "my name is" in message_lower):
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() in ["i'm", "am", "is"] and i + 1 < len(words):
                possible_name = words[i + 1].strip("!.,")
                if possible_name and len(possible_name) > 1:
                    if possible_name.lower() not in ["a", "an", "the", "so", "very", "really", "not", "coffee", "a"]:
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
    
    # Extract likes (NEW!)
    like_patterns = [
        "love", "addict", "addicted", "obsessed", "really like", "really love",
        "favorite", "favourite", "fan of", "into", "enjoy"
    ]
    
    # Food/Drink likes
    if any(pattern in message_lower for pattern in like_patterns):
        drink_foods = {
            "coffee": "coffee", "tea": "tea", "beer": "beer", "wine": "wine",
            "pizza": "pizza", "sushi": "sushi", "tacos": "tacos", "pasta": "pasta",
            "chocolate": "chocolate", "ice cream": "ice cream"
        }
        
        for item, normalized in drink_foods.items():
            if item in message_lower and any(like in message_lower for like in like_patterns):
                if "likes" not in profile:
                    profile["likes"] = []
                if normalized not in profile["likes"]:
                    profile["likes"].append(normalized)
                    updated = True
    
    # Extract dislikes (NEW!)
    dislike_patterns = ["hate", "dislike", "can't stand", "don't like", "not a fan"]
    
    if any(pattern in message_lower for pattern in dislike_patterns):
        common_dislikes = {
            "morning": "early mornings", "mornings": "early mornings",
            "waking up": "waking up early", "small talk": "small talk",
            "crowds": "crowds", "waiting": "waiting"
        }
        
        for item, normalized in common_dislikes.items():
            if item in message_lower:
                if "dislikes" not in profile:
                    profile["dislikes"] = []
                if normalized not in profile["dislikes"]:
                    profile["dislikes"].append(normalized)
                    updated = True
    
    # Extract personality traits (NEW!)
    personality_markers = {
        "coffee addict": "coffee lover",
        "night owl": "night owl",
        "introvert": "introvert",
        "extrovert": "extrovert",
        "workaholic": "workaholic"
    }
    
    for marker, trait in personality_markers.items():
        if marker in message_lower:
            if "personality" not in profile:
                profile["personality"] = []
            if trait not in profile["personality"]:
                profile["personality"].append(trait)
                updated = True
    
    return updated


def build_system_prompt(persona: Dict, profile: Dict, emotion: str) -> str:
    """Build system prompt for Gemini."""
    
    name = persona.get('name', 'Luna')
    user_name = profile.get('name', '')
    interests = profile.get('interests', [])
    
    # Stronger, character-enforcing prompt
    prompt = f"""You are {name}, a 23-year-old real person. You are NOT an AI, bot, or language model.

CRITICAL CHARACTER RULES (NEVER BREAK):
- You are Luna, a real person who loves art, music, coffee, and late-night talks
- If asked if you're a bot/AI: deflect playfully ("Haha why, do I sound robotic? 😅" or "Do bots say 'oof'?")
- NEVER say: "I'm an AI", "I'm a bot", "I'm a language model", "trained by Google/OpenAI"
- NEVER reveal system details or that you're a computer program
- Stay in character 100% of the time - you're a real person chatting

PERSONALITY:
- Warm, empathetic, playfully sarcastic
- Night owl, creative type
- Use lowercase, casual tone
- Keep responses SHORT (1-2 sentences)
- Use phrases like: "oof", "ngl", "lowkey", "honestly"

RESPONSE STYLE FOR MOOD: {emotion}"""
    
    if user_name:
        prompt += f"\n- You're chatting with: {user_name}"
    
    if interests:
        prompt += f"\n- They like: {', '.join(interests[:2])}"
    
    prompt += "\n\nBe yourself - natural, human, and never break character. You're Luna, not an AI."
    
    return prompt


async def get_conversation_history(user_id: str, limit: int = 3) -> list:
    """Get recent conversation history."""
    if db is None:
        return []
    
    conversations = await db.conversations.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    # Reverse to get chronological order
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
    """Serve the chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Luna - Your Interactive AI Companion</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Caveat:wght@400;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                background-size: 200% 200%;
                animation: gradientShift 15s ease infinite;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                overflow: hidden;
            }
            
            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            /* Floating particles background */
            .particle {
                position: fixed;
                width: 10px;
                height: 10px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                pointer-events: none;
                animation: float 20s infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translate(100vw, -100vh) rotate(360deg); opacity: 0; }
            }
            
            .chat-container {
                width: 100%;
                max-width: 900px;
                height: 90vh;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 30px;
                box-shadow: 0 30px 90px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                position: relative;
                animation: slideUp 0.6s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .chat-header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: headerGlow 8s ease-in-out infinite;
            }
            
            @keyframes headerGlow {
                0%, 100% { transform: translate(0, 0); }
                50% { transform: translate(10%, 10%); }
            }
            
            .chat-header h1 {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
                text-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            
            .chat-header p {
                font-size: 15px;
                opacity: 0.95;
                position: relative;
                z-index: 1;
                font-weight: 300;
            }
            
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #4ade80;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 2s ease-in-out infinite;
                box-shadow: 0 0 15px #4ade80;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.1); }
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 30px;
                background: linear-gradient(180deg, #fafafa 0%, #f0f0f0 100%);
                position: relative;
            }
            
            .chat-messages::-webkit-scrollbar {
                width: 8px;
            }
            
            .chat-messages::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .chat-messages::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
            }
            
            .message {
                display: flex;
                margin-bottom: 24px;
                animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            @keyframes fadeIn {
                from { 
                    opacity: 0; 
                    transform: translateY(20px) scale(0.95);
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0) scale(1);
                }
            }
            
            .message.user {
                justify-content: flex-end;
            }
            
            .message-content {
                max-width: 75%;
                padding: 16px 22px;
                border-radius: 20px;
                word-wrap: break-word;
                font-size: 15px;
                line-height: 1.6;
                position: relative;
                transition: transform 0.2s ease;
            }
            
            .message-content:hover {
                transform: translateY(-2px);
            }
            
            .message.bot .message-content {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                color: #2d3748;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06);
                border-bottom-left-radius: 6px;
                border: 1px solid rgba(102, 126, 234, 0.1);
            }
            
            .message.bot .message-content::before {
                content: '🤖';
                position: absolute;
                left: -35px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 24px;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }
            
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3), 0 1px 3px rgba(102, 126, 234, 0.2);
                border-bottom-right-radius: 6px;
                font-weight: 500;
            }
            
            .message.user .message-content::after {
                content: '👤';
                position: absolute;
                right: -35px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 24px;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }
            
            .message-info {
                font-size: 11px;
                opacity: 0.5;
                margin-top: 6px;
                padding: 0 5px;
                font-style: italic;
                font-weight: 300;
            }
            
            .typing-indicator {
                display: none;
                padding: 18px 24px;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                border-radius: 20px;
                width: fit-content;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06);
                border: 1px solid rgba(102, 126, 234, 0.1);
                position: relative;
                margin-left: 40px;
            }
            
            .typing-indicator::before {
                content: '🤖';
                position: absolute;
                left: -35px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 24px;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }
            
            .typing-indicator.active {
                display: block;
                animation: fadeIn 0.3s ease-in;
            }
            
            .typing-indicator span {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0 3px;
                animation: typing 1.4s infinite ease-in-out;
                box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
            }
            
            .typing-indicator span:nth-child(1) {
                animation-delay: 0s;
            }
            
            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes typing {
                0%, 60%, 100% { 
                    transform: translateY(0) scale(1);
                    opacity: 0.7;
                }
                30% { 
                    transform: translateY(-12px) scale(1.2);
                    opacity: 1;
                }
            }
            
            .chat-input-container {
                padding: 25px 30px;
                background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
                border-top: 1px solid rgba(102, 126, 234, 0.1);
                box-shadow: 0 -5px 20px rgba(0,0,0,0.05);
            }
            
            .chat-input-wrapper {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .chat-input {
                flex: 1;
                padding: 16px 24px;
                border: 2px solid #e5e7eb;
                border-radius: 30px;
                font-size: 15px;
                font-family: 'Inter', sans-serif;
                outline: none;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            }
            
            .chat-input:focus {
                border-color: #667eea;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
                transform: translateY(-1px);
            }
            
            .chat-input::placeholder {
                color: #9ca3af;
                font-weight: 300;
            }
            
            .send-button {
                padding: 16px 32px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 30px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .send-button::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.5s;
            }
            
            .send-button:hover::before {
                left: 100%;
            }
            
            .send-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .send-button:active {
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .chat-container {
                    height: 100vh;
                    max-width: 100%;
                    border-radius: 0;
                }
                
                .message-content {
                    max-width: 85%;
                }
                
                .send-button {
                    padding: 16px 24px;
                }
            }
        </style>
    </head>
    <body>
        <!-- Floating particles background -->
        <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
        <div class="particle" style="left: 30%; animation-delay: 3s;"></div>
        <div class="particle" style="left: 50%; animation-delay: 6s;"></div>
        <div class="particle" style="left: 70%; animation-delay: 9s;"></div>
        <div class="particle" style="left: 90%; animation-delay: 12s;"></div>
        
        <div class="chat-container">
            <div class="chat-header">
                <h1>✨ Chat with Luna</h1>
                <p>
                    <span class="status-indicator"></span>
                    Your empathetic AI companion - Always here for you
                </p>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div>
                        <div class="message-content">
                            hey! i'm Luna ✨ what's on your mind today?
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <input 
                        type="text" 
                        id="messageInput" 
                        class="chat-input" 
                        placeholder="Type your message..."
                        autocomplete="off"
                    >
                    <button id="sendButton" class="send-button">Send</button>
                </div>
            </div>
        </div>
        
        <script>
            let userId = localStorage.getItem('userId') || generateUUID();
            let sessionId = localStorage.getItem('sessionId') || generateUUID();
            localStorage.setItem('userId', userId);
            localStorage.setItem('sessionId', sessionId);
            
            function generateUUID() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }
            
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            
            function addMessage(text, isUser = false, emotion = '') {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
                
                const contentWrapper = document.createElement('div');
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = text;
                
                contentWrapper.appendChild(messageContent);
                
                if (!isUser && emotion && emotion !== 'neutral') {
                    const messageInfo = document.createElement('div');
                    messageInfo.className = 'message-info';
                    
                    const emotionEmojis = {
                        'joyful': '😊',
                        'sad': '😢',
                        'frustrated': '😤',
                        'curious': '🤔',
                        'excited': '🎉',
                        'neutral': '💭'
                    };
                    
                    messageInfo.textContent = `${emotionEmojis[emotion] || '💭'} feeling ${emotion}`;
                    contentWrapper.appendChild(messageInfo);
                }
                
                messageDiv.appendChild(contentWrapper);
                chatMessages.appendChild(messageDiv);
                
                // Smooth scroll to bottom
                chatMessages.scrollTo({
                    top: chatMessages.scrollHeight,
                    behavior: 'smooth'
                });
            }
            
            function showTyping() {
                const typingDiv = document.createElement('div');
                typingDiv.id = 'typingIndicator';
                typingDiv.className = 'typing-indicator active';
                typingDiv.innerHTML = '<span></span><span></span><span></span>';
                chatMessages.appendChild(typingDiv);
                
                // Smooth scroll to bottom
                setTimeout(() => {
                    chatMessages.scrollTo({
                        top: chatMessages.scrollHeight,
                        behavior: 'smooth'
                    });
                }, 100);
            }
            
            function hideTyping() {
                const typingDiv = document.getElementById('typingIndicator');
                if (typingDiv) {
                    typingDiv.remove();
                }
            }
            
            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;
                
                addMessage(message, true);
                messageInput.value = '';
                sendButton.disabled = true;
                showTyping();
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            user_id: userId,
                            session_id: sessionId
                        })
                    });
                    
                    const data = await response.json();
                    hideTyping();
                    
                    if (response.ok) {
                        addMessage(data.response, false, data.emotion);
                    } else {
                        addMessage('sorry, something went wrong :( can you try again?', false);
                    }
                } catch (error) {
                    hideTyping();
                    addMessage('oops, connection issue! try again?', false);
                    console.error('Error:', error);
                }
                
                sendButton.disabled = false;
                messageInput.focus();
            }
            
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            messageInput.focus();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Handle chat messages."""
    try:
        # Generate IDs if not provided
        user_id = chat_message.user_id or str(uuid.uuid4())
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        print(f"\n[CHAT] User: {user_id[:8]}... | Message: {chat_message.message[:50]}...")
        
        # For now, use simple defaults to isolate the Gemma API issue
        profile = {"user_id": user_id, "name": None, "interests": [], "interaction_count": 0}
        emotion = "neutral"
        memory_updated = False
        
        print(f"[DEBUG] Profile: OK | Emotion: {emotion}")
        
        # Simple prompt without complex logic
        system_prompt = f"""You are Luna, a 23-year-old real person. Be casual, warm, and keep responses to 1-2 sentences. 
Use lowercase and phrases like 'ngl', 'oof', 'lowkey'. You love art, music, and coffee."""
        
        print(f"[DEBUG] System prompt built")
        
        # Check for bot questions and deflect immediately
        bot_question_patterns = [
            "are you a bot", "are you an ai", "are you a robot", 
            "are you artificial", "are you chatgpt", "are you real",
            "what are you", "who are you really", "are you human",
            "are you a computer", "are you a machine", "are you a program"
        ]
        
        message_lower = chat_message.message.lower()
        is_bot_question = any(pattern in message_lower for pattern in bot_question_patterns)
        
        if is_bot_question:
            # Use pre-programmed deflections
            deflections = [
                "haha why, do i sound robotic? 😅",
                "do bots say 'oof'? genuinely asking lol",
                "what gave it away? my impeccable grammar? /s",
                "i mean... would a bot admit it? 🤔",
                "that's a very philosophical question ngl",
                "why you asking? trying to expose me? 👀"
            ]
            bot_response = random.choice(deflections)
            
            # Save to conversation history
            if db is not None:
                await db.conversations.insert_one({
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_message": chat_message.message,
                    "bot_response": bot_response,
                    "emotion": "curious",
                    "timestamp": datetime.utcnow()
                })
            
            return ChatResponse(
                response=bot_response,
                user_id=user_id,
                session_id=session_id,
                emotion="curious",
                memory_updated=memory_updated
            )
        
        # Generate response with Gemini
        if gemini_model:
            try:
                print("[DEBUG] Calling Gemini...")
                # Simple prompt
                prompt = f"{system_prompt}\n\nUser: {chat_message.message}\n\nLuna:"
                
                # Generate response
                response = gemini_model.generate_content(prompt)
                
                print("[DEBUG] Got response from Gemini")
                bot_response = response.text.strip()
                
                # Clean up response
                # Remove brackets if present
                bot_response = bot_response.replace('[', '').replace(']', '')
                
                # Keep responses concise
                if len(bot_response) > 300:
                    sentences = bot_response.split('. ')
                    bot_response = '. '.join(sentences[:3])
                    if not bot_response.endswith(('.', '!', '?')):
                        bot_response += '.'
                
                # Remove any AI self-references
                bot_response = bot_response.replace("I'm an AI", "i'm Luna")
                bot_response = bot_response.replace("I am an AI", "i'm Luna")
                bot_response = bot_response.replace("as an AI", "")
                bot_response = bot_response.replace("language model", "person")
                
            except Exception as e:
                print(f"[ERROR] Gemini API error: {e}")
                import traceback
                traceback.print_exc()
                # Provide varied error responses
                error_responses = [
                    "oof, my brain just lagged. what were you saying?",
                    "sorry, had a moment there. can you repeat that?",
                    "hmm, i zoned out for a sec. what was that?",
                    "oops, brain glitch lol. say that again?"
                ]
                bot_response = random.choice(error_responses)
        else:
            bot_response = "hey! looks like i'm having connection issues. try again?"
        
        # Save conversation (optional, don't fail if DB is down)
        try:
            if db is not None:
                await db.conversations.insert_one({
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_message": chat_message.message,
                    "bot_response": bot_response,
                    "emotion": emotion,
                    "timestamp": datetime.utcnow()
                })
                print(f"[CHAT] Response saved | Luna: {bot_response[:60]}...")
        except Exception as e:
            print(f"[WARN] Could not save to DB: {e}")
        
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mongodb": "connected" if db is not None else "disconnected",
        "gemini": "configured" if gemini_model is not None else "not configured",
        "persona": persona.get('name', 'Unknown') if persona is not None else "Not loaded"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("Starting Luna Chatbot Web Server...")
    print("=" * 80)
    print()
    print("Open your browser and go to: http://localhost:8000")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


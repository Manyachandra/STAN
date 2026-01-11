"""
FastAPI Server Example

Production-ready REST API for the chatbot system.

Endpoints:
- POST /chat - Send a message
- POST /start - Start a new conversation
- GET /users/{user_id}/stats - Get user statistics
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import uuid

from chatbot_system import ChatbotEngine


# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    text: str
    user_id: str
    session_id: str
    detected_tone: Optional[str] = None
    response_time_ms: float
    metadata: Optional[Dict[str, Any]] = None


class StartConversationRequest(BaseModel):
    """Request model for starting conversation."""
    user_id: str = Field(..., min_length=1, max_length=100)
    session_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    checks: Dict[str, bool]


# Initialize FastAPI app
app = FastAPI(
    title="Human-like Chatbot API",
    description="Production chatbot with emotional intelligence and memory",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot: Optional[ChatbotEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup."""
    global chatbot
    
    print("Initializing chatbot system...")
    
    chatbot = ChatbotEngine(
        persona_config_path=os.getenv("PERSONA_CONFIG", "config/persona.yaml"),
        redis_url=os.getenv("REDIS_URL"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        enable_safety=True,
        enable_tone_adaptation=True
    )
    
    # Health check
    health = await chatbot.health_check()
    if not health["overall"]:
        print("Warning: System health check failed!")
        print(health)
    else:
        print("Chatbot system initialized successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Shutting down chatbot system...")


def get_chatbot() -> ChatbotEngine:
    """Dependency to get chatbot instance."""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return chatbot


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    bot: ChatbotEngine = Depends(get_chatbot)
):
    """
    Send a message to the chatbot.
    
    Args:
        request: Chat request with user_id and message
        
    Returns:
        Chat response with bot's reply
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process message
        response = await bot.chat(
            user_id=request.user_id,
            message=request.message,
            session_id=session_id,
            metadata=request.metadata
        )
        
        return ChatResponse(
            text=response.text,
            user_id=response.user_id,
            session_id=response.session_id,
            detected_tone=response.detected_tone,
            response_time_ms=response.response_time_ms,
            metadata=response.metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start", response_model=ChatResponse)
async def start_conversation(
    request: StartConversationRequest,
    bot: ChatbotEngine = Depends(get_chatbot)
):
    """
    Start a new conversation with a greeting.
    
    Args:
        request: Start conversation request
        
    Returns:
        Chat response with greeting
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        response = await bot.start_conversation(
            user_id=request.user_id,
            session_id=session_id
        )
        
        return ChatResponse(
            text=response.text,
            user_id=response.user_id,
            session_id=response.session_id,
            detected_tone=response.detected_tone,
            response_time_ms=response.response_time_ms,
            metadata=response.metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    bot: ChatbotEngine = Depends(get_chatbot)
):
    """
    Get statistics for a specific user.
    
    Args:
        user_id: User identifier
        
    Returns:
        User statistics
    """
    try:
        stats = await bot.get_user_stats(user_id)
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check(bot: ChatbotEngine = Depends(get_chatbot)):
    """
    Check system health.
    
    Returns:
        Health status of all components
    """
    try:
        checks = await bot.health_check()
        
        status = "healthy" if checks["overall"] else "unhealthy"
        
        return HealthResponse(
            status=status,
            checks=checks
        )
    
    except Exception as e:
        return HealthResponse(
            status="error",
            checks={"error": str(e)}
        )


@app.get("/stats")
async def system_stats(bot: ChatbotEngine = Depends(get_chatbot)):
    """
    Get system-wide statistics.
    
    Returns:
        System statistics
    """
    return bot.get_system_stats()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Human-like Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


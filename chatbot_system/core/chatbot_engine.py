"""
Chatbot Engine - Main orchestrator for the conversational AI system.

Coordinates:
- Persona management
- Memory retrieval and storage
- Tone detection and adaptation
- Response generation
- Safety validation
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .persona_manager import PersonaManager
from .safety_layer import SafetyLayer
from ..memory.memory_manager import MemoryManager
from ..memory.redis_backend import RedisBackend
from ..conversation.tone_detector import ToneDetector
from ..conversation.context_builder import ContextBuilder
from ..conversation.summarizer import ConversationSummarizer
from ..integration.gemini_client import GeminiClient
from ..integration.prompt_builder import PromptBuilder


@dataclass
class ChatResponse:
    """Response from chatbot with metadata."""
    
    text: str
    user_id: str
    session_id: str
    detected_tone: Optional[str] = None
    confidence: float = 1.0
    tokens_used: int = 0
    response_time_ms: float = 0.0
    safety_passed: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "detected_tone": self.detected_tone,
            "confidence": self.confidence,
            "tokens_used": self.tokens_used,
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata or {}
        }


class ChatbotEngine:
    """
    Main chatbot engine that orchestrates all components.
    
    This is the primary interface for the chatbot system.
    """
    
    def __init__(
        self,
        persona_config_path: str,
        redis_url: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        enable_safety: bool = True,
        enable_tone_adaptation: bool = True
    ):
        """
        Initialize chatbot engine.
        
        Args:
            persona_config_path: Path to persona.yaml
            redis_url: Redis connection URL
            gemini_api_key: Gemini API key
            model: Gemini model name
            enable_safety: Enable safety validation
            enable_tone_adaptation: Enable tone adaptation
        """
        # Initialize components
        self.persona_manager = PersonaManager(persona_config_path)
        self.safety_layer = SafetyLayer()
        self.tone_detector = ToneDetector()
        self.context_builder = ContextBuilder()
        self.summarizer = ConversationSummarizer()
        self.prompt_builder = PromptBuilder()
        
        # Initialize backends
        redis_backend = RedisBackend(redis_url)
        self.memory_manager = MemoryManager(redis_backend)
        
        # Initialize Gemini client
        self.gemini_client = GeminiClient(
            api_key=gemini_api_key,
            model=model,
            temperature=0.9,  # High for natural variation
            max_tokens=500
        )
        
        # Settings
        self.enable_safety = enable_safety
        self.enable_tone_adaptation = enable_tone_adaptation
        
        # Stats
        self.total_conversations = 0
        self.total_tokens = 0
    
    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Process a user message and generate a response.
        
        Args:
            user_id: Unique user identifier
            message: User's message
            session_id: Session identifier
            metadata: Optional metadata
            
        Returns:
            ChatResponse object
        """
        import time
        start_time = time.time()
        
        try:
            # Validate input
            is_valid, error = self.gemini_client.validate_input(message)
            if not is_valid:
                return ChatResponse(
                    text="Hey, could you rephrase that?",
                    user_id=user_id,
                    session_id=session_id,
                    safety_passed=False,
                    metadata={"error": error}
                )
            
            # Check if asking if bot
            if self.persona_manager.should_deflect_bot_question(message):
                deflection = self.persona_manager.get_bot_deflection()
                return ChatResponse(
                    text=deflection,
                    user_id=user_id,
                    session_id=session_id,
                    detected_tone="curious",
                    confidence=1.0
                )
            
            # Detect tone
            detected_tone = None
            if self.enable_tone_adaptation:
                tone = self.tone_detector.detect(message)
                detected_tone = tone.primary
            
            # Load memory context
            context = await self.memory_manager.build_context_for_llm(
                user_id, session_id
            )
            
            # Get session and add user message
            session = await self.memory_manager.get_session_context(session_id, user_id)
            session.add_exchange("user", message, {"tone": detected_tone})
            await self.memory_manager.save_session_context(session)
            
            # Build system prompt
            system_prompt = self.persona_manager.get_system_prompt(
                user_context=context.get("user_profile")
            )
            
            # Add tone adaptation if enabled
            if self.enable_tone_adaptation and detected_tone:
                tone_guidance = self.tone_detector.get_response_guidance(tone)
                system_prompt = self.prompt_builder.build_tone_specific_prompt(
                    system_prompt,
                    detected_tone,
                    tone.energy_level
                )
            
            # Build context string
            user_context = self.context_builder.build_context(
                user_profile=context.get("user_profile", {}),
                conversation_history=session.get_conversation_history(),
                recent_summaries=context.get("recent_summaries", []),
                current_mood=session.current_mood,
                current_topic=session.current_topic
            )
            
            # Generate response
            response = await self.gemini_client.generate_response(
                system_prompt=system_prompt,
                conversation_history=session.get_conversation_history(),
                context=user_context
            )
            
            response_text = response.get("text", "")
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            
            # Safety validation
            if self.enable_safety:
                is_safe, error_type, error_msg = self.safety_layer.validate_response(
                    response_text,
                    context,
                    session.get_conversation_history()
                )
                
                if not is_safe:
                    # Regenerate or use fallback
                    response_text = self._get_safe_fallback(detected_tone)
            
            # Validate against persona
            is_valid, error = self.persona_manager.validate_response(response_text)
            if not is_valid:
                # Sanitize response
                response_text = self.safety_layer.sanitize_response(response_text)
            
            # Save bot response to session
            session.add_exchange("assistant", response_text)
            if detected_tone:
                session.update_mood(detected_tone)
            await self.memory_manager.save_session_context(session)
            
            # Extract and update user profile
            extracted_info = self._extract_user_info(message)
            if extracted_info:
                await self.memory_manager.extract_and_update_profile(
                    user_id, message, extracted_info
                )
            
            # Check if should summarize
            if self.summarizer.should_summarize(len(session.recent_exchanges)):
                await self._summarize_and_compress(user_id, session_id, session)
            
            # Update stats
            self.total_conversations += 1
            self.total_tokens += tokens_used
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            return ChatResponse(
                text=response_text,
                user_id=user_id,
                session_id=session_id,
                detected_tone=detected_tone,
                confidence=0.9,
                tokens_used=tokens_used,
                response_time_ms=response_time,
                safety_passed=True,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return ChatResponse(
                text="Oops, something went wrong on my end. Can you try again?",
                user_id=user_id,
                session_id=session_id,
                safety_passed=False,
                metadata={"error": str(e)}
            )
    
    async def start_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> ChatResponse:
        """
        Start a new conversation with a greeting.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            ChatResponse with greeting
        """
        # Get user profile
        profile = await self.memory_manager.get_user_profile(user_id)
        
        # Determine if returning user
        is_returning = profile.interaction_count > 0
        
        # Get appropriate opener
        greeting = self.persona_manager.get_conversation_opener(is_returning)
        
        # Create session
        session = await self.memory_manager.get_session_context(session_id, user_id)
        session.add_exchange("assistant", greeting)
        await self.memory_manager.save_session_context(session)
        
        return ChatResponse(
            text=greeting,
            user_id=user_id,
            session_id=session_id,
            detected_tone="casual",
            confidence=1.0
        )
    
    def _extract_user_info(self, message: str) -> Dict[str, List[str]]:
        """Extract user information from message."""
        extracted = {
            "interests": [],
            "likes": [],
            "dislikes": [],
            "personality_notes": []
        }
        
        message_lower = message.lower()
        
        # Extract name
        name_patterns = [
            r"(i'm|i am|my name is|call me) ([A-Z][a-z]+)",
            r"this is ([A-Z][a-z]+)"
        ]
        
        # Extract interests
        interest_patterns = [
            r"(love|like|enjoy|into|fan of) ([\w\s]+)",
            r"interested in ([\w\s]+)",
            r"hobby is ([\w\s]+)"
        ]
        
        for pattern in interest_patterns:
            import re
            matches = re.findall(pattern, message_lower)
            for match in matches:
                if isinstance(match, tuple):
                    interest = match[1].strip()
                    if len(interest) < 50:  # Reasonable length
                        extracted["interests"].append(interest)
        
        return extracted if any(extracted.values()) else {}
    
    def _get_safe_fallback(self, tone: Optional[str] = None) -> str:
        """Get a safe fallback response."""
        fallbacks = {
            "sad": "I'm here for you. Wanna talk about it?",
            "excited": "That's awesome! Tell me more!",
            "angry": "I hear you. That sounds frustrating.",
            "anxious": "Hey, it's okay. Take a breath. What's going on?",
            None: "Hmm, let me think about that differently..."
        }
        
        return fallbacks.get(tone, fallbacks[None])
    
    async def _summarize_and_compress(
        self,
        user_id: str,
        session_id: str,
        session
    ):
        """Summarize conversation and compress session."""
        summary_data = self.summarizer.summarize_conversation(
            session.recent_exchanges,
            extract_key_moments=True
        )
        
        # Create conversation summary
        from ..memory.memory_manager import ConversationSummary
        summary = ConversationSummary(
            session_id=session_id,
            user_id=user_id,
            summary=summary_data["summary"],
            key_moments=summary_data["key_moments"],
            emotional_arc=summary_data["emotional_arc"],
            topics_discussed=summary_data["topics"],
            original_message_count=summary_data["original_count"],
            tokens_saved=summary_data["tokens_saved"]
        )
        
        # Save summary
        await self.memory_manager.save_conversation_summary(summary)
        
        # Compress session (keep only recent exchanges)
        session.recent_exchanges = session.recent_exchanges[-4:]
        await self.memory_manager.save_session_context(session)
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user."""
        profile = await self.memory_manager.get_user_profile(user_id)
        summaries = await self.memory_manager.get_conversation_summaries(user_id)
        
        return {
            "user_id": user_id,
            "name": profile.name,
            "interaction_count": profile.interaction_count,
            "first_seen": profile.first_seen,
            "last_seen": profile.last_seen,
            "interests": profile.preferences.get("interests", []),
            "past_conversations": len(summaries)
        }
    
    async def reset_user_memory(self, user_id: str):
        """Reset all memory for a user (for testing/privacy)."""
        # This would clear all user data
        # Implementation depends on privacy requirements
        pass
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        return {
            "total_conversations": self.total_conversations,
            "total_tokens": self.total_tokens,
            "persona_name": self.persona_manager.name,
            "model": self.gemini_client.model_name,
            "safety_enabled": self.enable_safety,
            "tone_adaptation_enabled": self.enable_tone_adaptation
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        checks = {
            "gemini_api": False,
            "redis": False,
            "persona": bool(self.persona_manager.config),
            "overall": False
        }
        
        try:
            # Test Gemini
            checks["gemini_api"] = await self.gemini_client.test_connection()
            
            # Test Redis
            checks["redis"] = await self.memory_manager.backend.ping()
            
            # Overall health
            checks["overall"] = all([
                checks["gemini_api"],
                checks["redis"],
                checks["persona"]
            ])
            
        except Exception as e:
            print(f"Health check error: {e}")
        
        return checks
    
    def __repr__(self) -> str:
        return f"ChatbotEngine(persona={self.persona_manager.name})"


"""
Gemini Client - Handles communication with Google Gemini API.

Provides:
- Response generation
- Token management
- Error handling and retries
- Safety settings
"""

import os
from typing import Dict, List, Optional, Any
import asyncio
import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


class GeminiClient:
    """
    Client for Google Gemini API with retry logic and error handling.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.9,
        top_p: float = 0.95,
        top_k: int = 40,
        max_tokens: int = 500
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name
            temperature: Sampling temperature (0.0-1.0, higher = more creative)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        
        # Initialize model
        self.generation_config = genai.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )
        
        # Safety settings - permissive since we handle safety in-app
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using Gemini API.
        
        Args:
            system_prompt: System prompt defining persona and behavior
            conversation_history: List of message exchanges
            context: Additional context (memory, user profile, etc.)
            
        Returns:
            Dictionary with response text and metadata
        """
        try:
            # Build prompt
            full_prompt = self._build_prompt(
                system_prompt,
                conversation_history,
                context
            )
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            # Extract text
            if response.candidates:
                text = response.candidates[0].content.parts[0].text
            else:
                text = "Sorry, I couldn't generate a response right now."
            
            # Get usage metadata if available
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "response_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return {
                "text": text.strip(),
                "usage": usage,
                "model": self.model_name,
                "finish_reason": self._get_finish_reason(response)
            }
            
        except Exception as e:
            # Log error and return fallback
            print(f"Error generating response: {e}")
            raise
    
    def _build_prompt(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """Build complete prompt for Gemini."""
        parts = [system_prompt]
        
        # Add context if provided
        if context:
            parts.append(f"\n{context}")
        
        # Add conversation history
        if conversation_history:
            parts.append("\n")
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    parts.append(f"User: {content}")
                else:
                    parts.append(f"You: {content}")
        
        return "\n".join(parts)
    
    def _get_finish_reason(self, response) -> str:
        """Extract finish reason from response."""
        try:
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                return str(finish_reason)
        except:
            pass
        return "UNKNOWN"
    
    async def generate_response_streaming(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ):
        """
        Generate response with streaming (for real-time display).
        
        Args:
            system_prompt: System prompt
            conversation_history: Conversation history
            context: Additional context
            
        Yields:
            Response chunks
        """
        full_prompt = self._build_prompt(
            system_prompt,
            conversation_history,
            context
        )
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.candidates:
                    text = chunk.candidates[0].content.parts[0].text
                    yield {"text": text, "done": False}
            
            yield {"text": "", "done": True}
            
        except Exception as e:
            print(f"Streaming error: {e}")
            yield {"text": "Sorry, something went wrong.", "done": True}
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English
        return len(text) // 4
    
    def validate_input(self, text: str, max_length: int = 2000) -> tuple[bool, Optional[str]]:
        """
        Validate user input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Empty input"
        
        if len(text) > max_length:
            return False, f"Input too long (max {max_length} characters)"
        
        return True, None
    
    def set_temperature(self, temperature: float):
        """Update temperature setting."""
        if 0.0 <= temperature <= 1.0:
            self.temperature = temperature
            self.generation_config.temperature = temperature
            # Reinitialize model with new config
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model configuration."""
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_tokens": self.max_tokens
        }
    
    async def test_connection(self) -> bool:
        """
        Test API connection.
        
        Returns:
            True if connection successful
        """
        try:
            response = await self.generate_response(
                system_prompt="You are a test.",
                conversation_history=[{"role": "user", "content": "Hi"}],
                context=None
            )
            return bool(response.get("text"))
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"GeminiClient(model={self.model_name}, temp={self.temperature})"


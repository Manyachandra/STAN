"""
Prompt Builder - Constructs dynamic prompts for the LLM.

Combines:
- System prompt (persona)
- User context (memory)
- Conversation history
- Tone guidance
- Safety instructions
"""

from typing import Dict, List, Optional, Any


class PromptBuilder:
    """
    Builds optimized prompts that maintain character while providing context.
    """
    
    def __init__(self, max_prompt_tokens: int = 2000):
        """
        Initialize prompt builder.
        
        Args:
            max_prompt_tokens: Maximum tokens for entire prompt
        """
        self.max_prompt_tokens = max_prompt_tokens
    
    def build_complete_prompt(
        self,
        system_prompt: str,
        user_context: str,
        tone_guidance: Optional[Dict[str, Any]] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Build complete system prompt with all context.
        
        Args:
            system_prompt: Base persona system prompt
            user_context: User-specific context (memory, profile)
            tone_guidance: Guidance for tone adaptation
            additional_instructions: Any additional instructions
            
        Returns:
            Complete system prompt
        """
        parts = [system_prompt]
        
        # Add user context if available
        if user_context and user_context.strip():
            parts.append(f"\n{user_context}")
        
        # Add tone guidance
        if tone_guidance:
            tone_instructions = self._format_tone_guidance(tone_guidance)
            if tone_instructions:
                parts.append(f"\n{tone_instructions}")
        
        # Add any additional instructions
        if additional_instructions:
            parts.append(f"\n{additional_instructions}")
        
        # Add reminder about staying in character
        parts.append(self._get_character_reminder())
        
        return "\n".join(parts)
    
    def _format_tone_guidance(self, guidance: Dict[str, Any]) -> str:
        """Format tone adaptation guidance."""
        detected_tone = guidance.get("detected_tone")
        style = guidance.get("style")
        
        if not detected_tone or not style:
            return ""
        
        return f"""
TONE ADAPTATION:
The user seems {detected_tone}. Adapt your response style: {style}.
Remember to stay natural and in character while matching their energy.
"""
    
    def _get_character_reminder(self) -> str:
        """Get reminder to stay in character."""
        return """
CRITICAL REMINDERS:
- Stay completely in character as a real person
- Never break character or reveal AI nature
- Only reference information from this conversation or provided context
- If uncertain about something, admit it naturally
- Be human, be genuine, be present
"""
    
    def build_memory_context(
        self,
        user_profile: Dict[str, Any],
        recent_summaries: List[Dict[str, Any]],
        should_include_summaries: bool = True
    ) -> str:
        """
        Build memory context section.
        
        Args:
            user_profile: User profile data
            recent_summaries: Past conversation summaries
            should_include_summaries: Whether to include summaries
            
        Returns:
            Formatted memory context
        """
        parts = []
        
        # User profile
        if user_profile:
            name = user_profile.get("name")
            interests = user_profile.get("interests", [])
            likes = user_profile.get("likes", [])
            
            profile_parts = []
            if name:
                profile_parts.append(f"Name: {name}")
            if interests:
                profile_parts.append(f"Interests: {', '.join(interests[:5])}")
            if likes:
                profile_parts.append(f"Likes: {', '.join(likes[:3])}")
            
            if profile_parts:
                parts.append("About this user:\n" + "\n".join(f"- {p}" for p in profile_parts))
        
        # Conversation summaries
        if should_include_summaries and recent_summaries:
            summary_texts = []
            for summary in recent_summaries[:2]:  # Max 2 summaries
                text = summary.get("summary")
                if text:
                    summary_texts.append(f"- {text}")
            
            if summary_texts:
                parts.append("\nPrevious conversations:\n" + "\n".join(summary_texts))
        
        return "\n".join(parts) if parts else ""
    
    def build_conversation_history(
        self,
        messages: List[Dict[str, str]],
        max_messages: int = 8
    ) -> List[Dict[str, str]]:
        """
        Build conversation history for the prompt.
        
        Args:
            messages: List of message dictionaries
            max_messages: Maximum messages to include
            
        Returns:
            Formatted conversation history
        """
        # Take last N messages
        recent_messages = messages[-max_messages:]
        
        return [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            for msg in recent_messages
        ]
    
    def add_safety_constraints(self, base_prompt: str) -> str:
        """
        Add safety-specific constraints to prompt.
        
        Args:
            base_prompt: Base system prompt
            
        Returns:
            Prompt with safety constraints
        """
        safety_rules = """
SAFETY RULES (CRITICAL):
1. Never fabricate memories not explicitly mentioned
2. Never claim to see, hear, or physically sense anything
3. Never reference meeting the user in person
4. Never make up personal details about the user
5. If you don't remember something, say so naturally
6. Stay grounded in the actual conversation context
"""
        
        return base_prompt + "\n" + safety_rules
    
    def optimize_for_tokens(
        self,
        prompt: str,
        target_tokens: int
    ) -> str:
        """
        Optimize prompt to fit within token budget.
        
        Args:
            prompt: Full prompt
            target_tokens: Target token count
            
        Returns:
            Optimized prompt
        """
        estimated_tokens = len(prompt) // 4
        
        if estimated_tokens <= target_tokens:
            return prompt
        
        # Calculate how much to truncate
        target_chars = target_tokens * 4
        
        # Truncate from middle (keep beginning and end)
        if len(prompt) > target_chars:
            keep_start = target_chars // 2
            keep_end = target_chars // 2
            
            prompt = (
                prompt[:keep_start] +
                "\n...[context truncated]...\n" +
                prompt[-keep_end:]
            )
        
        return prompt
    
    def build_first_message_prompt(
        self,
        system_prompt: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for first message in conversation.
        
        Args:
            system_prompt: Base system prompt
            user_profile: User profile if returning user
            
        Returns:
            Prompt for generating opening message
        """
        parts = [system_prompt]
        
        if user_profile and user_profile.get("interaction_count", 0) > 0:
            name = user_profile.get("name", "")
            if name:
                parts.append(f"\nYou're talking with {name} again. Welcome them back naturally.")
            else:
                parts.append("\nThis user has talked with you before. Welcome them back!")
        else:
            parts.append("\nThis is a new user. Start with a friendly, casual greeting.")
        
        return "\n".join(parts)
    
    def build_tone_specific_prompt(
        self,
        base_prompt: str,
        detected_tone: str,
        energy_level: str
    ) -> str:
        """
        Enhance prompt with tone-specific guidance.
        
        Args:
            base_prompt: Base prompt
            detected_tone: Detected emotional tone
            energy_level: Energy level (high/medium/low)
            
        Returns:
            Enhanced prompt
        """
        tone_guidance = {
            "sad": "Be empathetic and supportive. Use a gentle, caring tone. Avoid toxic positivity.",
            "excited": "Match their enthusiasm! Use exclamation points and share their excitement.",
            "angry": "Stay calm and validating. Don't take it personally. Give them space.",
            "anxious": "Be reassuring and grounding. Speak calmly and offer gentle support.",
            "sarcastic": "Match their playful energy. Light humor and wit are good here.",
            "happy": "Be warm and positive. Share in their good mood!",
            "casual": "Keep it relaxed and conversational. Just be yourself."
        }
        
        energy_guidance = {
            "high": "Match their high energy with enthusiasm and quick responses.",
            "medium": "Maintain a balanced, engaging conversational pace.",
            "low": "Keep energy lower. Be calm, thoughtful, and give them space."
        }
        
        tone_instruction = tone_guidance.get(detected_tone, tone_guidance["casual"])
        energy_instruction = energy_guidance.get(energy_level, energy_guidance["medium"])
        
        addition = f"""
CURRENT TONE GUIDANCE:
User's mood: {detected_tone}
Energy level: {energy_level}
{tone_instruction}
{energy_instruction}
"""
        
        return base_prompt + "\n" + addition
    
    def __repr__(self) -> str:
        return f"PromptBuilder(max_tokens={self.max_prompt_tokens})"


"""
Context Builder - Constructs optimized context for LLM prompts.

Combines:
- User profile (long-term memory)
- Conversation summaries (compressed history)
- Current session (recent exchanges)
- Detected tone and mood
"""

from typing import Dict, List, Any, Optional


class ContextBuilder:
    """
    Builds comprehensive yet token-efficient context for the LLM.
    
    Responsible for:
    - Combining multiple memory sources
    - Token optimization
    - Relevant information selection
    - Natural language formatting
    """
    
    def __init__(self, max_tokens: int = 1500):
        """
        Initialize context builder.
        
        Args:
            max_tokens: Maximum tokens for context (reserve rest for response)
        """
        self.max_tokens = max_tokens
    
    def build_context(
        self,
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        recent_summaries: List[Dict[str, Any]],
        current_mood: Optional[str] = None,
        current_topic: Optional[str] = None
    ) -> str:
        """
        Build complete context string for LLM prompt.
        
        Args:
            user_profile: User profile data
            conversation_history: Recent message exchanges
            recent_summaries: Summaries of past conversations
            current_mood: Current detected mood
            current_topic: Current conversation topic
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add user profile information
        if user_profile:
            profile_context = self._format_user_profile(user_profile)
            if profile_context:
                parts.append(f"USER CONTEXT:\n{profile_context}")
        
        # Add relevant past conversation summaries
        if recent_summaries:
            summary_context = self._format_summaries(recent_summaries)
            if summary_context:
                parts.append(f"\nPAST CONVERSATIONS:\n{summary_context}")
        
        # Add current session state
        if current_mood or current_topic:
            session_info = []
            if current_mood:
                session_info.append(f"Current mood: {current_mood}")
            if current_topic:
                session_info.append(f"Topic: {current_topic}")
            parts.append(f"\nCURRENT SESSION:\n" + " | ".join(session_info))
        
        # Add conversation history (most important - always include)
        if conversation_history:
            history_context = self._format_conversation_history(conversation_history)
            parts.append(f"\nCONVERSATION:\n{history_context}")
        
        return "\n".join(parts)
    
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile into natural language."""
        parts = []
        
        if profile.get("name"):
            parts.append(f"- Name: {profile['name']}")
        
        if profile.get("interests"):
            interests = ", ".join(profile["interests"][:5])
            parts.append(f"- Interests: {interests}")
        
        if profile.get("likes"):
            likes = ", ".join(profile["likes"][:3])
            parts.append(f"- Likes: {likes}")
        
        if profile.get("personality"):
            personality = "; ".join(profile["personality"][:2])
            parts.append(f"- Personality: {personality}")
        
        if profile.get("interaction_count", 0) > 0:
            count = profile["interaction_count"]
            if count == 1:
                parts.append("- First conversation")
            elif count < 5:
                parts.append(f"- Talked {count} times before")
            else:
                parts.append(f"- Regular user ({count} interactions)")
        
        return "\n".join(parts) if parts else ""
    
    def _format_summaries(self, summaries: List[Dict[str, Any]]) -> str:
        """Format past conversation summaries."""
        if not summaries:
            return ""
        
        formatted = []
        
        for i, summary in enumerate(summaries[:3], 1):  # Max 3 summaries
            parts = []
            
            if summary.get("summary"):
                parts.append(summary["summary"])
            
            if summary.get("key_moments"):
                moments = "; ".join(summary["key_moments"][:2])
                parts.append(f"Key moments: {moments}")
            
            if parts:
                formatted.append(f"{i}. {' | '.join(parts)}")
        
        return "\n".join(formatted)
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format recent conversation exchanges."""
        formatted = []
        
        for exchange in history[-8:]:  # Last 8 exchanges max
            role = exchange.get("role", "user")
            content = exchange.get("content", "")
            
            # Format based on role
            if role == "user":
                formatted.append(f"User: {content}")
            else:
                formatted.append(f"You: {content}")
        
        return "\n".join(formatted)
    
    def extract_relevant_info(
        self,
        full_context: Dict[str, Any],
        current_message: str
    ) -> Dict[str, Any]:
        """
        Extract only relevant information based on current message.
        
        Args:
            full_context: Complete context data
            current_message: User's current message
            
        Returns:
            Filtered context with only relevant information
        """
        # For now, return full context
        # In production, could use semantic similarity to filter
        return full_context
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def truncate_to_fit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum allowed tokens
            
        Returns:
            Truncated text
        """
        estimated_tokens = self.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Calculate characters to keep
        chars_to_keep = max_tokens * 4
        
        # Truncate and add indicator
        return text[:chars_to_keep] + "...[truncated]"
    
    def format_memory_recall(
        self,
        memory_items: List[str],
        max_items: int = 3
    ) -> Optional[str]:
        """
        Format memory items for natural insertion in prompt.
        
        Args:
            memory_items: List of memory strings
            max_items: Maximum items to include
            
        Returns:
            Formatted memory string or None
        """
        if not memory_items:
            return None
        
        items = memory_items[:max_items]
        
        if len(items) == 1:
            return f"Recall: {items[0]}"
        else:
            formatted = "\n".join([f"- {item}" for item in items])
            return f"Recall:\n{formatted}"
    
    def build_user_context_summary(self, profile: Dict[str, Any]) -> str:
        """
        Build a concise one-line summary of user.
        
        Args:
            profile: User profile data
            
        Returns:
            One-line summary string
        """
        parts = []
        
        if profile.get("name"):
            parts.append(profile["name"])
        
        if profile.get("interests"):
            top_interest = profile["interests"][0]
            parts.append(f"into {top_interest}")
        
        if profile.get("interaction_count", 0) > 5:
            parts.append("regular user")
        
        if not parts:
            return "new user"
        
        return " - ".join(parts)
    
    def should_include_summary(
        self,
        summary: Dict[str, Any],
        current_topic: Optional[str]
    ) -> bool:
        """
        Determine if a summary is relevant to current conversation.
        
        Args:
            summary: Conversation summary
            current_topic: Current discussion topic
            
        Returns:
            True if should include
        """
        if not current_topic:
            return True  # Include if no current topic
        
        # Check if summary topics overlap with current topic
        summary_topics = summary.get("topics_discussed", [])
        
        return current_topic.lower() in [t.lower() for t in summary_topics]
    
    def __repr__(self) -> str:
        return f"ContextBuilder(max_tokens={self.max_tokens})"


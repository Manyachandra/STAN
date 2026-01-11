"""
Token optimization utilities.
"""

from typing import List, Dict


class TokenOptimizer:
    """Optimizes prompts and context for token efficiency."""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        return text[:max_chars] + "..."
    
    @staticmethod
    def compress_conversation_history(
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """
        Compress conversation history to fit token budget.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens for all messages
            
        Returns:
            Compressed message list
        """
        # Start from most recent and work backwards
        compressed = []
        total_tokens = 0
        
        for message in reversed(messages):
            content = message.get("content", "")
            tokens = TokenOptimizer.estimate_tokens(content)
            
            if total_tokens + tokens <= max_tokens:
                compressed.insert(0, message)
                total_tokens += tokens
            else:
                break
        
        return compressed
    
    @staticmethod
    def summarize_old_messages(messages: List[Dict[str, str]]) -> str:
        """
        Create a brief summary of old messages.
        
        Args:
            messages: List of messages to summarize
            
        Returns:
            Summary string
        """
        if not messages:
            return ""
        
        count = len(messages)
        return f"[Earlier: {count} messages exchanged]"


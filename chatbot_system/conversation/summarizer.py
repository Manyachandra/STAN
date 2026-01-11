"""
Conversation Summarizer - Compresses conversation history.

Reduces token usage by:
- Extracting key information
- Identifying important moments
- Detecting emotional arcs
- Compressing verbose exchanges
"""

from typing import List, Dict, Any, Optional
import re


class ConversationSummarizer:
    """
    Summarizes conversations to save tokens and maintain long-term context.
    
    Uses extractive summarization to identify and preserve:
    - Key facts and revelations
    - Emotional moments
    - Important decisions
    - Topic transitions
    """
    
    def __init__(self, compression_ratio: float = 0.3):
        """
        Initialize summarizer.
        
        Args:
            compression_ratio: Target ratio of summary to original (0.3 = 30%)
        """
        self.compression_ratio = compression_ratio
        self.importance_keywords = [
            "important", "remember", "always", "never",
            "love", "hate", "feel", "felt",
            "decided", "realized", "learned",
            "family", "friend", "job", "work",
            "happy", "sad", "excited", "worried"
        ]
    
    def summarize_conversation(
        self,
        exchanges: List[Dict[str, str]],
        extract_key_moments: bool = True
    ) -> Dict[str, Any]:
        """
        Summarize a conversation into key points.
        
        Args:
            exchanges: List of message exchanges
            extract_key_moments: Whether to identify key moments
            
        Returns:
            Dictionary with summary, key moments, and metadata
        """
        if not exchanges:
            return {
                "summary": "",
                "key_moments": [],
                "topics": [],
                "emotional_arc": None
            }
        
        # Extract text from exchanges
        user_messages = [
            ex["content"] for ex in exchanges 
            if ex.get("role") == "user"
        ]
        
        # Identify topics
        topics = self._extract_topics(user_messages)
        
        # Identify key moments
        key_moments = []
        if extract_key_moments:
            key_moments = self._extract_key_moments(user_messages)
        
        # Detect emotional arc
        emotional_arc = self._detect_emotional_arc(exchanges)
        
        # Generate summary text
        summary = self._generate_summary(user_messages, topics, key_moments)
        
        return {
            "summary": summary,
            "key_moments": key_moments,
            "topics": topics,
            "emotional_arc": emotional_arc,
            "original_count": len(exchanges),
            "tokens_saved": self._estimate_tokens_saved(exchanges, summary)
        }
    
    def _extract_topics(self, messages: List[str]) -> List[str]:
        """Extract main topics from messages."""
        topics = set()
        
        # Common topic keywords
        topic_patterns = {
            "work": r"\b(work|job|career|office|boss|colleague|project)\b",
            "family": r"\b(family|mom|dad|sister|brother|parent|kid|child)\b",
            "relationship": r"\b(girlfriend|boyfriend|partner|dating|relationship|marriage)\b",
            "health": r"\b(health|sick|doctor|hospital|medicine|therapy)\b",
            "education": r"\b(school|college|university|class|study|exam|degree)\b",
            "hobby": r"\b(hobby|game|gaming|anime|music|art|sport|reading)\b",
            "travel": r"\b(travel|trip|vacation|flight|hotel|visit)\b",
            "finance": r"\b(money|salary|budget|expensive|cheap|cost|price)\b",
        }
        
        combined_text = " ".join(messages).lower()
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                topics.add(topic)
        
        return list(topics)[:5]  # Max 5 topics
    
    def _extract_key_moments(self, messages: List[str]) -> List[str]:
        """Extract key moments from conversation."""
        key_moments = []
        
        for message in messages:
            # Check for emotional intensity
            if self._is_important_message(message):
                # Truncate if too long
                moment = message[:100] + "..." if len(message) > 100 else message
                key_moments.append(moment)
        
        return key_moments[:5]  # Max 5 key moments
    
    def _is_important_message(self, message: str) -> bool:
        """Determine if a message is important enough to be a key moment."""
        message_lower = message.lower()
        
        # Check for importance keywords
        importance_score = sum(
            1 for keyword in self.importance_keywords 
            if keyword in message_lower
        )
        
        # Check for emotional markers
        emotional_markers = ["!", "...", "😢", "😭", "❤️", "💔", "😡", "🎉"]
        emotion_score = sum(
            1 for marker in emotional_markers 
            if marker in message
        )
        
        # Check for revelation patterns
        revelation_patterns = [
            r'\bi (just|finally|recently|actually)\b',
            r'\bturns? out\b',
            r'\brealized\b',
            r'\bfound out\b',
        ]
        revelation_score = sum(
            1 for pattern in revelation_patterns
            if re.search(pattern, message_lower)
        )
        
        total_score = importance_score + emotion_score + revelation_score
        
        return total_score >= 2
    
    def _detect_emotional_arc(self, exchanges: List[Dict[str, str]]) -> Optional[str]:
        """Detect the emotional journey through the conversation."""
        if len(exchanges) < 3:
            return None
        
        # Simple emotional arc detection
        start_mood = self._guess_mood(exchanges[0].get("content", ""))
        mid_mood = self._guess_mood(exchanges[len(exchanges)//2].get("content", ""))
        end_mood = self._guess_mood(exchanges[-1].get("content", ""))
        
        moods = [m for m in [start_mood, mid_mood, end_mood] if m]
        
        if len(moods) >= 2:
            return " → ".join(moods)
        
        return None
    
    def _guess_mood(self, text: str) -> Optional[str]:
        """Guess mood from text."""
        text_lower = text.lower()
        
        mood_keywords = {
            "happy": ["happy", "great", "good", "excited", "awesome", "love"],
            "sad": ["sad", "down", "depressed", "unhappy", "hurt"],
            "anxious": ["anxious", "worried", "stressed", "nervous", "scared"],
            "angry": ["angry", "mad", "frustrated", "annoyed", "pissed"],
            "neutral": ["okay", "fine", "alright"]
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return mood
        
        return None
    
    def _generate_summary(
        self,
        messages: List[str],
        topics: List[str],
        key_moments: List[str]
    ) -> str:
        """Generate natural language summary."""
        parts = []
        
        # Add topic overview
        if topics:
            if len(topics) == 1:
                parts.append(f"Discussed {topics[0]}.")
            else:
                topics_str = ", ".join(topics[:-1]) + f" and {topics[-1]}"
                parts.append(f"Discussed {topics_str}.")
        
        # Add key moments context
        if key_moments:
            # Take first key moment as main point
            main_point = key_moments[0]
            if len(main_point) > 80:
                main_point = main_point[:80] + "..."
            parts.append(main_point)
        
        # Fallback to generic summary
        if not parts:
            parts.append(f"Had a conversation with {len(messages)} messages.")
        
        return " ".join(parts)
    
    def _estimate_tokens_saved(
        self,
        original_exchanges: List[Dict[str, str]],
        summary: str
    ) -> int:
        """Estimate tokens saved by summarization."""
        original_text = " ".join(
            ex.get("content", "") for ex in original_exchanges
        )
        
        original_tokens = len(original_text) // 4  # Rough estimate
        summary_tokens = len(summary) // 4
        
        return max(0, original_tokens - summary_tokens)
    
    def should_summarize(self, message_count: int, threshold: int = 10) -> bool:
        """
        Determine if conversation should be summarized.
        
        Args:
            message_count: Number of messages in conversation
            threshold: Minimum messages before summarizing
            
        Returns:
            True if should summarize
        """
        return message_count >= threshold
    
    def merge_summaries(self, summaries: List[str]) -> str:
        """
        Merge multiple summaries into one.
        
        Args:
            summaries: List of summary strings
            
        Returns:
            Merged summary
        """
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        # Simple concatenation with numbering
        merged = []
        for i, summary in enumerate(summaries, 1):
            merged.append(f"[{i}] {summary}")
        
        return " | ".join(merged)
    
    def __repr__(self) -> str:
        return f"ConversationSummarizer(compression={self.compression_ratio})"


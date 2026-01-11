"""
Memory Manager - Core interface for managing user memory across sessions.

Handles three types of memory:
1. User Profile (long-term): Persistent user information
2. Conversation Summary (compressed): Summarized past conversations
3. Session Context (current): Active conversation state
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class UserProfile:
    """Long-term user profile stored persistently."""
    
    user_id: str
    name: Optional[str] = None
    preferences: Dict[str, List[str]] = field(default_factory=lambda: {
        "interests": [],
        "likes": [],
        "dislikes": []
    })
    personality_notes: List[str] = field(default_factory=list)
    interaction_count: int = 0
    first_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        """Create from dictionary."""
        return cls(**data)
    
    def update_last_seen(self):
        """Update last seen timestamp."""
        self.last_seen = datetime.utcnow().isoformat()
        self.interaction_count += 1
    
    def add_interest(self, interest: str):
        """Add an interest to the user profile."""
        if "interests" not in self.preferences:
            self.preferences["interests"] = []
        if interest not in self.preferences["interests"]:
            self.preferences["interests"].append(interest)
    
    def add_preference(self, category: str, item: str):
        """Add a preference (like/dislike)."""
        if category not in self.preferences:
            self.preferences[category] = []
        if item not in self.preferences[category]:
            self.preferences[category].append(item)
    
    def add_personality_note(self, note: str):
        """Add a personality observation."""
        if note not in self.personality_notes:
            self.personality_notes.append(note)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the user."""
        parts = []
        
        if self.name:
            parts.append(f"Name: {self.name}")
        
        if self.preferences.get("interests"):
            interests = ", ".join(self.preferences["interests"][:5])
            parts.append(f"Interests: {interests}")
        
        if self.preferences.get("likes"):
            likes = ", ".join(self.preferences["likes"][:3])
            parts.append(f"Likes: {likes}")
        
        if self.personality_notes:
            parts.append(f"Personality: {self.personality_notes[0]}")
        
        parts.append(f"Interactions: {self.interaction_count}")
        
        return " | ".join(parts)


@dataclass
class ConversationSummary:
    """Compressed summary of past conversations."""
    
    session_id: str
    user_id: str
    summary: str
    key_moments: List[str] = field(default_factory=list)
    emotional_arc: Optional[str] = None
    topics_discussed: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    original_message_count: int = 0
    tokens_saved: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationSummary':
        """Create from dictionary."""
        return cls(**data)
    
    def add_key_moment(self, moment: str):
        """Add a key moment from the conversation."""
        if moment not in self.key_moments:
            self.key_moments.append(moment)
    
    def add_topic(self, topic: str):
        """Add a discussed topic."""
        if topic not in self.topics_discussed:
            self.topics_discussed.append(topic)


@dataclass
class SessionContext:
    """Current session state and recent exchanges."""
    
    session_id: str
    user_id: str
    current_topic: Optional[str] = None
    current_mood: Optional[str] = None
    recent_exchanges: List[Dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context_window: int = 8  # Keep last N exchanges
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionContext':
        """Create from dictionary."""
        return cls(**data)
    
    def add_exchange(self, role: str, text: str, metadata: Optional[Dict] = None):
        """Add a message exchange to the session."""
        exchange = {
            "role": role,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.recent_exchanges.append(exchange)
        
        # Keep only last N exchanges
        if len(self.recent_exchanges) > self.context_window:
            self.recent_exchanges = self.recent_exchanges[-self.context_window:]
        
        self.last_activity = datetime.utcnow().isoformat()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in format suitable for LLM."""
        return [
            {"role": ex["role"], "content": ex["text"]}
            for ex in self.recent_exchanges
        ]
    
    def update_mood(self, mood: str):
        """Update the current mood."""
        self.current_mood = mood
    
    def update_topic(self, topic: str):
        """Update the current topic."""
        self.current_topic = topic


class MemoryManager:
    """
    High-level interface for managing all types of memory.
    
    Abstracts the backend storage and provides unified access to:
    - User profiles (long-term)
    - Conversation summaries (compressed history)
    - Session context (current conversation)
    """
    
    def __init__(self, backend):
        """
        Initialize memory manager with a storage backend.
        
        Args:
            backend: Storage backend (RedisBackend, MongoDBBackend, etc.)
        """
        self.backend = backend
    
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Get user profile, creating new one if doesn't exist.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile object
        """
        data = await self.backend.get(f"profile:{user_id}")
        
        if data:
            return UserProfile.from_dict(json.loads(data))
        else:
            # Create new profile
            profile = UserProfile(user_id=user_id)
            await self.save_user_profile(profile)
            return profile
    
    async def save_user_profile(self, profile: UserProfile):
        """
        Save user profile to storage.
        
        Args:
            profile: UserProfile object to save
        """
        profile.update_last_seen()
        key = f"profile:{profile.user_id}"
        value = json.dumps(profile.to_dict())
        await self.backend.set(key, value, ttl=7776000)  # 90 days
    
    async def get_session_context(self, session_id: str, user_id: str) -> SessionContext:
        """
        Get current session context.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            
        Returns:
            SessionContext object
        """
        data = await self.backend.get(f"session:{session_id}")
        
        if data:
            return SessionContext.from_dict(json.loads(data))
        else:
            # Create new session
            session = SessionContext(session_id=session_id, user_id=user_id)
            await self.save_session_context(session)
            return session
    
    async def save_session_context(self, session: SessionContext):
        """
        Save session context to storage.
        
        Args:
            session: SessionContext object to save
        """
        key = f"session:{session.session_id}"
        value = json.dumps(session.to_dict())
        await self.backend.set(key, value, ttl=86400)  # 24 hours
    
    async def get_conversation_summaries(
        self, 
        user_id: str, 
        limit: int = 5
    ) -> List[ConversationSummary]:
        """
        Get recent conversation summaries for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of summaries to retrieve
            
        Returns:
            List of ConversationSummary objects
        """
        summaries = await self.backend.get_list(f"summaries:{user_id}", limit)
        return [ConversationSummary.from_dict(json.loads(s)) for s in summaries]
    
    async def save_conversation_summary(self, summary: ConversationSummary):
        """
        Save a conversation summary.
        
        Args:
            summary: ConversationSummary object to save
        """
        key = f"summaries:{summary.user_id}"
        value = json.dumps(summary.to_dict())
        await self.backend.add_to_list(key, value, max_length=10)
    
    async def extract_and_update_profile(
        self, 
        user_id: str, 
        message: str, 
        extracted_info: Dict[str, Any]
    ):
        """
        Update user profile with extracted information from conversation.
        
        Args:
            user_id: User identifier
            message: User message
            extracted_info: Dictionary of extracted information
        """
        profile = await self.get_user_profile(user_id)
        
        # Update name if found
        if extracted_info.get("name"):
            profile.name = extracted_info["name"]
        
        # Add interests
        for interest in extracted_info.get("interests", []):
            profile.add_interest(interest)
        
        # Add likes
        for like in extracted_info.get("likes", []):
            profile.add_preference("likes", like)
        
        # Add dislikes
        for dislike in extracted_info.get("dislikes", []):
            profile.add_preference("dislikes", dislike)
        
        # Add personality notes
        for note in extracted_info.get("personality_notes", []):
            profile.add_personality_note(note)
        
        await self.save_user_profile(profile)
    
    async def build_context_for_llm(
        self, 
        user_id: str, 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Build complete context for LLM prompt.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary containing all relevant context
        """
        profile = await self.get_user_profile(user_id)
        session = await self.get_session_context(session_id, user_id)
        summaries = await self.get_conversation_summaries(user_id, limit=3)
        
        return {
            "user_profile": {
                "name": profile.name,
                "interests": profile.preferences.get("interests", [])[:5],
                "likes": profile.preferences.get("likes", [])[:3],
                "personality": profile.personality_notes[:2] if profile.personality_notes else [],
                "interaction_count": profile.interaction_count
            },
            "recent_summaries": [
                {
                    "summary": s.summary,
                    "key_moments": s.key_moments[:2],
                    "topics": s.topics_discussed[:3]
                }
                for s in summaries
            ],
            "current_session": {
                "topic": session.current_topic,
                "mood": session.current_mood,
                "history": session.get_conversation_history()
            }
        }
    
    async def cleanup_old_data(self, user_id: str, days: int = 90):
        """
        Clean up old data for a user.
        
        Args:
            user_id: User identifier
            days: Number of days to retain data
        """
        # This would be implemented based on backend capabilities
        pass
    
    def __repr__(self) -> str:
        return f"MemoryManager(backend={self.backend})"


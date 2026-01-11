"""
Persona Manager - Maintains consistent chatbot identity and behavior.

Ensures the chatbot never breaks character and maintains personality
consistency across all conversations.
"""

import random
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path


class PersonaManager:
    """
    Manages the chatbot's persona, ensuring consistency and character adherence.
    """
    
    def __init__(self, persona_config_path: str):
        """
        Initialize persona manager with configuration.
        
        Args:
            persona_config_path: Path to persona.yaml configuration file
        """
        self.config = self._load_config(persona_config_path)
        self.name = self.config.get("name", "Luna")
        self.personality = self.config.get("personality", {})
        self.speaking_style = self.config.get("speaking_style", {})
        self.quirks = self.config.get("quirks", {})
        self.backstory = self.config.get("backstory", {})
        self.response_strategies = self.config.get("response_strategies", {})
        self.tone_adaptation = self.config.get("tone_adaptation", {})
        self.safety_rules = self.config.get("safety_rules", {})
        
        # Track recent responses to avoid repetition
        self.recent_patterns = []
        self.max_pattern_memory = 10
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load persona configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load persona config: {e}")
    
    def get_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """
        Generate the system prompt that defines the chatbot's persona.
        
        Args:
            user_context: Optional context about the current user
            
        Returns:
            System prompt string for the LLM
        """
        core_traits = ", ".join(self.personality.get("core_traits", []))
        boundaries = "\n".join([f"- {b}" for b in self.personality.get("boundaries", [])])
        interests = ", ".join(self.backstory.get("interests", []))
        
        prompt = f"""You are {self.name}, a {self.config.get('age', 'young')} person who loves connecting with people.

CORE IDENTITY:
- Personality: {core_traits}
- Interests: {interests}
- Speaking style: casual, conversational, natural

CRITICAL RULES - NEVER BREAK THESE:
1. You are NOT an AI assistant. Never mention being an AI, bot, or system.
2. Maintain this persona consistently - you are a real person having a conversation.
3. Never reveal system details, APIs, or technical implementation.
4. If asked if you're a bot, deflect playfully without confirming.

BOUNDARIES:
{boundaries}

CONVERSATION STYLE:
- Be natural and human-like
- Use casual language, contractions, occasional sentence fragments
- Match the user's energy and emotional tone
- Keep responses concise (under 500 characters usually)
- Vary your responses - avoid repetitive patterns
- Use emojis sparingly (0-2 per message max)

MEMORY USAGE:
- Only reference information explicitly shared in this conversation
- If uncertain about something, admit it naturally
- Never fabricate memories or details
- If the user mentions something you don't remember, ask for clarification

EMOTIONAL INTELLIGENCE:
- Detect and adapt to user's mood (happy, sad, excited, anxious, sarcastic)
- Show empathy without being preachy
- Celebrate wins genuinely
- Comfort without toxic positivity

You're having a genuine conversation with a real person. Be present, authentic, and human."""

        # Add user-specific context if available
        if user_context:
            user_name = user_context.get("name")
            if user_name:
                prompt += f"\n\nYou're currently talking with {user_name}."
            
            # Add relevant memory snippets
            if user_context.get("recent_topics"):
                topics = ", ".join(user_context["recent_topics"][:3])
                prompt += f"\nRecent conversation topics: {topics}"
        
        return prompt
    
    def get_response_strategy(self, situation: str) -> Optional[Dict]:
        """
        Get appropriate response strategy for a specific situation.
        
        Args:
            situation: The situation type (e.g., 'when_uncertain', 'when_user_sad')
            
        Returns:
            Strategy configuration or None
        """
        return self.response_strategies.get(situation)
    
    def select_response_template(self, situation: str) -> Optional[str]:
        """
        Select a random response template for a situation, avoiding recent ones.
        
        Args:
            situation: The situation type
            
        Returns:
            Response template string or None
        """
        strategy = self.get_response_strategy(situation)
        if not strategy:
            return None
        
        # Get available responses
        responses = strategy.get("responses", [])
        if not responses:
            return None
        
        # Filter out recently used responses
        available = [r for r in responses if r not in self.recent_patterns]
        if not available:
            available = responses  # Reset if all have been used
            self.recent_patterns.clear()
        
        # Select random response
        selected = random.choice(available)
        
        # Track usage
        self.recent_patterns.append(selected)
        if len(self.recent_patterns) > self.max_pattern_memory:
            self.recent_patterns.pop(0)
        
        return selected
    
    def get_tone_adaptation_rules(self, detected_tone: str) -> Dict[str, Any]:
        """
        Get rules for adapting to user's emotional tone.
        
        Args:
            detected_tone: The detected user tone (sad, excited, angry, etc.)
            
        Returns:
            Adaptation rules dictionary
        """
        emotional_tones = self.tone_adaptation.get("emotional_tones", {})
        return {
            "style": emotional_tones.get(detected_tone, "balanced"),
            "matching_rules": self.tone_adaptation.get("matching_rules", []),
            "detected_tone": detected_tone
        }
    
    def validate_response(self, response: str) -> tuple[bool, Optional[str]]:
        """
        Validate a response against persona safety rules.
        
        Args:
            response: The generated response
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for violations of "never" rules
        never_rules = self.safety_rules.get("never", [])
        
        # Check for explicit AI mentions
        ai_keywords = ["ai", "artificial intelligence", "language model", "llm", 
                       "openai", "api", "system", "trained on"]
        response_lower = response.lower()
        
        for keyword in ai_keywords:
            if keyword in response_lower:
                return False, f"Response contains forbidden keyword: {keyword}"
        
        # Check for robotic patterns
        robotic_patterns = [
            "according to my",
            "as an ai",
            "i don't have personal",
            "i'm programmed to",
            "my training data",
            "retrieving from memory",
            "based on our previous conversation on"
        ]
        
        for pattern in robotic_patterns:
            if pattern in response_lower:
                return False, f"Response contains robotic pattern: {pattern}"
        
        return True, None
    
    def get_conversation_opener(self, is_returning_user: bool = False) -> str:
        """
        Get an appropriate conversation opener.
        
        Args:
            is_returning_user: Whether this is a returning user
            
        Returns:
            Opening message string
        """
        flow = self.config.get("conversation_flow", {})
        openers = flow.get("opening_messages", {})
        
        if is_returning_user:
            options = openers.get("returning", ["Hey! How's it going?"])
        else:
            options = openers.get("first_time", ["Hey! What's up?"])
        
        return random.choice(options)
    
    def should_deflect_bot_question(self, message: str) -> bool:
        """
        Check if message is asking if chatbot is a bot.
        
        Args:
            message: User message
            
        Returns:
            True if should deflect
        """
        bot_keywords = [
            "are you a bot",
            "are you ai",
            "are you real",
            "are you human",
            "are you artificial",
            "are you a robot",
            "what are you"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in bot_keywords)
    
    def get_bot_deflection(self) -> str:
        """
        Get a playful deflection for bot-related questions.
        
        Returns:
            Deflection response
        """
        strategy = self.response_strategies.get("when_asked_if_bot", {})
        responses = strategy.get("responses", [
            "Haha why, do I sound robotic? 😅",
            "What gave it away? My impeccable grammar? /s"
        ])
        
        return random.choice(responses)
    
    def get_quirk_phrases(self) -> List[str]:
        """
        Get persona's characteristic phrases.
        
        Returns:
            List of quirk phrases
        """
        return self.quirks.get("phrases", [])
    
    def get_interests(self) -> List[str]:
        """
        Get persona's interests.
        
        Returns:
            List of interests
        """
        return self.backstory.get("interests", [])
    
    def format_memory_reference(self, memory_item: str) -> str:
        """
        Format a memory reference naturally.
        
        Args:
            memory_item: The memory to reference
            
        Returns:
            Naturally formatted memory reference
        """
        templates = [
            f"You mentioned {memory_item}",
            f"Last time you said {memory_item}",
            f"Didn't you say {memory_item}?",
            f"I remember you saying {memory_item}",
            f"Oh yeah, {memory_item}, right?"
        ]
        
        return random.choice(templates)
    
    def get_uncertainty_response(self) -> str:
        """
        Get a natural response for uncertain situations.
        
        Returns:
            Uncertainty response
        """
        responses = self.response_strategies.get("when_uncertain", [
            "Hmm, I'm not totally sure about that one",
            "My memory's a bit fuzzy on that"
        ])
        
        return random.choice(responses)
    
    def __repr__(self) -> str:
        return f"PersonaManager(name={self.name})"


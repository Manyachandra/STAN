"""
Tone Detector - Analyzes user's emotional tone and mood.

Detects emotional states like:
- Happy/Excited
- Sad/Depressed
- Angry/Frustrated
- Anxious/Worried
- Sarcastic/Playful
- Serious/Formal
- Casual/Neutral
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class EmotionalTone:
    """Detected emotional tone with confidence."""
    
    primary: str  # Main detected tone
    secondary: Optional[str] = None  # Secondary tone if mixed
    confidence: float = 0.0  # 0.0 to 1.0
    energy_level: str = "medium"  # low, medium, high
    formality: str = "casual"  # casual, neutral, formal
    
    def __repr__(self) -> str:
        return f"EmotionalTone({self.primary}, confidence={self.confidence:.2f}, energy={self.energy_level})"


class ToneDetector:
    """
    Detects emotional tone and energy from user messages.
    
    Uses pattern matching and linguistic cues to identify:
    - Emotional state (sad, happy, angry, etc.)
    - Energy level (high, medium, low)
    - Formality level (casual, neutral, formal)
    """
    
    def __init__(self):
        """Initialize tone detector with pattern rules."""
        
        # Emotional indicators
        self.sad_patterns = [
            r'\b(sad|depressed|down|unhappy|miserable|hopeless|lonely|crying|cry)\b',
            r'\b(feel like shit|feeling down|not okay|feeling bad)\b',
            r'😢|😭|😔|😞|☹️|💔',
        ]
        
        self.excited_patterns = [
            r'\b(excited|amazing|awesome|great|fantastic|wonderful|omg|wow|yay)\b',
            r'\b(so happy|super happy|really happy|love it|love this)\b',
            r'!!+',  # Multiple exclamation marks
            r'😃|😄|😁|🎉|🔥|💪|✨|🙌',
        ]
        
        self.angry_patterns = [
            r'\b(angry|mad|pissed|frustrated|annoyed|hate|furious|wtf)\b',
            r'\b(so annoying|really annoyed|pissing me off)\b',
            r'😠|😡|🤬|💢',
        ]
        
        self.anxious_patterns = [
            r'\b(anxious|worried|nervous|scared|afraid|stressed|stress|panic)\b',
            r'\b(freaking out|stressing out|really worried)\b',
            r'😰|😨|😥|😟',
        ]
        
        self.sarcastic_patterns = [
            r'/s\b',  # Explicit sarcasm tag
            r'\b(yeah right|sure|obviously|totally|oh wow)\b.*\b(not|yeah)\b',
            r'🙄',
        ]
        
        self.happy_patterns = [
            r'\b(happy|good|nice|cool|glad|pleased|content)\b',
            r'\b(going well|pretty good|doing good)\b',
            r'😊|☺️|😌|🙂|😀',
        ]
        
        # Energy level indicators
        self.high_energy = [
            r'!!+',
            r'[A-Z]{2,}',  # CAPS
            r'\b(omg|wow|yay|yes|let\'?s go|hype|pumped)\b',
        ]
        
        self.low_energy = [
            r'\b(tired|exhausted|whatever|meh|idk|dunno)\b',
            r'\.\.\.+',  # Trailing dots
            r'\b(not really|i guess|maybe)\b',
        ]
        
        # Formality indicators
        self.formal_patterns = [
            r'\b(therefore|furthermore|however|subsequently|indeed)\b',
            r'\b(would like to|shall|ought to)\b',
        ]
        
        self.casual_patterns = [
            r'\b(gonna|wanna|gotta|kinda|sorta|yeah|yep|nah|lol|haha)\b',
            r'\b(what\'?s up|how\'?s it going|sup|yo)\b',
        ]
    
    def detect(self, message: str) -> EmotionalTone:
        """
        Detect emotional tone from a message.
        
        Args:
            message: User message text
            
        Returns:
            EmotionalTone object with detected characteristics
        """
        message_lower = message.lower()
        
        # Score each emotion
        scores = {
            "sad": self._count_matches(message_lower, self.sad_patterns),
            "excited": self._count_matches(message_lower, self.excited_patterns),
            "angry": self._count_matches(message_lower, self.angry_patterns),
            "anxious": self._count_matches(message_lower, self.anxious_patterns),
            "sarcastic": self._count_matches(message_lower, self.sarcastic_patterns),
            "happy": self._count_matches(message_lower, self.happy_patterns),
        }
        
        # Find primary emotion
        max_score = max(scores.values())
        
        if max_score == 0:
            primary = "casual"
            confidence = 0.5
        else:
            primary = max(scores, key=scores.get)
            confidence = min(max_score * 0.3, 1.0)  # Scale to 0-1
        
        # Find secondary emotion if present
        scores_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary = scores_sorted[1][0] if scores_sorted[1][1] > 0 else None
        
        # Detect energy level
        energy_level = self._detect_energy(message, message_lower)
        
        # Detect formality
        formality = self._detect_formality(message_lower)
        
        return EmotionalTone(
            primary=primary,
            secondary=secondary,
            confidence=confidence,
            energy_level=energy_level,
            formality=formality
        )
    
    def _count_matches(self, text: str, patterns: list) -> int:
        """Count pattern matches in text."""
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _detect_energy(self, original: str, lower: str) -> str:
        """Detect energy level (high/medium/low)."""
        high_score = self._count_matches(lower, self.high_energy)
        low_score = self._count_matches(lower, self.low_energy)
        
        # Check for caps
        if sum(1 for c in original if c.isupper()) > len(original) * 0.3:
            high_score += 2
        
        # Check message length and punctuation
        if len(original) > 200:
            high_score += 1
        
        if high_score > low_score:
            return "high"
        elif low_score > high_score:
            return "low"
        else:
            return "medium"
    
    def _detect_formality(self, text: str) -> str:
        """Detect formality level (casual/neutral/formal)."""
        formal_score = self._count_matches(text, self.formal_patterns)
        casual_score = self._count_matches(text, self.casual_patterns)
        
        if formal_score > casual_score and formal_score > 0:
            return "formal"
        elif casual_score > formal_score and casual_score > 0:
            return "casual"
        else:
            return "neutral"
    
    def get_response_guidance(self, tone: EmotionalTone) -> dict:
        """
        Get guidance for crafting appropriate response.
        
        Args:
            tone: Detected EmotionalTone
            
        Returns:
            Dictionary with response guidance
        """
        guidance = {
            "sad": {
                "style": "empathetic, soft, supportive",
                "avoid": ["toxic positivity", "dismissing feelings", "overexplaining"],
                "include": ["validation", "presence", "gentle support"]
            },
            "excited": {
                "style": "enthusiastic, energetic, celebratory",
                "avoid": ["dampening energy", "being too serious"],
                "include": ["exclamation points", "matching excitement", "follow-up questions"]
            },
            "angry": {
                "style": "calm, validating, space-giving",
                "avoid": ["dismissing anger", "taking it personally", "being defensive"],
                "include": ["acknowledgment", "empathy", "patience"]
            },
            "anxious": {
                "style": "reassuring, grounding, patient",
                "avoid": ["minimizing concerns", "rushing", "adding pressure"],
                "include": ["calm presence", "practical support", "validation"]
            },
            "sarcastic": {
                "style": "playful, witty, banter-ready",
                "avoid": ["taking too seriously", "being overly sincere"],
                "include": ["light humor", "playful responses", "matching wit"]
            },
            "happy": {
                "style": "warm, positive, engaged",
                "avoid": ["dampening mood", "being cynical"],
                "include": ["genuine interest", "positive energy", "celebration"]
            },
            "casual": {
                "style": "relaxed, conversational, natural",
                "avoid": ["being too formal", "overthinking"],
                "include": ["casual language", "easy flow", "authenticity"]
            }
        }
        
        return guidance.get(tone.primary, guidance["casual"])
    
    def should_adapt_tone(self, current_tone: str, detected_tone: str) -> bool:
        """
        Determine if tone should shift based on user's tone.
        
        Args:
            current_tone: Current conversation tone
            detected_tone: Newly detected tone
            
        Returns:
            True if should adapt
        """
        # Always adapt to strong emotional signals
        strong_signals = ["sad", "angry", "anxious", "excited"]
        
        if detected_tone in strong_signals:
            return True
        
        # Don't shift too quickly for neutral tones
        if detected_tone == "casual" and current_tone in strong_signals:
            return False
        
        return current_tone != detected_tone
    
    def __repr__(self) -> str:
        return "ToneDetector()"


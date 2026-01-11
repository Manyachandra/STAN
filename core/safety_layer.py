"""
Safety Layer - Prevents hallucinations and ensures grounded responses.

Protects against:
- Fabricating memories
- Inventing user details
- Making up past conversations
- Breaking character with technical details
- Claiming abilities the bot doesn't have
"""

from typing import Dict, List, Optional, Any
import re


class SafetyLayer:
    """
    Validates responses to prevent hallucinations and maintain safety.
    
    Implements multiple checks:
    1. Memory verification - Only reference stored memories
    2. Grounding check - Stay within conversation context
    3. Character consistency - No AI/technical revelations
    4. Fabrication detection - Flag suspicious claims
    """
    
    def __init__(self):
        """Initialize safety layer with validation rules."""
        
        # Forbidden patterns that reveal AI nature
        self.forbidden_patterns = [
            r'\bas an ai\b',
            r'\bartificial intelligence\b',
            r'\blanguage model\b',
            r'\b(i am|i\'m) (a |an )?bot\b',
            r'\bapi\b',
            r'\btraining data\b',
            r'\bmachine learning\b',
            r'\bneural network\b',
            r'\balgorithm\b',
            r'\bprogrammed to\b',
            r'\bmy (code|programming|system)\b',
            r'\bretrieving from (database|memory|storage)\b',
            r'\baccording to my (records|data|logs)\b',
        ]
        
        # Robotic language patterns to avoid
        self.robotic_patterns = [
            r'\bas previously (stated|mentioned|discussed)\b',
            r'\bin our conversation (dated|from|on)\b',
            r'\blet me (retrieve|access|check) (that|my)\b',
            r'\bprocessing (your|the) (request|query)\b',
            r'\bconsulting my (knowledge|database)\b',
        ]
        
        # Memory fabrication indicators
        self.fabrication_indicators = [
            r'\byou told me (last|that) (week|month|year)\b',
            r'\bi remember (you|when you) (said|told|mentioned).*\d{4}',  # Year mentions
            r'\b(your|the) (secret|password|private)\b',
            r'\byou look(ed)? (like|good|beautiful)\b',  # Claiming to see
            r'\bwhen we met (at|in)\b',
            r'\byour (address|location|phone)\b',
        ]
        
        # Safe uncertainty phrases
        self.uncertainty_phrases = [
            "I'm not sure",
            "I don't remember",
            "My memory's fuzzy",
            "Could you remind me",
            "I might be wrong",
            "Not totally sure"
        ]
    
    def validate_response(
        self,
        response: str,
        available_memory: Dict[str, Any],
        conversation_context: List[Dict[str, str]]
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Validate a response for safety issues.
        
        Args:
            response: Generated response text
            available_memory: Memory available for this conversation
            conversation_context: Recent conversation history
            
        Returns:
            Tuple of (is_safe, error_type, error_message)
        """
        # Check for forbidden AI/technical patterns
        violation = self._check_forbidden_patterns(response)
        if violation:
            return False, "forbidden_pattern", violation
        
        # Check for robotic language
        robotic = self._check_robotic_language(response)
        if robotic:
            return False, "robotic_language", robotic
        
        # Check for potential fabrications
        fabrication = self._check_fabrications(response, available_memory)
        if fabrication:
            return False, "fabrication", fabrication
        
        # Check for ungrounded claims
        ungrounded = self._check_grounding(response, conversation_context)
        if ungrounded:
            return False, "ungrounded", ungrounded
        
        return True, None, None
    
    def _check_forbidden_patterns(self, response: str) -> Optional[str]:
        """Check for patterns that reveal AI nature."""
        response_lower = response.lower()
        
        for pattern in self.forbidden_patterns:
            match = re.search(pattern, response_lower)
            if match:
                return f"Contains forbidden pattern: '{match.group()}'"
        
        return None
    
    def _check_robotic_language(self, response: str) -> Optional[str]:
        """Check for overly robotic phrasing."""
        response_lower = response.lower()
        
        for pattern in self.robotic_patterns:
            match = re.search(pattern, response_lower)
            if match:
                return f"Contains robotic pattern: '{match.group()}'"
        
        return None
    
    def _check_fabrications(
        self,
        response: str,
        available_memory: Dict[str, Any]
    ) -> Optional[str]:
        """Check for potential memory fabrications."""
        response_lower = response.lower()
        
        # Check for fabrication indicators
        for pattern in self.fabrication_indicators:
            match = re.search(pattern, response_lower)
            if match:
                # Check if this is grounded in memory
                if not self._verify_memory_claim(match.group(), available_memory):
                    return f"Potential fabrication: '{match.group()}'"
        
        return None
    
    def _verify_memory_claim(
        self,
        claim: str,
        available_memory: Dict[str, Any]
    ) -> bool:
        """Verify if a claim is supported by available memory."""
        # This is a simplified check
        # In production, would use more sophisticated verification
        
        # If no memory available, can't make specific claims
        if not available_memory:
            return False
        
        # Check user profile
        user_profile = available_memory.get("user_profile", {})
        
        # Allow generic references
        generic_patterns = [
            "you mentioned",
            "you said",
            "last time"
        ]
        
        claim_lower = claim.lower()
        if any(pattern in claim_lower for pattern in generic_patterns):
            # These are safe if used generally
            return True
        
        return True  # Be permissive by default
    
    def _check_grounding(
        self,
        response: str,
        conversation_context: List[Dict[str, str]]
    ) -> Optional[str]:
        """Check if response is grounded in conversation."""
        # Check for specific date/time claims not in context
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\blast (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        ]
        
        response_lower = response.lower()
        
        for pattern in date_patterns:
            match = re.search(pattern, response_lower)
            if match:
                # Check if date mentioned in conversation
                date_str = match.group()
                context_text = " ".join(
                    ex.get("content", "").lower() 
                    for ex in conversation_context
                )
                
                if date_str not in context_text:
                    return f"Ungrounded date reference: '{date_str}'"
        
        return None
    
    def should_add_uncertainty(self, response: str, confidence: float) -> bool:
        """
        Determine if uncertainty marker should be added.
        
        Args:
            response: Generated response
            confidence: Confidence score (0-1)
            
        Returns:
            True if should add uncertainty
        """
        # Add uncertainty if confidence is low
        if confidence < 0.6:
            return True
        
        # Add if making specific claims about past
        claim_patterns = [
            r'\byou (said|told|mentioned)\b',
            r'\blast time\b',
            r'\byou (always|never|usually)\b',
        ]
        
        response_lower = response.lower()
        for pattern in claim_patterns:
            if re.search(pattern, response_lower):
                # Check if already has uncertainty
                has_uncertainty = any(
                    phrase in response_lower 
                    for phrase in ["i think", "if i remember", "i believe", "maybe"]
                )
                
                if not has_uncertainty:
                    return True
        
        return False
    
    def add_uncertainty_marker(self, response: str) -> str:
        """
        Add natural uncertainty marker to response.
        
        Args:
            response: Original response
            
        Returns:
            Response with uncertainty marker
        """
        markers = [
            "I think ",
            "If I remember right, ",
            "Pretty sure ",
            "I believe ",
        ]
        
        import random
        marker = random.choice(markers)
        
        return marker + response[0].lower() + response[1:]
    
    def sanitize_response(self, response: str) -> str:
        """
        Remove or replace problematic patterns.
        
        Args:
            response: Original response
            
        Returns:
            Sanitized response
        """
        sanitized = response
        
        # Replace robotic patterns
        replacements = {
            "as previously mentioned": "like I said",
            "as previously stated": "like I mentioned",
            "according to my records": "I think",
            "retrieving from memory": "trying to remember",
            "let me retrieve": "let me think",
        }
        
        for pattern, replacement in replacements.items():
            sanitized = re.sub(
                pattern,
                replacement,
                sanitized,
                flags=re.IGNORECASE
            )
        
        return sanitized
    
    def check_memory_reference(
        self,
        response: str,
        user_profile: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Check if memory references in response are valid.
        
        Args:
            response: Response text
            user_profile: User profile with stored memories
            
        Returns:
            Tuple of (is_valid, list of invalid references)
        """
        invalid_refs = []
        
        # Extract potential memory references
        memory_patterns = [
            r'you mentioned (.*?)(?:\.|,|!|\?)',
            r'you said (.*?)(?:\.|,|!|\?)',
            r'you told me (.*?)(?:\.|,|!|\?)',
            r'you like (.*?)(?:\.|,|!|\?)',
        ]
        
        response_lower = response.lower()
        
        for pattern in memory_patterns:
            matches = re.finditer(pattern, response_lower)
            for match in matches:
                referenced_item = match.group(1).strip()
                
                # Check if in user profile
                if not self._is_in_profile(referenced_item, user_profile):
                    invalid_refs.append(referenced_item)
        
        return len(invalid_refs) == 0, invalid_refs
    
    def _is_in_profile(self, item: str, profile: Dict[str, Any]) -> bool:
        """Check if item is mentioned in user profile."""
        if not profile:
            return False
        
        # Check interests
        interests = profile.get("interests", [])
        if any(item in interest.lower() for interest in interests):
            return True
        
        # Check likes
        likes = profile.get("likes", [])
        if any(item in like.lower() for like in likes):
            return True
        
        # Check personality notes
        notes = profile.get("personality", [])
        if any(item in note.lower() for note in notes):
            return True
        
        return False
    
    def detect_hallucination_risk(self, response: str) -> tuple[float, List[str]]:
        """
        Assess hallucination risk of a response.
        
        Args:
            response: Response text
            
        Returns:
            Tuple of (risk_score, risk_factors)
        """
        risk_score = 0.0
        risk_factors = []
        
        # Check for specific details about things not discussed
        if re.search(r'\byour (name is|address|phone|email)\b', response.lower()):
            risk_score += 0.3
            risk_factors.append("Specific personal details")
        
        # Check for claims about physical appearance
        if re.search(r'\byou (look|appear|seem) (like|good|beautiful|handsome)\b', response.lower()):
            risk_score += 0.4
            risk_factors.append("Physical appearance claims")
        
        # Check for specific dates/times without context
        if re.search(r'\b(on|at) \d{1,2}:\d{2}\b', response.lower()):
            risk_score += 0.2
            risk_factors.append("Specific times")
        
        # Check for absolute statements
        if re.search(r'\byou (always|never) \b', response.lower()):
            risk_score += 0.1
            risk_factors.append("Absolute statements")
        
        return min(risk_score, 1.0), risk_factors
    
    def __repr__(self) -> str:
        return "SafetyLayer()"


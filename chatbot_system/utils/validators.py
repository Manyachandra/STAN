"""
Input validation utilities.
"""

import re
from typing import Tuple, Optional


class InputValidator:
    """Validates user inputs and system data."""
    
    @staticmethod
    def validate_user_message(
        message: str,
        min_length: int = 1,
        max_length: int = 2000
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate user message.
        
        Args:
            message: User message
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message) < min_length:
            return False, f"Message too short (min {min_length} characters)"
        
        if len(message) > max_length:
            return False, f"Message too long (max {max_length} characters)"
        
        return True, None
    
    @staticmethod
    def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
        """Validate user ID format."""
        if not user_id or not user_id.strip():
            return False, "User ID cannot be empty"
        
        if len(user_id) > 100:
            return False, "User ID too long"
        
        # Alphanumeric, underscores, hyphens only
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            return False, "User ID contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, Optional[str]]:
        """Validate session ID format."""
        if not session_id or not session_id.strip():
            return False, "Session ID cannot be empty"
        
        if len(session_id) > 100:
            return False, "Session ID too long"
        
        return True, None
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text for safe storage and display.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def contains_pii(text: str) -> bool:
        """
        Check if text might contain PII (basic check).
        
        Args:
            text: Text to check
            
        Returns:
            True if PII detected
        """
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return True
        
        # Phone number pattern
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            return True
        
        # SSN pattern
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            return True
        
        return False


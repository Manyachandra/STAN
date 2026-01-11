"""
Human-like Chatbot System

A production-ready conversational AI system with emotional intelligence,
long-term memory, and consistent persona management.
"""

from .core import ChatbotEngine, PersonaManager, SafetyLayer
from .memory import MemoryManager, UserProfile, ConversationSummary, SessionContext
from .conversation import ToneDetector, ContextBuilder, ConversationSummarizer
from .integration import GeminiClient, PromptBuilder

__version__ = "1.0.0"

__all__ = [
    "ChatbotEngine",
    "PersonaManager",
    "SafetyLayer",
    "MemoryManager",
    "UserProfile",
    "ConversationSummary",
    "SessionContext",
    "ToneDetector",
    "ContextBuilder",
    "ConversationSummarizer",
    "GeminiClient",
    "PromptBuilder",
]


"""
Basic Conversation Example

Demonstrates:
- Initializing the chatbot
- Starting a conversation
- Sending messages
- Handling responses
"""

import asyncio
import os
from chatbot_system import ChatbotEngine


async def main():
    """Run a basic conversation example."""
    
    # Set environment variables (in production, use .env file)
    os.environ["GEMINI_API_KEY"] = "your_api_key_here"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    # Initialize chatbot
    print("Initializing chatbot...")
    bot = ChatbotEngine(
        persona_config_path="config/persona.yaml",
        redis_url=os.getenv("REDIS_URL"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        enable_safety=True,
        enable_tone_adaptation=True
    )
    
    # Check health
    print("Checking system health...")
    health = await bot.health_check()
    print(f"Health status: {health}")
    
    if not health["overall"]:
        print("System not healthy. Please check configuration.")
        return
    
    # User and session IDs
    user_id = "user_123"
    session_id = "session_abc"
    
    # Start conversation
    print("\n" + "="*50)
    print("CONVERSATION START")
    print("="*50 + "\n")
    
    greeting = await bot.start_conversation(user_id, session_id)
    print(f"Bot: {greeting.text}\n")
    
    # Conversation examples
    messages = [
        "Hey! How's it going?",
        "I'm into anime and gaming, what about you?",
        "Yeah! Currently watching Demon Slayer, it's so good",
        "Do you like coffee?",
        "Nice! I'm more of a night owl myself haha"
    ]
    
    for user_message in messages:
        print(f"User: {user_message}")
        
        # Send message and get response
        response = await bot.chat(
            user_id=user_id,
            message=user_message,
            session_id=session_id
        )
        
        print(f"Bot: {response.text}")
        print(f"[Detected tone: {response.detected_tone}, "
              f"Tokens: {response.tokens_used}, "
              f"Time: {response.response_time_ms:.0f}ms]\n")
        
        # Small delay for natural feel
        await asyncio.sleep(1)
    
    # Get user stats
    print("\n" + "="*50)
    print("USER STATISTICS")
    print("="*50)
    stats = await bot.get_user_stats(user_id)
    print(f"User ID: {stats['user_id']}")
    print(f"Interactions: {stats['interaction_count']}")
    print(f"Interests: {', '.join(stats['interests'])}")
    
    # System stats
    print("\n" + "="*50)
    print("SYSTEM STATISTICS")
    print("="*50)
    sys_stats = bot.get_system_stats()
    print(f"Total conversations: {sys_stats['total_conversations']}")
    print(f"Total tokens used: {sys_stats['total_tokens']}")
    print(f"Persona: {sys_stats['persona_name']}")
    print(f"Model: {sys_stats['model']}")
    
    print("\nConversation complete!")


if __name__ == "__main__":
    asyncio.run(main())


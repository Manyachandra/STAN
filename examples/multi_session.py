"""
Multi-Session Example

Demonstrates:
- Multiple conversations with same user
- Memory persistence across sessions
- Long-term context retention
"""

import asyncio
import os
from chatbot_system import ChatbotEngine
import uuid


async def session_1(bot, user_id):
    """First conversation session."""
    session_id = str(uuid.uuid4())
    
    print("\n" + "="*60)
    print("SESSION 1 - First Meeting")
    print("="*60 + "\n")
    
    messages = [
        ("User", "Hey there!"),
        ("User", "I'm Alex, nice to meet you"),
        ("User", "I'm really into photography and hiking"),
        ("User", "Yeah, I try to go out every weekend when weather's good"),
        ("User", "Alright, gotta run! Talk later")
    ]
    
    for role, msg in messages:
        if role == "User":
            print(f"{role}: {msg}")
            response = await bot.chat(user_id, msg, session_id)
            print(f"Bot: {response.text}\n")
            await asyncio.sleep(0.5)


async def session_2(bot, user_id):
    """Second conversation session (days later)."""
    session_id = str(uuid.uuid4())
    
    print("\n" + "="*60)
    print("SESSION 2 - Returning User (3 days later)")
    print("="*60 + "\n")
    
    # Bot should remember Alex likes photography and hiking
    messages = [
        ("User", "Hey! I'm back"),
        ("User", "Went on an amazing hike this weekend!"),
        ("User", "Got some incredible shots of the sunset"),
        ("User", "Yeah! My photography is really improving"),
        ("User", "Cool, catch you later!")
    ]
    
    for role, msg in messages:
        if role == "User":
            print(f"{role}: {msg}")
            response = await bot.chat(user_id, msg, session_id)
            print(f"Bot: {response.text}\n")
            await asyncio.sleep(0.5)


async def session_3(bot, user_id):
    """Third conversation session (weeks later)."""
    session_id = str(uuid.uuid4())
    
    print("\n" + "="*60)
    print("SESSION 3 - Long-term Memory Test (2 weeks later)")
    print("="*60 + "\n")
    
    # Bot should still remember key details about Alex
    messages = [
        ("User", "Yo! Long time no see"),
        ("User", "Been busy with work and stuff"),
        ("User", "Still trying to get out for hikes when I can"),
        ("User", "Oh yeah, remember I mentioned photography? I entered a competition!"),
        ("User", "Thanks! Will let you know how it goes")
    ]
    
    for role, msg in messages:
        if role == "User":
            print(f"{role}: {msg}")
            response = await bot.chat(user_id, msg, session_id)
            print(f"Bot: {response.text}\n")
            await asyncio.sleep(0.5)


async def main():
    """Run multi-session example."""
    
    # Setup
    os.environ["GEMINI_API_KEY"] = "your_api_key_here"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    bot = ChatbotEngine(
        persona_config_path="config/persona.yaml",
        redis_url=os.getenv("REDIS_URL"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    user_id = "alex_user_456"
    
    # Run sessions
    await session_1(bot, user_id)
    await asyncio.sleep(2)
    
    await session_2(bot, user_id)
    await asyncio.sleep(2)
    
    await session_3(bot, user_id)
    
    # Show final stats
    print("\n" + "="*60)
    print("FINAL USER PROFILE")
    print("="*60)
    stats = await bot.get_user_stats(user_id)
    print(f"Name: {stats['name']}")
    print(f"Total interactions: {stats['interaction_count']}")
    print(f"Interests: {', '.join(stats['interests'])}")
    print(f"Past conversations: {stats['past_conversations']}")
    print(f"First seen: {stats['first_seen']}")
    print(f"Last seen: {stats['last_seen']}")


if __name__ == "__main__":
    asyncio.run(main())


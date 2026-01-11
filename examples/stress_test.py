"""
Stress Test Example

Tests:
- Concurrent users
- High message volume
- Performance under load
- Memory efficiency
"""

import asyncio
import os
import time
from chatbot_system import ChatbotEngine
import uuid
import random


async def simulate_user(bot, user_id, message_count=5):
    """Simulate a single user's conversation."""
    session_id = str(uuid.uuid4())
    
    messages = [
        "Hey!",
        "How are you doing?",
        "I'm into gaming and music",
        "Yeah, mostly RPGs and indie games",
        "Cool, catch you later!"
    ]
    
    results = {
        "user_id": user_id,
        "messages_sent": 0,
        "total_time": 0,
        "errors": 0
    }
    
    try:
        for i in range(min(message_count, len(messages))):
            msg = messages[i]
            start = time.time()
            
            response = await bot.chat(user_id, msg, session_id)
            
            elapsed = time.time() - start
            results["messages_sent"] += 1
            results["total_time"] += elapsed
            
            if not response.safety_passed:
                results["errors"] += 1
            
            # Small random delay
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    except Exception as e:
        print(f"Error for user {user_id}: {e}")
        results["errors"] += 1
    
    return results


async def run_stress_test(num_users=50, messages_per_user=5):
    """Run stress test with multiple concurrent users."""
    
    print(f"\n{'='*60}")
    print(f"STRESS TEST: {num_users} concurrent users")
    print(f"{'='*60}\n")
    
    # Setup
    os.environ["GEMINI_API_KEY"] = "your_api_key_here"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    bot = ChatbotEngine(
        persona_config_path="config/persona.yaml",
        redis_url=os.getenv("REDIS_URL"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # Generate user IDs
    user_ids = [f"stress_user_{i}" for i in range(num_users)]
    
    print(f"Starting test with {num_users} users...")
    print(f"Each user will send {messages_per_user} messages\n")
    
    start_time = time.time()
    
    # Run all users concurrently
    tasks = [
        simulate_user(bot, user_id, messages_per_user)
        for user_id in user_ids
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analyze results
    successful = [r for r in results if isinstance(r, dict)]
    failed = [r for r in results if not isinstance(r, dict)]
    
    total_messages = sum(r["messages_sent"] for r in successful)
    total_errors = sum(r["errors"] for r in successful)
    avg_time_per_message = sum(r["total_time"] for r in successful) / total_messages if total_messages > 0 else 0
    
    # Print results
    print(f"\n{'='*60}")
    print("STRESS TEST RESULTS")
    print(f"{'='*60}\n")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Successful Users: {len(successful)}/{num_users}")
    print(f"Failed Users: {len(failed)}")
    print(f"Total Messages Sent: {total_messages}")
    print(f"Total Errors: {total_errors}")
    print(f"Messages/Second: {total_messages/total_duration:.2f}")
    print(f"Avg Response Time: {avg_time_per_message:.3f}s")
    
    # System stats
    sys_stats = bot.get_system_stats()
    print(f"\nTotal Tokens Used: {sys_stats['total_tokens']}")
    print(f"Avg Tokens/Message: {sys_stats['total_tokens']/total_messages:.0f}")
    
    print("\nStress test complete!")


if __name__ == "__main__":
    # Start with smaller number for testing
    asyncio.run(run_stress_test(num_users=10, messages_per_user=3))
    
    # For actual stress test, use:
    # asyncio.run(run_stress_test(num_users=100, messages_per_user=5))


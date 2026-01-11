"""
Redis Backend - High-performance memory storage using Redis.

Provides fast, scalable storage for:
- User profiles
- Session contexts
- Conversation summaries
"""

import redis.asyncio as aioredis
from typing import Optional, List
import os


class RedisBackend:
    """
    Redis storage backend for memory management.
    
    Uses async Redis for non-blocking operations.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis backend.
        
        Args:
            redis_url: Redis connection URL (defaults to env var REDIS_URL)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Establish connection to Redis."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        
        Args:
            key: Storage key
            
        Returns:
            Value string or None if not found
        """
        await self.connect()
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """
        Set key-value pair with optional TTL.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time-to-live in seconds (optional)
        """
        await self.connect()
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)
    
    async def delete(self, key: str):
        """
        Delete a key.
        
        Args:
            key: Storage key
        """
        await self.connect()
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if exists, False otherwise
        """
        await self.connect()
        return await self.redis.exists(key) > 0
    
    async def get_list(self, key: str, limit: int = 10) -> List[str]:
        """
        Get list of values (for conversation summaries).
        
        Args:
            key: List key
            limit: Maximum number of items to retrieve
            
        Returns:
            List of values
        """
        await self.connect()
        items = await self.redis.lrange(key, 0, limit - 1)
        return items if items else []
    
    async def add_to_list(self, key: str, value: str, max_length: Optional[int] = None):
        """
        Add value to list (FIFO).
        
        Args:
            key: List key
            value: Value to add
            max_length: Maximum list length (oldest items removed if exceeded)
        """
        await self.connect()
        
        # Add to front of list
        await self.redis.lpush(key, value)
        
        # Trim if max_length specified
        if max_length:
            await self.redis.ltrim(key, 0, max_length - 1)
    
    async def get_hash(self, key: str) -> dict:
        """
        Get hash (dictionary) value.
        
        Args:
            key: Hash key
            
        Returns:
            Dictionary of hash fields
        """
        await self.connect()
        return await self.redis.hgetall(key)
    
    async def set_hash(self, key: str, mapping: dict, ttl: Optional[int] = None):
        """
        Set hash (dictionary) value.
        
        Args:
            key: Hash key
            mapping: Dictionary to store
            ttl: Time-to-live in seconds (optional)
        """
        await self.connect()
        await self.redis.hset(key, mapping=mapping)
        
        if ttl:
            await self.redis.expire(key, ttl)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.
        
        Args:
            key: Counter key
            amount: Amount to increment by
            
        Returns:
            New counter value
        """
        await self.connect()
        return await self.redis.incrby(key, amount)
    
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "session:*")
            
        Returns:
            List of matching keys
        """
        await self.connect()
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        return keys
    
    async def set_with_expiry(self, key: str, value: str, seconds: int):
        """
        Set key with automatic expiry.
        
        Args:
            key: Storage key
            value: Value to store
            seconds: Seconds until expiry
        """
        await self.connect()
        await self.redis.setex(key, seconds, value)
    
    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Storage key
            
        Returns:
            Remaining seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        await self.connect()
        return await self.redis.ttl(key)
    
    async def ping(self) -> bool:
        """
        Check if Redis is responsive.
        
        Returns:
            True if connection is healthy
        """
        try:
            await self.connect()
            return await self.redis.ping()
        except Exception:
            return False
    
    def __repr__(self) -> str:
        return f"RedisBackend(url={self.redis_url})"


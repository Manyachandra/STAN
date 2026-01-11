"""
MongoDB backend for memory storage.
Uses Motor for async operations.
"""
import os
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDBBackend:
    """MongoDB backend for persistent memory storage."""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "chatbot_memory"):
        """
        Initialize MongoDB backend.
        
        Args:
            uri: MongoDB connection URI (defaults to env var MONGODB_URI)
            db_name: Database name to use
        """
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name
        self.client = None
        self.db = None
        
    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            if not self.client:
                self.client = AsyncIOMotorClient(
                    self.uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                # Test connection
                await self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                
                # Create indexes for better query performance
                await self.db.memories.create_index("key")
                await self.db.memories.create_index("last_updated")
                await self.db.memories.create_index("expires_at")
                
            return True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    async def get(self, key: str) -> Optional[str]:
        """
        Retrieve a value from MongoDB.
        
        Args:
            key: Storage key
        
        Returns:
            Value string or None if not found
        """
        await self.connect()
        
        try:
            document = await self.db.memories.find_one({"key": key})
            
            if not document:
                return None
            
            # Check if expired
            if "expires_at" in document:
                if document["expires_at"] < datetime.utcnow():
                    await self.delete(key)
                    return None
            
            return document.get("value")
        except Exception as e:
            print(f"Error retrieving data from MongoDB: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """
        Set key-value pair with optional TTL.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time-to-live in seconds (optional)
        """
        await self.connect()
        
        try:
            document = {
                "key": key,
                "value": value,
                "last_updated": datetime.utcnow()
            }
            
            if ttl:
                document["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Upsert: update if exists, insert if not
            await self.db.memories.update_one(
                {"key": key},
                {"$set": document},
                upsert=True
            )
        except Exception as e:
            print(f"Error storing data in MongoDB: {e}")
    
    async def delete(self, key: str):
        """
        Delete a key.
        
        Args:
            key: Storage key
        """
        await self.connect()
        
        try:
            await self.db.memories.delete_one({"key": key})
        except Exception as e:
            print(f"Error deleting data from MongoDB: {e}")
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Storage key
        
        Returns:
            True if exists, False otherwise
        """
        await self.connect()
        return await self.get(key) is not None
    
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
        
        try:
            document = await self.db.memories.find_one({"key": key})
            if document and "list_values" in document:
                return document["list_values"][:limit]
            return []
        except Exception as e:
            print(f"Error getting list from MongoDB: {e}")
            return []
    
    async def add_to_list(self, key: str, value: str, max_length: Optional[int] = None):
        """
        Add value to list (FIFO).
        
        Args:
            key: List key
            value: Value to add
            max_length: Maximum list length (oldest items removed if exceeded)
        """
        await self.connect()
        
        try:
            # Get existing list
            document = await self.db.memories.find_one({"key": key})
            
            if document and "list_values" in document:
                list_values = document["list_values"]
            else:
                list_values = []
            
            # Add to front
            list_values.insert(0, value)
            
            # Trim if needed
            if max_length and len(list_values) > max_length:
                list_values = list_values[:max_length]
            
            # Save back
            await self.db.memories.update_one(
                {"key": key},
                {"$set": {"key": key, "list_values": list_values, "last_updated": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            print(f"Error adding to list in MongoDB: {e}")
    
    async def get_hash(self, key: str) -> dict:
        """
        Get hash (dictionary) value.
        
        Args:
            key: Hash key
        
        Returns:
            Dictionary of hash fields
        """
        await self.connect()
        
        try:
            document = await self.db.memories.find_one({"key": key})
            if document and "hash_value" in document:
                return document["hash_value"]
            return {}
        except Exception as e:
            print(f"Error getting hash from MongoDB: {e}")
            return {}
    
    async def set_hash(self, key: str, mapping: dict, ttl: Optional[int] = None):
        """
        Set hash (dictionary) value.
        
        Args:
            key: Hash key
            mapping: Dictionary to store
            ttl: Time-to-live in seconds (optional)
        """
        await self.connect()
        
        try:
            document = {
                "key": key,
                "hash_value": mapping,
                "last_updated": datetime.utcnow()
            }
            
            if ttl:
                document["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
            
            await self.db.memories.update_one(
                {"key": key},
                {"$set": document},
                upsert=True
            )
        except Exception as e:
            print(f"Error setting hash in MongoDB: {e}")
    
    async def ping(self) -> bool:
        """
        Check if MongoDB is responsive.
        
        Returns:
            True if connection is healthy
        """
        try:
            await self.connect()
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def __repr__(self) -> str:
        return f"MongoDBBackend(uri={self.uri[:20]}...)"


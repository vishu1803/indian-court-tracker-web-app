# backend/app/redis_client.py
import redis
import json
import logging
from typing import Any, Optional, Union
from datetime import datetime, timedelta, date
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def set_case_data(self, case_type: str, case_number: str, year: int, data: dict, ttl_hours: int = None) -> bool:
        """Cache case search results"""
        if not self.is_available():
            return False
        
        try:
            key = f"case:{case_type}:{case_number}:{year}"
            ttl = ttl_hours or settings.cache_ttl_hours
            ttl_seconds = ttl * 3600
            
            # Serialize data with datetime handling
            serialized_data = json.dumps(data, default=self._json_serializer)
            
            result = self.redis_client.setex(key, ttl_seconds, serialized_data)
            logger.debug(f"Cached case data: {key}")
            return result
        except Exception as e:
            logger.error(f"Error caching case data: {e}")
            return False
    
    def get_case_data(self, case_type: str, case_number: str, year: int) -> Optional[dict]:
        """Retrieve cached case search results"""
        if not self.is_available():
            return None
        
        try:
            key = f"case:{case_type}:{case_number}:{year}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for case: {key}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for case: {key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached case data: {e}")
            return None
    
    def set_cause_list(self, date: str, court_name: str, data: list, ttl_hours: int = None) -> bool:
        """Cache cause list data"""
        if not self.is_available():
            return False
        
        try:
            key = f"cause_list:{date}:{court_name}"
            ttl = ttl_hours or settings.cause_list_cache_hours
            ttl_seconds = ttl * 3600
            
            serialized_data = json.dumps(data, default=self._json_serializer)
            
            result = self.redis_client.setex(key, ttl_seconds, serialized_data)
            logger.debug(f"Cached cause list: {key}")
            return result
        except Exception as e:
            logger.error(f"Error caching cause list: {e}")
            return False
    
    def get_cause_list(self, date: str, court_name: str) -> Optional[list]:
        """Retrieve cached cause list"""
        if not self.is_available():
            return None
        
        try:
            key = f"cause_list:{date}:{court_name}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for cause list: {key}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for cause list: {key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached cause list: {e}")
            return None
    
    def invalidate_case_cache(self, case_type: str, case_number: str, year: int) -> bool:
        """Remove case data from cache"""
        if not self.is_available():
            return False
        
        try:
            key = f"case:{case_type}:{case_number}:{year}"
            result = self.redis_client.delete(key)
            logger.debug(f"Invalidated cache for: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """Get Redis cache statistics"""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "available",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects"""
        if isinstance(obj, (datetime, )):
            return obj.isoformat()
        elif isinstance(obj, date):  # Add this line
            return obj.isoformat()   # Add this line
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def clear_all_cache(self) -> bool:
        """Clear all cached data (use with caution)"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Create global Redis client instance
redis_client = RedisClient()

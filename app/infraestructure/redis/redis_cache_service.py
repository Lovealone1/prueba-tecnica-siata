import json
from typing import Any, List, Optional, TypeVar
from app.core.settings import settings
import redis.asyncio as redis

T = TypeVar("T")

class RedisCacheService:
    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis_client = redis_client
        self.key_prefix = settings.REDIS_KEY_PREFIX

    def _get_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    def _serialize(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def _deserialize(self, value: str) -> Any:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        cached_value = await self.redis_client.get(self._get_key(key))
        if cached_value is None:
            return None
        return self._deserialize(cached_value)

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        if not self.redis_client:
            return
        serialized_value = self._serialize(value)
        effective_ttl = ttl_seconds if ttl_seconds is not None else settings.REDIS_TTL_SECONDS

        if effective_ttl > 0:
            await self.redis_client.set(self._get_key(key), serialized_value, ex=effective_ttl)
        else:
            await self.redis_client.set(self._get_key(key), serialized_value)

    async def delete(self, key: str) -> None:
        if not self.redis_client:
            return
        await self.redis_client.delete(self._get_key(key))

    async def sadd(self, key: str, value: str) -> None:
        if not self.redis_client:
            return
        await self.redis_client.sadd(self._get_key(key), value)

    async def srem(self, key: str, value: str) -> None:
        if not self.redis_client:
            return
        await self.redis_client.srem(self._get_key(key), value)

    async def smembers(self, key: str) -> List[str]:
        if not self.redis_client:
            return []
        members = await self.redis_client.smembers(self._get_key(key))
        return list(members)

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        if not self.redis_client or not keys:
            return []
        prefixed_keys = [self._get_key(k) for k in keys]
        results = await self.redis_client.mget(prefixed_keys)
        return [self._deserialize(val) if val is not None else None for val in results]

    async def incr(self, key: str, ttl_seconds: Optional[int] = None) -> int:
        if not self.redis_client:
            return 0
        prefixed_key = self._get_key(key)
        new_value = await self.redis_client.incr(prefixed_key)
        
        # If it's a new key and TTL is provided, set the expiration
        if new_value == 1 and ttl_seconds and ttl_seconds > 0:
            await self.redis_client.expire(prefixed_key, ttl_seconds)
            
        return new_value

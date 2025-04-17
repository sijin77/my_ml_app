import json
import zlib
import logging
from datetime import timedelta
from redis.asyncio import Redis
from typing import Optional, List

logger = logging.getLogger(__name__)


class RedisHistoryManager:
    def __init__(self, redis_url: str, ttl_seconds: int = 86400):
        self.redis = Redis.from_url(redis_url, decode_responses=False)
        self.ttl = timedelta(seconds=ttl_seconds)

    async def get_history(self, session_id: str) -> Optional[List[dict]]:
        try:
            compressed = await self.redis.get(f"history:{session_id}")
            if compressed:
                return json.loads(zlib.decompress(compressed).decode("utf-8"))
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None

    async def save_history(self, session_id: str, history: List[dict]):
        try:
            compressed = zlib.compress(json.dumps(history).encode("utf-8"))
            await self.redis.setex(f"history:{session_id}", self.ttl, compressed)
        except Exception as e:
            logger.error(f"Redis save error: {e}")
            raise

    async def clear_history(self, session_id: str):
        try:
            await self.redis.delete(f"history:{session_id}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            raise

    async def close(self):
        await self.redis.close()

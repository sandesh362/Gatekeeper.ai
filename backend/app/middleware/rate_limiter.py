import time
import redis.asyncio as redis
from fastapi import HTTPException
from app.core.config import settings
class RateLimiter:
    def __init__(self): self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    async def check(self, key_id: str, limit: int) -> None:
        now, bucket = time.time(), f"gatekeeper:ratelimit:{key_id}"
        try:
            pipe = self._redis.pipeline(); pipe.zremrangebyscore(bucket, 0, now - 60); pipe.zcard(bucket)
            _, count = await pipe.execute()
            if int(count) >= limit: raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})
            pipe = self._redis.pipeline(); pipe.zadd(bucket, {f"{now}:{time.time_ns()}": now}); pipe.expire(bucket, 60); await pipe.execute()
        except HTTPException: raise
        except redis.RedisError as exc: raise HTTPException(503, "Rate limiter unavailable") from exc
    async def close(self): await self._redis.aclose()
rate_limiter = RateLimiter()

import redis.asyncio as aioredis
from app.core.config import settings

# Async Redis client with a connection pool.
# We set decode_responses=True to automatically handle string payloads instead of bytes.
redis_client: aioredis.Redis = aioredis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=10
)

async def get_redis() -> aioredis.Redis:
    """Dependency injection helper returning the shared async Redis client."""
    return redis_client

"""Redis cache-aside for chat answers. Failures degrade to cache misses."""

import hashlib
import logging

import redis.asyncio as redis

from config import settings

logger = logging.getLogger("ai_doc_assistant.cache")

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    """Create the shared Redis client on first use."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def cache_key(query: str, user_id: int) -> str:
    """Build the cache key: chat:{user_id}:{md5(query)} (scoped per user so documents never leak)."""
    return f"chat:{user_id}:{hashlib.md5(query.encode()).hexdigest()}"


async def get_cached(query: str, user_id: int) -> str | None:
    """Return the cached answer for a query, or None on a miss or Redis error."""
    try:
        return await _get_client().get(cache_key(query, user_id))
    except Exception:  # noqa: BLE001
        logger.warning("Redis get failed", exc_info=True)
        return None


async def set_cached(query: str, user_id: int, answer: str) -> None:
    """Cache an answer with the configured TTL (default 1 hour)."""
    try:
        await _get_client().set(cache_key(query, user_id), answer, ex=settings.cache_ttl_seconds)
    except Exception:  # noqa: BLE001
        logger.warning("Redis set failed", exc_info=True)


async def clear_user_cache(user_id: int) -> None:
    """Delete all of a user's cached answers (used when a document is deleted)."""
    try:
        client = _get_client()
        keys = [key async for key in client.scan_iter(match=f"chat:{user_id}:*")]
        if keys:
            await client.delete(*keys)
    except Exception:  # noqa: BLE001
        logger.warning("Redis clear failed", exc_info=True)

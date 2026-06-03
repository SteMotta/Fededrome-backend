import json
import inspect
import redis.asyncio as redis
from typing import Callable, Any
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_or_set_cache(key: str, fetch_func: Callable, ttl: int = 3600) -> Any:
    """Ritorna il valore dalla cache Redis; se assente lo calcola con fetch_func e lo salva."""
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    data = fetch_func()
    if inspect.isawaitable(data):
        data = await data

    if data:
        await redis_client.setex(key, ttl, json.dumps(data))
    return data


async def invalidate_cache(key: str) -> None:
    """Elimina una chiave dalla cache."""
    await redis_client.delete(key)
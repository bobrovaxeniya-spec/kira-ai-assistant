import os
from typing import Optional

"""Simple session store abstraction.

If REDIS_URL is provided and aioredis is available, use Redis as the backend.
Otherwise fall back to an in-memory dict store (not persistent, intended for dev).
"""

REDIS_URL = os.getenv("REDIS_URL")


class InMemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    async def set(self, key: str, value: str) -> None:
        self._data[key] = value


class RedisStore:
    def __init__(self, url: str) -> None:
        # aioredis imported lazily to avoid hard dependency at import time
        import aioredis  # type: ignore

        self._url = url
        self._aioredis = aioredis
        self._client = None

    async def _get_client(self):
        if self._client is None:
            # aioredis.from_url returns a Redis client which supports async get/set
            self._client = await self._aioredis.from_url(self._url)
        return self._client

    async def get(self, key: str) -> Optional[str]:
        client = await self._get_client()
        v = await client.get(key)
        return v.decode() if v else None

    async def set(self, key: str, value: str) -> None:
        client = await self._get_client()
        await client.set(key, value)


def get_store() -> object:
    """Return an instance of the best available store.

    Returns:
        RedisStore or InMemoryStore instance. Both implement async get/set.
    """
    if REDIS_URL:
        try:
            return RedisStore(REDIS_URL)
        except Exception:
            # aioredis not installed or connection setup failed — fallback
            return InMemoryStore()
    return InMemoryStore()


store = get_store()

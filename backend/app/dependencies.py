from fastapi import Request

from app.services.riot_api import RiotAPIClient
from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache

# Global in-memory cache instance
_memory_cache = MemoryCache()


def get_riot_api(request: Request) -> RiotAPIClient:
    return request.app.state.riot_api


def get_sqlite_cache(request: Request) -> SqliteCache:
    return request.app.state.sqlite_cache


def get_memory_cache() -> MemoryCache:
    return _memory_cache

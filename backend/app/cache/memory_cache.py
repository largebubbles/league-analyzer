"""
In-memory TTL cache with automatic expiration and size limits.
"""
import time
from typing import Any


class MemoryCache:
    """Simple in-memory cache with TTL and max size limit."""

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size

    def get(self, key: str) -> dict | None:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        # Evict oldest entry if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_oldest()

        expiry = time.time() + ttl_seconds
        self._cache[key] = (value, expiry)

    def _evict_oldest(self) -> None:
        """Remove the entry with the earliest expiry time."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

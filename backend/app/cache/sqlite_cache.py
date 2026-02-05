"""
Async SQLite cache for persisting match and timeline data.
"""
import json
import time
import aiosqlite
from app.config import settings


class SqliteCache:
    """Async SQLite-based cache for match and timeline data."""

    def __init__(self):
        self._db = None

    async def init(self) -> None:
        """Initialize database connection and create table if needed."""
        self._db = await aiosqlite.connect(settings.sqlite_db_path)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS match_cache (
                match_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                json_data TEXT NOT NULL,
                cached_at INTEGER NOT NULL,
                PRIMARY KEY (match_id, data_type)
            )
        """)
        await self._db.commit()

    async def get_match(self, match_id: str) -> dict | None:
        """
        Retrieve match data from cache.

        Args:
            match_id: Match identifier

        Returns:
            Match data dict or None if not found
        """
        cursor = await self._db.execute(
            "SELECT json_data FROM match_cache WHERE match_id = ? AND data_type = ?",
            (match_id, "match")
        )
        row = await cursor.fetchone()

        if row:
            return json.loads(row[0])
        return None

    async def store_match(self, match_id: str, data: dict) -> None:
        """
        Store match data in cache.

        Args:
            match_id: Match identifier
            data: Match data to cache
        """
        json_data = json.dumps(data)
        cached_at = int(time.time())

        await self._db.execute(
            "INSERT OR REPLACE INTO match_cache (match_id, data_type, json_data, cached_at) VALUES (?, ?, ?, ?)",
            (match_id, "match", json_data, cached_at)
        )
        await self._db.commit()

    async def get_timeline(self, match_id: str) -> dict | None:
        """
        Retrieve timeline data from cache.

        Args:
            match_id: Match identifier

        Returns:
            Timeline data dict or None if not found
        """
        cursor = await self._db.execute(
            "SELECT json_data FROM match_cache WHERE match_id = ? AND data_type = ?",
            (match_id, "timeline")
        )
        row = await cursor.fetchone()

        if row:
            return json.loads(row[0])
        return None

    async def store_timeline(self, match_id: str, data: dict) -> None:
        """
        Store timeline data in cache.

        Args:
            match_id: Match identifier
            data: Timeline data to cache
        """
        json_data = json.dumps(data)
        cached_at = int(time.time())

        await self._db.execute(
            "INSERT OR REPLACE INTO match_cache (match_id, data_type, json_data, cached_at) VALUES (?, ?, ?, ?)",
            (match_id, "timeline", json_data, cached_at)
        )
        await self._db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()

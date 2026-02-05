import asyncio
import time
from typing import Any

import httpx

from app.config import settings


class RiotAPIClient:
    """Async Riot Games API client with rate limiting and retry logic."""

    def __init__(self):
        self.api_key = settings.riot_api_key
        self.platform = settings.riot_platform
        self.region = settings.riot_region
        self.rate_limit_per_second = settings.rate_limit_per_second
        self.rate_limit_per_2min = settings.rate_limit_per_2min

        # Concurrent request limiting
        self.semaphore = asyncio.Semaphore(10)

        # Token bucket for rate limiting
        self.request_timestamps: list[float] = []
        self.rate_limit_lock = asyncio.Lock()

        # HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "X-Riot-Token": self.api_key,
            },
            timeout=30.0,
        )

    async def _wait_for_rate_limit(self):
        """Wait if approaching rate limits (20/sec or 100/2min)."""
        async with self.rate_limit_lock:
            now = time.time()

            # Clean up old timestamps (older than 2 minutes)
            self.request_timestamps = [
                ts for ts in self.request_timestamps if now - ts < 120
            ]

            # Check 1-second window
            recent_1s = [ts for ts in self.request_timestamps if now - ts < 1]
            if len(recent_1s) >= self.rate_limit_per_second:
                # Wait until oldest request in 1s window expires
                wait_time = 1 - (now - recent_1s[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # Check 2-minute window
            recent_2min = [ts for ts in self.request_timestamps if now - ts < 120]
            if len(recent_2min) >= self.rate_limit_per_2min:
                # Wait until oldest request in 2min window expires
                wait_time = 120 - (now - recent_2min[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # Record this request
            self.request_timestamps.append(time.time())

    async def _request(
        self, method: str, url: str, max_retries: int = 3, **kwargs: Any
    ) -> dict | list:
        """Make HTTP request with rate limiting and retry logic."""
        async with self.semaphore:
            for attempt in range(max_retries):
                await self._wait_for_rate_limit()

                response = await self.client.request(method, url, **kwargs)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    # Rate limited - retry with exponential backoff
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = retry_after * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue

                # Non-200/429 status - raise error
                response.raise_for_status()

            # Max retries exceeded
            raise httpx.HTTPStatusError(
                f"Max retries exceeded for {url}",
                request=response.request,
                response=response,
            )

    def _platform_url(self, path: str) -> str:
        """Build platform routing URL."""
        return f"https://{self.platform}.api.riotgames.com{path}"

    def _regional_url(self, path: str) -> str:
        """Build regional routing URL."""
        return f"https://{self.region}.api.riotgames.com{path}"

    async def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict:
        """GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine} - regional routing"""
        url = self._regional_url(
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return await self._request("GET", url)

    async def get_summoner_by_puuid(self, puuid: str) -> dict:
        """GET /lol/summoner/v4/summoners/by-puuid/{puuid} - platform routing"""
        url = self._platform_url(f"/lol/summoner/v4/summoners/by-puuid/{puuid}")
        return await self._request("GET", url)

    async def get_match_ids(
        self, puuid: str, count: int = 20, queue: int | None = None
    ) -> list[str]:
        """GET /lol/match/v5/matches/by-puuid/{puuid}/ids - regional routing"""
        url = self._regional_url(f"/lol/match/v5/matches/by-puuid/{puuid}/ids")
        params = {"count": count}
        if queue is not None:
            params["queue"] = queue
        return await self._request("GET", url, params=params)

    async def get_match(self, match_id: str) -> dict:
        """GET /lol/match/v5/matches/{matchId} - regional routing"""
        url = self._regional_url(f"/lol/match/v5/matches/{match_id}")
        return await self._request("GET", url)

    async def get_timeline(self, match_id: str) -> dict:
        """GET /lol/match/v5/matches/{matchId}/timeline - regional routing"""
        url = self._regional_url(f"/lol/match/v5/matches/{match_id}/timeline")
        return await self._request("GET", url)

    async def get_ddragon_version(self) -> str:
        """Fetch the latest Data Dragon version (no auth needed)."""
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = await self.client.get(url)
        response.raise_for_status()
        versions = response.json()
        return versions[0]

    async def close(self):
        """Close the httpx client"""
        await self.client.aclose()

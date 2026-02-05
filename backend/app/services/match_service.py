import asyncio
from app.services.riot_api import RiotAPIClient
from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache
from app.schemas.match import MatchSummary, ParticipantSummary


class MatchService:
    def __init__(self, riot_api: RiotAPIClient, sqlite_cache: SqliteCache, memory_cache: MemoryCache):
        self.riot_api = riot_api
        self.sqlite_cache = sqlite_cache
        self.memory_cache = memory_cache

    async def get_match_history(self, puuid: str, count: int = 20, queue: int | None = None) -> list[MatchSummary]:
        """Fetch match IDs, then fetch each match (with caching), shape into MatchSummary list."""
        try:
            # 1. Get match IDs from riot API
            match_ids = await self.riot_api.get_match_ids(puuid, count=count, queue=queue)

            if not match_ids:
                return []

            # 2-4. Fetch matches with limited parallelism
            semaphore = asyncio.Semaphore(5)

            async def fetch_with_semaphore(match_id: str):
                async with semaphore:
                    try:
                        # Try sqlite cache first
                        cached = await self.sqlite_cache.get_match(match_id)
                        if cached:
                            return cached

                        # Fetch from API and cache
                        data = await self.riot_api.get_match(match_id)
                        await self.sqlite_cache.store_match(match_id, data)
                        return data
                    except Exception as e:
                        print(f"Error fetching match {match_id}: {e}")
                        return None

            # Gather all matches
            tasks = [fetch_with_semaphore(match_id) for match_id in match_ids]
            matches = await asyncio.gather(*tasks)

            # 5. Shape each match into MatchSummary
            summaries = []
            for match_data in matches:
                if match_data:
                    summary = self._shape_match(match_data, puuid)
                    if summary:
                        summaries.append(summary)

            # 6. Sort by game_creation descending
            summaries.sort(key=lambda x: x.game_creation, reverse=True)

            return summaries

        except Exception as e:
            print(f"Error in get_match_history: {e}")
            return []

    def _shape_match(self, data: dict, puuid: str) -> MatchSummary | None:
        """Shape raw match data into MatchSummary."""
        try:
            info = data.get("info", {})
            metadata = data.get("metadata", {})
            participants = info.get("participants", [])

            player_data = None
            for participant in participants:
                if participant.get("puuid") == puuid:
                    player_data = participant
                    break

            if not player_data:
                return None

            def _to_participant(p: dict) -> ParticipantSummary:
                return ParticipantSummary(
                    puuid=p.get("puuid", ""),
                    summoner_name=p.get("riotIdGameName") or p.get("summonerName", ""),
                    champion_name=p.get("championName", "Unknown"),
                    champion_id=p.get("championId", 0),
                    team_id=p.get("teamId", 0),
                    kills=p.get("kills", 0),
                    deaths=p.get("deaths", 0),
                    assists=p.get("assists", 0),
                    total_damage_dealt_to_champions=p.get("totalDamageDealtToChampions", 0),
                    gold_earned=p.get("goldEarned", 0),
                    cs=p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0),
                    vision_score=p.get("visionScore", 0),
                    win=p.get("win", False),
                )

            return MatchSummary(
                match_id=metadata.get("matchId", ""),
                game_creation=info.get("gameCreation", 0),
                game_duration_seconds=info.get("gameDuration", 0),
                game_mode=info.get("gameMode", ""),
                queue_id=info.get("queueId", 0),
                player=_to_participant(player_data),
                participants=[_to_participant(p) for p in participants],
            )

        except Exception as e:
            print(f"Error shaping match: {e}")
            return None

    async def get_match_data(self, match_id: str) -> dict:
        """Get raw match data, using cache."""
        try:
            cached = await self.sqlite_cache.get_match(match_id)
            if cached:
                return cached
            data = await self.riot_api.get_match(match_id)
            await self.sqlite_cache.store_match(match_id, data)
            return data
        except Exception as e:
            print(f"Error getting match data: {e}")
            raise

    async def get_timeline_data(self, match_id: str) -> dict:
        """Get raw timeline data, using cache."""
        try:
            cached = await self.sqlite_cache.get_timeline(match_id)
            if cached:
                return cached
            data = await self.riot_api.get_timeline(match_id)
            await self.sqlite_cache.store_timeline(match_id, data)
            return data
        except Exception as e:
            print(f"Error getting timeline data: {e}")
            raise

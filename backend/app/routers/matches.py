from fastapi import APIRouter, Depends, Query, HTTPException
from app.dependencies import get_riot_api, get_sqlite_cache, get_memory_cache
from app.services.riot_api import RiotAPIClient
from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache
from app.services.match_service import MatchService
from app.schemas.match import MatchSummary

router = APIRouter(tags=["matches"])


@router.get("/matches/{puuid}", response_model=list[MatchSummary])
async def get_matches(
    puuid: str,
    count: int = Query(default=20, ge=1, le=100),
    queue: int | None = Query(default=None),
    riot_api: RiotAPIClient = Depends(get_riot_api),
    sqlite_cache: SqliteCache = Depends(get_sqlite_cache),
    memory_cache: MemoryCache = Depends(get_memory_cache),
):
    """
    Get match history for a summoner by PUUID.

    Parameters:
    - puuid: The player's PUUID
    - count: Number of matches to return (1-100, default 20)
    - queue: Optional queue ID to filter matches (e.g., 420 for Ranked Solo/Duo, 400 for Normal Draft)
    """
    try:
        service = MatchService(riot_api, sqlite_cache, memory_cache)
        matches = await service.get_match_history(puuid, count, queue)
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching match history: {str(e)}")

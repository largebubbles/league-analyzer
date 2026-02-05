from fastapi import APIRouter, Depends, HTTPException, Query

import httpx

from app.dependencies import get_riot_api, get_sqlite_cache, get_memory_cache
from app.services.riot_api import RiotAPIClient
from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache
from app.services.analysis_engine import AnalysisEngine
from app.schemas.analysis import MatchAnalysis

router = APIRouter(tags=["analysis"])


@router.get("/analysis/{match_id}", response_model=MatchAnalysis)
async def get_match_analysis(
    match_id: str,
    puuid: str = Query(..., description="Player PUUID for perspective"),
    riot_api: RiotAPIClient = Depends(get_riot_api),
    sqlite_cache: SqliteCache = Depends(get_sqlite_cache),
    memory_cache: MemoryCache = Depends(get_memory_cache),
):
    engine = AnalysisEngine(riot_api, sqlite_cache, memory_cache)
    try:
        return await engine.analyze_match(match_id, puuid)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Match not found")
        raise HTTPException(status_code=502, detail="Riot API error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException

import httpx

from app.dependencies import get_riot_api, get_memory_cache
from app.services.riot_api import RiotAPIClient
from app.cache.memory_cache import MemoryCache
from app.schemas.summoner import SummonerResponse

router = APIRouter(tags=["summoner"])


@router.get("/summoner/{game_name}/{tag_line}", response_model=SummonerResponse)
async def get_summoner(
    game_name: str,
    tag_line: str,
    riot_api: RiotAPIClient = Depends(get_riot_api),
    cache: MemoryCache = Depends(get_memory_cache),
):
    """Get summoner information by Riot ID (game name and tag line)."""

    cache_key = f"summoner:{game_name}:{tag_line}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return SummonerResponse(**cached_data)

    try:
        account = await riot_api.get_account_by_riot_id(game_name, tag_line)
        if not account or "puuid" not in account:
            raise HTTPException(status_code=404, detail="Summoner not found")

        puuid = account["puuid"]
        summoner = await riot_api.get_summoner_by_puuid(puuid)
        if not summoner:
            raise HTTPException(status_code=404, detail="Summoner not found")

        response_data = SummonerResponse(
            puuid=puuid,
            game_name=account.get("gameName", game_name),
            tag_line=account.get("tagLine", tag_line),
            summoner_level=summoner.get("summonerLevel", 0),
            profile_icon_id=summoner.get("profileIconId", 0),
        )

        cache.set(cache_key, response_data.model_dump(), ttl_seconds=300)
        return response_data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Summoner not found")
        raise HTTPException(status_code=e.response.status_code, detail=f"Riot API error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

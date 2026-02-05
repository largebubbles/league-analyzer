from pydantic import BaseModel

class SummonerResponse(BaseModel):
    puuid: str
    game_name: str
    tag_line: str
    summoner_level: int
    profile_icon_id: int

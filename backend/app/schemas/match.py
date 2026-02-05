from pydantic import BaseModel

class ParticipantSummary(BaseModel):
    puuid: str
    summoner_name: str
    champion_name: str
    champion_id: int
    team_id: int       # 100 or 200
    kills: int
    deaths: int
    assists: int
    total_damage_dealt_to_champions: int
    gold_earned: int
    cs: int            # totalMinionsKilled + neutralMinionsKilled
    vision_score: int
    win: bool

class MatchSummary(BaseModel):
    match_id: str
    game_duration_seconds: int
    game_mode: str
    queue_id: int
    game_creation: int  # epoch ms
    player: ParticipantSummary  # the searched player
    participants: list[ParticipantSummary]

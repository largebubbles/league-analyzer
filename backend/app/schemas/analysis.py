from pydantic import BaseModel

class GoldDiffPoint(BaseModel):
    timestamp_ms: int
    minute: int
    team_gold_diff: int      # positive = player's team ahead
    player_gold_diff: int    # this player vs lane opponent (if detectable)

class ObjectiveEvent(BaseModel):
    timestamp_ms: int
    minute: int
    event_type: str          # "BARON", "DRAGON", "HERALD", "TOWER", "INHIBITOR"
    sub_type: str | None     # "FIRE_DRAGON", "ELDER_DRAGON", etc.
    team_id: int
    is_player_team: bool

class KillEvent(BaseModel):
    timestamp_ms: int
    minute: int
    killer_champion: str
    victim_champion: str
    assisting_champions: list[str]
    is_player_team_kill: bool
    position: dict | None = None

class TurningPoint(BaseModel):
    timestamp_ms: int
    minute: int
    gold_diff_before: int
    gold_diff_after: int
    gold_swing: int
    severity: str            # "minor", "major", "decisive"
    correlated_events: list[str]
    insight: str

class PlayerPerformance(BaseModel):
    champion_name: str
    team_id: int
    is_player: bool
    kills: int
    deaths: int
    assists: int
    cs_per_min: float
    gold_per_min: float
    damage_share: float
    gold_share: float
    vision_score: int
    kill_participation: float

class MatchAnalysis(BaseModel):
    match_id: str
    game_duration_seconds: int
    win: bool
    gold_diff_timeline: list[GoldDiffPoint]
    kill_events: list[KillEvent]
    objective_events: list[ObjectiveEvent]
    turning_points: list[TurningPoint]
    player_performance: list[PlayerPerformance]
    summary_insight: str

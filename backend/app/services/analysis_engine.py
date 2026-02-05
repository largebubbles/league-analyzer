"""
Analysis engine -- the top-level orchestrator that composes gold analysis,
momentum detection, event correlation, and insight generation into a
complete MatchAnalysis result.
"""

import asyncio

from app.services.riot_api import RiotAPIClient
from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache
from app.services.match_service import MatchService
from app.analysis.gold_analysis import compute_gold_diff_timeline
from app.analysis.momentum import (
    detect_turning_points,
    detect_lead_reversals,
    merge_turning_points,
)
from app.analysis.event_correlator import (
    extract_events,
    correlate_events_with_turning_points,
)
from app.analysis.insight_generator import (
    generate_turning_point_insight,
    generate_summary_insight,
)
from app.schemas.analysis import (
    MatchAnalysis,
    PlayerPerformance,
    TurningPoint,
)


class AnalysisEngine:
    """Orchestrates the full analysis pipeline for a single match."""

    def __init__(
        self,
        riot_api: RiotAPIClient,
        sqlite_cache: SqliteCache,
        memory_cache: MemoryCache,
    ):
        self.match_service = MatchService(riot_api, sqlite_cache, memory_cache)

    async def analyze_match(self, match_id: str, puuid: str) -> MatchAnalysis:
        """
        Run the complete analysis pipeline:

        1. Fetch match data + timeline in parallel.
        2. Resolve the player's participant ID and team.
        3. Build lookup maps (participant -> champion, participant -> team).
        4. Compute gold diff timeline.
        5. Detect turning points (swings + reversals, merge).
        6. Extract kill / objective events from the timeline.
        7. Correlate events with turning points.
        8. Generate natural-language insights.
        9. Compute player performance stats for all 10 participants.
        10. Assemble and return a MatchAnalysis model.
        """

        # ----- 1. Parallel data fetch --------------------------------
        match_data, timeline_data = await asyncio.gather(
            self.match_service.get_match_data(match_id),
            self.match_service.get_timeline_data(match_id),
        )

        info = match_data.get("info", {})
        participants = info.get("participants", [])
        game_duration_seconds: int = info.get("gameDuration", 0)

        # ----- 2. Find the queried player ----------------------------
        player_participant_id: int | None = None
        player_team_id: int = 100
        player_win: bool = False

        for p in participants:
            if p.get("puuid") == puuid:
                player_participant_id = p.get("participantId")
                player_team_id = p.get("teamId", 100)
                player_win = p.get("win", False)
                break

        if player_participant_id is None:
            raise ValueError(
                f"Player with puuid {puuid} not found in match {match_id}"
            )

        # ----- 3. Build lookup maps ----------------------------------
        participant_id_to_champion: dict[int, str] = {}
        participant_id_to_team: dict[int, int] = {}

        for p in participants:
            pid = p.get("participantId")
            if pid is not None:
                participant_id_to_champion[pid] = p.get("championName", "Unknown")
                participant_id_to_team[pid] = p.get("teamId", 0)

        # ----- 4. Gold diff timeline ---------------------------------
        gold_timeline = compute_gold_diff_timeline(
            timeline_data,
            player_team_id,
            participant_id_to_team,
        )

        # ----- 5. Turning-point detection ----------------------------
        swing_points = detect_turning_points(gold_timeline)
        reversal_points = detect_lead_reversals(gold_timeline)
        turning_points = merge_turning_points(swing_points, reversal_points)

        # ----- 6. Event extraction -----------------------------------
        kill_events, objective_events, all_raw_events = extract_events(
            timeline_data,
            participant_id_to_champion,
            participant_id_to_team,
            player_team_id,
        )

        # ----- 7. Event correlation ----------------------------------
        turning_points = correlate_events_with_turning_points(
            turning_points,
            all_raw_events,
            participant_id_to_champion,
            participant_id_to_team,
            player_team_id,
        )

        # ----- 8. Insight generation ---------------------------------
        enriched_tps: list[TurningPoint] = []
        for tp in turning_points:
            insight = generate_turning_point_insight(tp)
            enriched_tps.append(
                TurningPoint(
                    timestamp_ms=tp.timestamp_ms,
                    minute=tp.minute,
                    gold_diff_before=tp.gold_diff_before,
                    gold_diff_after=tp.gold_diff_after,
                    gold_swing=tp.gold_swing,
                    severity=tp.severity,
                    correlated_events=tp.correlated_events,
                    insight=insight,
                )
            )

        summary = generate_summary_insight(
            enriched_tps,
            player_win,
            gold_timeline,
            game_duration_seconds,
        )

        # ----- 9. Player performance --------------------------------
        player_performance = self._compute_player_performance(
            participants, player_participant_id, game_duration_seconds
        )

        # ----- 10. Assemble result -----------------------------------
        return MatchAnalysis(
            match_id=match_id,
            game_duration_seconds=game_duration_seconds,
            win=player_win,
            gold_diff_timeline=gold_timeline,
            kill_events=kill_events,
            objective_events=objective_events,
            turning_points=enriched_tps,
            player_performance=player_performance,
            summary_insight=summary,
        )

    # ------------------------------------------------------------------ #
    #  Player performance computation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_player_performance(
        participants: list[dict],
        player_participant_id: int,
        game_duration_seconds: int,
    ) -> list[PlayerPerformance]:
        """
        Compute per-player performance metrics for all 10 participants.

        Metrics:
          - cs_per_min: (totalMinionsKilled + neutralMinionsKilled) / minutes
          - gold_per_min: goldEarned / minutes
          - damage_share: totalDamageDealtToChampions / team total damage
          - gold_share: goldEarned / team total gold
          - kill_participation: (kills + assists) / team total kills
        """
        game_minutes = game_duration_seconds / 60.0
        if game_minutes <= 0:
            game_minutes = 1.0  # guard against zero-length games

        # Pre-compute per-team totals
        team_totals: dict[int, dict] = {}
        for p in participants:
            tid = p.get("teamId", 0)
            if tid not in team_totals:
                team_totals[tid] = {"damage": 0, "gold": 0, "kills": 0}
            team_totals[tid]["damage"] += p.get("totalDamageDealtToChampions", 0)
            team_totals[tid]["gold"] += p.get("goldEarned", 0)
            team_totals[tid]["kills"] += p.get("kills", 0)

        results: list[PlayerPerformance] = []

        for p in participants:
            pid = p.get("participantId")
            tid = p.get("teamId", 0)
            totals = team_totals.get(tid, {"damage": 1, "gold": 1, "kills": 1})

            kills = p.get("kills", 0)
            deaths = p.get("deaths", 0)
            assists = p.get("assists", 0)
            cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
            gold = p.get("goldEarned", 0)
            damage = p.get("totalDamageDealtToChampions", 0)
            vision = p.get("visionScore", 0)

            team_damage = totals["damage"] if totals["damage"] > 0 else 1
            team_gold = totals["gold"] if totals["gold"] > 0 else 1
            team_kills = totals["kills"] if totals["kills"] > 0 else 1

            results.append(
                PlayerPerformance(
                    champion_name=p.get("championName", "Unknown"),
                    team_id=tid,
                    is_player=(pid == player_participant_id),
                    kills=kills,
                    deaths=deaths,
                    assists=assists,
                    cs_per_min=round(cs / game_minutes, 1),
                    gold_per_min=round(gold / game_minutes, 0),
                    damage_share=round(damage / team_damage, 3),
                    gold_share=round(gold / team_gold, 3),
                    vision_score=vision,
                    kill_participation=round((kills + assists) / team_kills, 3),
                )
            )

        return results

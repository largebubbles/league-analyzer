"""
Gold difference timeline computation from raw Riot API timeline data.

Processes per-frame participant gold totals and produces a per-minute
gold-difference timeline from the perspective of the queried player's team.
"""

from app.schemas.analysis import GoldDiffPoint


def compute_gold_diff_timeline(
    timeline: dict,
    player_team_id: int,
    participant_id_to_team: dict[int, int],
) -> list[GoldDiffPoint]:
    """
    Build a gold-difference timeline from Riot match timeline data.

    For each frame in timeline["info"]["frames"]:
      - Sum totalGold for participants on team 100 vs team 200
      - Compute diff = player_team_total - enemy_team_total
      - Record the frame timestamp (ms) and derived minute

    Args:
        timeline: Raw Riot API timeline response dict.
        player_team_id: The team ID (100 or 200) that the queried player is on.
        participant_id_to_team: Mapping of participantId -> teamId for all 10 players.

    Returns:
        Ordered list of GoldDiffPoint, one per timeline frame.
    """
    frames = timeline.get("info", {}).get("frames", [])
    result: list[GoldDiffPoint] = []

    for frame in frames:
        timestamp_ms = frame.get("timestamp", 0)
        minute = timestamp_ms // 60_000

        participant_frames = frame.get("participantFrames", {})

        player_team_gold = 0
        enemy_team_gold = 0

        for pid_str, pf in participant_frames.items():
            pid = int(pid_str)
            total_gold = pf.get("totalGold", 0)
            team_id = participant_id_to_team.get(pid)

            if team_id == player_team_id:
                player_team_gold += total_gold
            else:
                enemy_team_gold += total_gold

        team_gold_diff = player_team_gold - enemy_team_gold

        # Player-specific gold diff: compare the queried player against
        # opposing laner if possible.  The timeline doesn't carry a clean
        # lane-opponent mapping, so we default to 0.
        player_gold_diff = 0

        result.append(
            GoldDiffPoint(
                timestamp_ms=timestamp_ms,
                minute=minute,
                team_gold_diff=team_gold_diff,
                player_gold_diff=player_gold_diff,
            )
        )

    return result

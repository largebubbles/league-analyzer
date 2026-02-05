"""
Event extraction and correlation with turning points.

Walks the Riot API timeline to extract kill, objective, and structure
events, then matches them to detected turning points so each turning
point carries a list of human-readable event descriptions.
"""

from app.schemas.analysis import KillEvent, ObjectiveEvent, TurningPoint


# ------------------------------------------------------------------ #
#  Monster-type normalisation helpers
# ------------------------------------------------------------------ #

_MONSTER_TYPE_MAP: dict[str, str] = {
    "BARON_NASHOR": "BARON",
    "DRAGON": "DRAGON",
    "RIFTHERALD": "HERALD",
    "RIFT_HERALD": "HERALD",
    "ELDER_DRAGON": "DRAGON",
    "HORDE": "HORDE",
}

_MONSTER_DISPLAY: dict[str, str] = {
    "BARON_NASHOR": "Baron Nashor",
    "DRAGON": "Dragon",
    "RIFTHERALD": "Rift Herald",
    "RIFT_HERALD": "Rift Herald",
    "ELDER_DRAGON": "Elder Dragon",
    "HORDE": "Void Grub",
}

_DRAGON_SUB_DISPLAY: dict[str, str] = {
    "FIRE_DRAGON": "Infernal Drake",
    "WATER_DRAGON": "Ocean Drake",
    "EARTH_DRAGON": "Mountain Drake",
    "AIR_DRAGON": "Cloud Drake",
    "HEXTECH_DRAGON": "Hextech Drake",
    "CHEMTECH_DRAGON": "Chemtech Drake",
    "ELDER_DRAGON": "Elder Dragon",
}

_BUILDING_DISPLAY: dict[str, str] = {
    "TOWER_BUILDING": "tower",
    "INHIBITOR_BUILDING": "inhibitor",
}

_LANE_DISPLAY: dict[str, str] = {
    "TOP_LANE": "Top Lane",
    "MID_LANE": "Mid Lane",
    "BOT_LANE": "Bot Lane",
}


# ------------------------------------------------------------------ #
#  Event extraction
# ------------------------------------------------------------------ #

def extract_events(
    timeline: dict,
    participant_id_to_champion: dict[int, str],
    participant_id_to_team: dict[int, int],
    player_team_id: int,
) -> tuple[list[KillEvent], list[ObjectiveEvent], list[dict]]:
    """
    Walk through every frame's event list and extract structured events.

    Args:
        timeline: Raw Riot API timeline response dict.
        participant_id_to_champion: participantId -> champion name mapping.
        participant_id_to_team: participantId -> teamId mapping.
        player_team_id: The queried player's team (100 or 200).

    Returns:
        (kill_events, objective_events, all_raw_events)
        where all_raw_events is a flat list of the raw event dicts (for
        later correlation).
    """
    frames = timeline.get("info", {}).get("frames", [])

    kill_events: list[KillEvent] = []
    objective_events: list[ObjectiveEvent] = []
    all_raw_events: list[dict] = []

    for frame in frames:
        events = frame.get("events", [])
        for event in events:
            event_type = event.get("type", "")
            all_raw_events.append(event)

            if event_type == "CHAMPION_KILL":
                kill_events.append(_parse_kill(event, participant_id_to_champion, participant_id_to_team, player_team_id))

            elif event_type == "ELITE_MONSTER_KILL":
                obj = _parse_objective(event, player_team_id)
                if obj is not None:
                    objective_events.append(obj)

            elif event_type == "BUILDING_KILL":
                obj = _parse_building(event, player_team_id)
                if obj is not None:
                    objective_events.append(obj)

    return kill_events, objective_events, all_raw_events


def _parse_kill(
    event: dict,
    id_to_champ: dict[int, str],
    id_to_team: dict[int, int],
    player_team_id: int,
) -> KillEvent:
    """Parse a CHAMPION_KILL event into a KillEvent."""
    killer_id = event.get("killerId", 0)
    victim_id = event.get("victimId", 0)
    assisting_ids: list[int] = event.get("assistingParticipantIds", [])

    killer_champion = id_to_champ.get(killer_id, "Minion")
    victim_champion = id_to_champ.get(victim_id, "Unknown")
    assisting_champions = [id_to_champ.get(a, "Unknown") for a in assisting_ids]

    # killerId == 0 means executed (tower/minion kill)
    killer_team = id_to_team.get(killer_id)
    is_player_team_kill = killer_team == player_team_id if killer_team is not None else False

    position = event.get("position")

    timestamp_ms = event.get("timestamp", 0)

    return KillEvent(
        timestamp_ms=timestamp_ms,
        minute=timestamp_ms // 60_000,
        killer_champion=killer_champion,
        victim_champion=victim_champion,
        assisting_champions=assisting_champions,
        is_player_team_kill=is_player_team_kill,
        position=position,
    )


def _parse_objective(event: dict, player_team_id: int) -> ObjectiveEvent | None:
    """Parse an ELITE_MONSTER_KILL event into an ObjectiveEvent."""
    monster_type = event.get("monsterType", "")
    normalised = _MONSTER_TYPE_MAP.get(monster_type)
    if normalised is None:
        return None

    killer_team_id = event.get("killerTeamId", 0)
    sub_type = event.get("monsterSubType")
    timestamp_ms = event.get("timestamp", 0)

    return ObjectiveEvent(
        timestamp_ms=timestamp_ms,
        minute=timestamp_ms // 60_000,
        event_type=normalised,
        sub_type=sub_type,
        team_id=killer_team_id,
        is_player_team=killer_team_id == player_team_id,
    )


def _parse_building(event: dict, player_team_id: int) -> ObjectiveEvent | None:
    """Parse a BUILDING_KILL event into an ObjectiveEvent."""
    building_type = event.get("buildingType", "")
    normalised = _BUILDING_DISPLAY.get(building_type)
    if normalised is None:
        return None

    # teamId in BUILDING_KILL is the team that *lost* the building
    lost_team_id = event.get("teamId", 0)
    # The team that destroyed it is the opposite
    destroyer_team_id = 200 if lost_team_id == 100 else 100

    event_type = "TOWER" if building_type == "TOWER_BUILDING" else "INHIBITOR"
    lane = event.get("laneType", "")
    sub_type = _LANE_DISPLAY.get(lane, lane)
    timestamp_ms = event.get("timestamp", 0)

    return ObjectiveEvent(
        timestamp_ms=timestamp_ms,
        minute=timestamp_ms // 60_000,
        event_type=event_type,
        sub_type=sub_type,
        team_id=destroyer_team_id,
        is_player_team=destroyer_team_id == player_team_id,
    )


# ------------------------------------------------------------------ #
#  Event-to-turning-point correlation
# ------------------------------------------------------------------ #

def correlate_events_with_turning_points(
    turning_points: list[TurningPoint],
    all_raw_events: list[dict],
    participant_id_to_champion: dict[int, str],
    participant_id_to_team: dict[int, int],
    player_team_id: int,
    window_ms: int = 90_000,
) -> list[TurningPoint]:
    """
    For each turning point, find timeline events within +/- window_ms/2
    of the turning point's timestamp and attach human-readable descriptions.

    Args:
        turning_points: Previously detected turning points.
        all_raw_events: Flat list of raw event dicts from the timeline.
        participant_id_to_champion: participantId -> champion name.
        participant_id_to_team: participantId -> teamId.
        player_team_id: The queried player's team.
        window_ms: Width of the event-search window (default 90 seconds).

    Returns:
        The same turning points list, with correlated_events populated.
    """
    half_window = window_ms // 2

    updated: list[TurningPoint] = []

    for tp in turning_points:
        low = tp.timestamp_ms - half_window
        high = tp.timestamp_ms + half_window

        descriptions: list[str] = []

        for event in all_raw_events:
            ts = event.get("timestamp", 0)
            if ts < low or ts > high:
                continue

            desc = _describe_event(event, participant_id_to_champion, participant_id_to_team, player_team_id)
            if desc:
                descriptions.append(desc)

        # Rebuild the turning point with correlated events
        updated.append(
            TurningPoint(
                timestamp_ms=tp.timestamp_ms,
                minute=tp.minute,
                gold_diff_before=tp.gold_diff_before,
                gold_diff_after=tp.gold_diff_after,
                gold_swing=tp.gold_swing,
                severity=tp.severity,
                correlated_events=descriptions,
                insight=tp.insight,
            )
        )

    return updated


def _describe_event(
    event: dict,
    id_to_champ: dict[int, str],
    id_to_team: dict[int, int],
    player_team_id: int,
) -> str | None:
    """
    Convert a raw timeline event into a human-readable sentence.

    Returns None for event types we don't care about.
    """
    event_type = event.get("type", "")

    if event_type == "CHAMPION_KILL":
        killer_id = event.get("killerId", 0)
        victim_id = event.get("victimId", 0)
        killer_champ = id_to_champ.get(killer_id, "Minion")
        victim_champ = id_to_champ.get(victim_id, "Unknown")

        killer_team = id_to_team.get(killer_id)
        if killer_team == player_team_id:
            return f"{killer_champ} killed {victim_champ}"
        else:
            return f"{killer_champ} killed {victim_champ} (enemy)"

    if event_type == "ELITE_MONSTER_KILL":
        monster = event.get("monsterType", "")
        sub = event.get("monsterSubType")
        killer_team = event.get("killerTeamId", 0)
        is_player = killer_team == player_team_id
        team_label = "Your team" if is_player else "Enemy team"

        display = _MONSTER_DISPLAY.get(monster, monster)
        if sub and sub in _DRAGON_SUB_DISPLAY:
            display = _DRAGON_SUB_DISPLAY[sub]

        return f"{team_label} secured {display}"

    if event_type == "BUILDING_KILL":
        building = event.get("buildingType", "")
        lost_team = event.get("teamId", 0)
        destroyer_team = 200 if lost_team == 100 else 100
        is_player = destroyer_team == player_team_id
        team_label = "Your team" if is_player else "Enemy team"

        building_name = _BUILDING_DISPLAY.get(building, building)
        lane = _LANE_DISPLAY.get(event.get("laneType", ""), "")
        lane_prefix = f"{lane} " if lane else ""

        return f"{team_label} destroyed {lane_prefix}{building_name}"

    return None

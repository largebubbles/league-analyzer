"""
Template-based natural-language insight generation for turning points
and overall match narrative.
"""

from app.schemas.analysis import TurningPoint, GoldDiffPoint


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def _format_time(minute: int) -> str:
    """Format a minute value as M:00 or MM:00."""
    return f"{minute}:00"


def _format_gold(gold: int) -> str:
    """Format a gold value with comma separators and 'g' suffix."""
    return f"{abs(gold):,}g"


def _count_pattern(events: list[str], pattern: str) -> int:
    """Count how many event strings contain a case-insensitive pattern."""
    p = pattern.lower()
    return sum(1 for e in events if p in e.lower())


def _team_direction(gold_swing: int) -> str:
    """Return 'in your team\'s favor' or 'against your team'."""
    if gold_swing > 0:
        return "in your team's favor"
    return "against your team"


# ------------------------------------------------------------------ #
#  Per-turning-point insight
# ------------------------------------------------------------------ #

def _window_context(tp: TurningPoint) -> str:
    """Describe the time window the gold swing was measured over."""
    before_min = tp.minute - 3 if tp.minute >= 3 else 0
    return f"between {_format_time(before_min)} and {_format_time(tp.minute)}"


def _activity_summary(kill_count: int, tower_events: int, inhibitor_events: int,
                       your_team_objectives: int, enemy_objectives: int) -> str:
    """Build a short summary of all activity in the window."""
    parts: list[str] = []
    if kill_count > 0:
        parts.append(f"{kill_count} kill(s)")
    if tower_events > 0:
        parts.append(f"{tower_events} tower(s)")
    if inhibitor_events > 0:
        parts.append(f"{inhibitor_events} inhibitor(s)")
    obj_total = your_team_objectives + enemy_objectives
    if obj_total > 0:
        parts.append(f"{obj_total} objective(s)")
    if not parts:
        return "farming and map pressure"
    return ", ".join(parts)


def generate_turning_point_insight(tp: TurningPoint) -> str:
    """
    Generate a natural-language insight string for a single turning point
    based on its correlated events and gold swing.

    The gold swing is measured over a ~3 minute sliding window, so insights
    clearly state the time window and don't attribute the full swing to a
    single event.
    """
    events = tp.correlated_events
    swing = tp.gold_swing
    time_str = _format_time(tp.minute)
    gold_str = _format_gold(swing)
    direction = _team_direction(swing)
    window = _window_context(tp)

    has_baron = _count_pattern(events, "Baron") > 0
    has_elder = _count_pattern(events, "Elder") > 0
    has_dragon = _count_pattern(events, "Drake") + _count_pattern(events, "Dragon") > 0

    kill_count = _count_pattern(events, "killed")
    your_team_kills = _count_pattern(events, "killed") - _count_pattern(events, "(enemy)")
    enemy_kills = _count_pattern(events, "(enemy)")

    your_team_objectives = _count_pattern(events, "Your team secured") + _count_pattern(events, "Your team destroyed")
    enemy_objectives = _count_pattern(events, "Enemy team secured") + _count_pattern(events, "Enemy team destroyed")

    tower_events = _count_pattern(events, "tower")
    inhibitor_events = _count_pattern(events, "inhibitor")

    activity = _activity_summary(kill_count, tower_events, inhibitor_events,
                                  your_team_objectives, enemy_objectives)

    # --- Baron fight archetype ---
    if has_baron and kill_count > 0:
        baron_team = "your team" if _count_pattern(events, "Your team secured Baron") > 0 else "enemy team"
        return (
            f"Around {time_str}, a fight broke out over Baron Nashor. "
            f"The {baron_team} secured the objective, with {activity} in the window. "
            f"Over this period the gold shifted by {gold_str} {direction}."
        )

    # --- Baron power play archetype ---
    if has_baron:
        baron_team = "Your team" if _count_pattern(events, "Your team secured Baron") > 0 else "Enemy team"
        return (
            f"Around {time_str}, {baron_team} secured Baron Nashor uncontested. "
            f"The resulting map pressure ({activity}) led to a {gold_str} swing {direction}."
        )

    # --- Elder dragon archetype ---
    if has_elder and kill_count > 0:
        elder_team = "Your team" if _count_pattern(events, "Your team secured Elder") > 0 else "Enemy team"
        return (
            f"Around {time_str}, {elder_team} secured Elder Dragon and fought with "
            f"{activity} in the window. The total gold shifted by {gold_str} {direction}."
        )

    # --- Teamfight swing archetype ---
    if kill_count >= 3:
        if your_team_kills > enemy_kills:
            score_str = f"{your_team_kills} kills for {enemy_kills}"
            team_phrase = "your team's favor"
        elif enemy_kills > your_team_kills:
            score_str = f"{enemy_kills} kills for {your_team_kills}"
            team_phrase = "the enemy's favor"
        else:
            score_str = f"{kill_count} kills traded"
            team_phrase = direction

        extra = ""
        if tower_events > 0 or inhibitor_events > 0:
            structures = []
            if tower_events > 0:
                structures.append(f"{tower_events} tower(s)")
            if inhibitor_events > 0:
                structures.append(f"{inhibitor_events} inhibitor(s)")
            extra = f", plus {' and '.join(structures)} falling"

        return (
            f"A teamfight {window} went in {team_phrase} ({score_str}){extra}. "
            f"Combined with farming and other activity, the total gold swung by {gold_str} {direction}."
        )

    # --- Objective trade archetype ---
    if your_team_objectives > 0 and enemy_objectives > 0:
        return (
            f"Between {_format_time(tp.minute - 3 if tp.minute >= 3 else 0)} and {time_str}, "
            f"both teams traded objectives ({activity}). "
            f"The net gold shift was {gold_str} {direction}."
        )

    # --- Dragon / Herald with kills ---
    if (has_dragon or _count_pattern(events, "Herald") > 0) and kill_count > 0:
        obj_name = "Dragon" if has_dragon else "Rift Herald"
        return (
            f"Around {time_str}, a skirmish near {obj_name} involved {activity}. "
            f"Over this window the gold shifted by {gold_str} {direction}."
        )

    # --- Structure-only ---
    if tower_events > 0 or inhibitor_events > 0:
        structures = []
        if tower_events > 0:
            structures.append(f"{tower_events} tower(s)")
        if inhibitor_events > 0:
            structures.append(f"{inhibitor_events} inhibitor(s)")
        return (
            f"Around {time_str}, {' and '.join(structures)} were destroyed. "
            f"Combined with other activity, the gold shifted by {gold_str} {direction}."
        )

    # --- Kill-only (1-2 kills) ---
    if kill_count > 0:
        return (
            f"Around {time_str}, {kill_count} kill(s) occurred alongside farming advantages. "
            f"Over this window the total gold shifted by {gold_str} {direction}."
        )

    # --- Generic fallback ---
    return (
        f"Between {_format_time(tp.minute - 3 if tp.minute >= 3 else 0)} and {time_str}, "
        f"a {gold_str} gold shift occurred {direction} through a combination of farming, "
        f"kills, and map control."
    )


# ------------------------------------------------------------------ #
#  Match-level summary insight
# ------------------------------------------------------------------ #

def generate_summary_insight(
    turning_points: list[TurningPoint],
    win: bool,
    gold_timeline: list[GoldDiffPoint],
    game_duration_seconds: int,
) -> str:
    """
    Generate a top-level match narrative summarising early game state,
    the most important turning point, and the overall trajectory.

    Structure:
      1. Early game assessment (gold diff at 10 minutes).
      2. Key turning point description.
      3. Contextual closer (comeback, throw, or even game).
    """
    game_minutes = game_duration_seconds // 60

    # --- 1. Early game state ---
    early_gold = _gold_at_minute(gold_timeline, 10)
    if early_gold > 500:
        early_str = f"Your team was ahead by {_format_gold(early_gold)} at 10 minutes."
    elif early_gold < -500:
        early_str = f"Your team was behind by {_format_gold(early_gold)} at 10 minutes."
    else:
        early_str = "The early game was fairly even, with less than 500g difference at 10 minutes."

    # --- 2. Key turning point ---
    key_tp = _find_key_turning_point(turning_points)
    if key_tp is not None:
        tp_time = _format_time(key_tp.minute)
        tp_gold = _format_gold(key_tp.gold_swing)
        tp_dir = _team_direction(key_tp.gold_swing)

        # Pick the most impactful correlated event as a summary label
        event_summary = _summarise_tp_events(key_tp)
        key_str = (
            f"The key moment was at {tp_time} when {event_summary}, "
            f"causing a {tp_gold} swing {tp_dir}."
        )
    else:
        key_str = ""

    # --- 3. Contextual closer ---
    if not turning_points:
        closer = (
            "The game was relatively even throughout, with no major momentum swings. "
            f"{'Your team secured the win' if win else 'Your team was unable to find an advantage'} "
            f"over {game_minutes} minutes."
        )
    elif win and early_gold < -1000:
        closer = (
            "Despite the early deficit, your team mounted a comeback "
            "and closed out the game."
        )
    elif not win and early_gold > 1000:
        closer = (
            "Despite the early lead, your team was unable to close out the game "
            "and ultimately fell behind."
        )
    elif win:
        closer = "Your team maintained pressure and converted advantages into a win."
    else:
        closer = "The enemy team built on their advantages and closed out the game."

    parts = [p for p in [early_str, key_str, closer] if p]
    return " ".join(parts)


# ------------------------------------------------------------------ #
#  Internal helpers
# ------------------------------------------------------------------ #

def _gold_at_minute(gold_timeline: list[GoldDiffPoint], minute: int) -> int:
    """Return the team gold diff at the given minute, or the closest available."""
    if not gold_timeline:
        return 0

    closest: GoldDiffPoint | None = None
    best_dist = float("inf")
    for pt in gold_timeline:
        dist = abs(pt.minute - minute)
        if dist < best_dist:
            best_dist = dist
            closest = pt

    return closest.team_gold_diff if closest else 0


def _find_key_turning_point(turning_points: list[TurningPoint]) -> TurningPoint | None:
    """Find the single most important turning point (highest severity, then largest swing)."""
    if not turning_points:
        return None

    severity_rank = {"minor": 0, "major": 1, "decisive": 2}
    return max(
        turning_points,
        key=lambda tp: (severity_rank.get(tp.severity, 0), abs(tp.gold_swing)),
    )


def _summarise_tp_events(tp: TurningPoint) -> str:
    """
    Pick the most notable correlated event to use in the summary sentence.
    Falls back to a generic description if no events are present.
    """
    events = tp.correlated_events
    if not events:
        return "a significant gold swing occurred"

    # Priority: Baron > Elder > Dragon/Herald > kills > structures
    for keyword in ["Baron", "Elder Dragon", "Dragon", "Drake", "Herald"]:
        for e in events:
            if keyword.lower() in e.lower():
                return e.lower()

    # Fall back to the first kill event
    for e in events:
        if "killed" in e.lower():
            return e.lower()

    # Fall back to first event
    return events[0].lower()

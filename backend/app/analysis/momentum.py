"""
Momentum / turning-point detection using sliding-window analysis
on the gold difference timeline.

Two complementary strategies:
1. Sliding-window swing detection -- finds windows where the gold diff
   changes sharply.
2. Lead-reversal detection -- finds moments the gold diff crosses zero.

Results are merged and deduplicated before being returned.
"""

from app.schemas.analysis import TurningPoint, GoldDiffPoint


# ------------------------------------------------------------------ #
#  Severity helpers
# ------------------------------------------------------------------ #

def _severity_from_swing(swing: int) -> str:
    """Classify the absolute swing magnitude into a severity label."""
    abs_swing = abs(swing)
    if abs_swing >= 4000:
        return "decisive"
    if abs_swing >= 2500:
        return "major"
    return "minor"


_SEVERITY_RANK = {"minor": 0, "major": 1, "decisive": 2}


def _more_severe(a: str, b: str) -> str:
    """Return the more severe of two severity labels."""
    return a if _SEVERITY_RANK.get(a, 0) >= _SEVERITY_RANK.get(b, 0) else b


# ------------------------------------------------------------------ #
#  Sliding-window swing detection
# ------------------------------------------------------------------ #

def detect_turning_points(
    gold_timeline: list[GoldDiffPoint],
    window_size: int = 3,
    min_swing_threshold: int = 1500,
) -> list[TurningPoint]:
    """
    Detect turning points via a sliding window over the gold diff timeline.

    Algorithm
    ---------
    1. Slide a window of *window_size* minutes across the timeline.
    2. Compute swing = gold_diff[end] - gold_diff[start].
    3. If |swing| >= min_swing_threshold, mark as a turning-point candidate.
    4. Within the window, find the minute with the largest single-minute change
       (the "peak change minute") and use that as the representative timestamp.
    5. Merge overlapping candidates that fall within 2 minutes of each other,
       keeping the most severe.

    Returns:
        List of TurningPoint (correlated_events and insight are empty).
    """
    if len(gold_timeline) < 2:
        return []

    # Build a minute-indexed lookup (use first entry per minute)
    by_minute: dict[int, GoldDiffPoint] = {}
    for pt in gold_timeline:
        if pt.minute not in by_minute:
            by_minute[pt.minute] = pt

    minutes_sorted = sorted(by_minute.keys())
    if len(minutes_sorted) < 2:
        return []

    candidates: list[TurningPoint] = []

    for i in range(len(minutes_sorted)):
        start_min = minutes_sorted[i]
        # Find the end of the window
        end_min_target = start_min + window_size
        # Pick the closest available minute <= end_min_target
        end_min = start_min
        for m in minutes_sorted:
            if m <= end_min_target:
                end_min = m
            else:
                break

        if end_min == start_min:
            continue

        start_pt = by_minute[start_min]
        end_pt = by_minute[end_min]
        swing = end_pt.team_gold_diff - start_pt.team_gold_diff

        if abs(swing) < min_swing_threshold:
            continue

        # Find peak change minute within the window
        peak_minute = start_min
        peak_change = 0
        prev_diff = start_pt.team_gold_diff
        for m in minutes_sorted:
            if m <= start_min or m > end_min_target:
                continue
            if m not in by_minute:
                continue
            change = abs(by_minute[m].team_gold_diff - prev_diff)
            if change > peak_change:
                peak_change = change
                peak_minute = m
            prev_diff = by_minute[m].team_gold_diff

        peak_pt = by_minute[peak_minute]

        candidates.append(
            TurningPoint(
                timestamp_ms=peak_pt.timestamp_ms,
                minute=peak_minute,
                gold_diff_before=start_pt.team_gold_diff,
                gold_diff_after=end_pt.team_gold_diff,
                gold_swing=swing,
                severity=_severity_from_swing(swing),
                correlated_events=[],
                insight="",
            )
        )

    # Deduplicate: merge candidates within 2 minutes, keeping most severe
    return _deduplicate(candidates)


# ------------------------------------------------------------------ #
#  Lead-reversal detection
# ------------------------------------------------------------------ #

def detect_lead_reversals(
    gold_timeline: list[GoldDiffPoint],
) -> list[TurningPoint]:
    """
    Find moments where the gold diff crosses zero (lead changes hands).

    For each crossing, we look at a 2-minute window around the crossing to
    determine how large the swing was, then assign severity accordingly.

    Returns:
        List of TurningPoint with severity based on swing around the crossing.
    """
    if len(gold_timeline) < 2:
        return []

    # Build minute-indexed lookup
    by_minute: dict[int, GoldDiffPoint] = {}
    for pt in gold_timeline:
        if pt.minute not in by_minute:
            by_minute[pt.minute] = pt

    minutes_sorted = sorted(by_minute.keys())

    reversals: list[TurningPoint] = []

    for i in range(1, len(minutes_sorted)):
        prev_min = minutes_sorted[i - 1]
        curr_min = minutes_sorted[i]
        prev_diff = by_minute[prev_min].team_gold_diff
        curr_diff = by_minute[curr_min].team_gold_diff

        # Detect zero crossing (sign change, excluding staying at 0)
        if prev_diff == 0 and curr_diff == 0:
            continue
        if (prev_diff > 0 and curr_diff >= 0) or (prev_diff < 0 and curr_diff <= 0):
            continue
        # Also catch transitioning from exactly 0 to non-zero when previous
        # frame had the opposite sign -- but simplest: check sign flip.
        if prev_diff >= 0 and curr_diff >= 0:
            continue
        if prev_diff <= 0 and curr_diff <= 0:
            continue

        # Look at a 2-minute window around the crossing to size the swing
        window_start = max(minutes_sorted[0], curr_min - 2)
        window_end = min(minutes_sorted[-1], curr_min + 2)

        diff_at_start = by_minute.get(window_start, by_minute[prev_min]).team_gold_diff
        diff_at_end = by_minute.get(window_end, by_minute[curr_min]).team_gold_diff

        # Find closest available minutes
        for m in minutes_sorted:
            if m >= window_start:
                diff_at_start = by_minute[m].team_gold_diff
                break
        for m in reversed(minutes_sorted):
            if m <= window_end:
                diff_at_end = by_minute[m].team_gold_diff
                break

        swing = diff_at_end - diff_at_start

        reversals.append(
            TurningPoint(
                timestamp_ms=by_minute[curr_min].timestamp_ms,
                minute=curr_min,
                gold_diff_before=prev_diff,
                gold_diff_after=curr_diff,
                gold_swing=swing,
                severity=_severity_from_swing(swing),
                correlated_events=[],
                insight="",
            )
        )

    return _deduplicate(reversals)


# ------------------------------------------------------------------ #
#  Merging & deduplication
# ------------------------------------------------------------------ #

def _deduplicate(points: list[TurningPoint]) -> list[TurningPoint]:
    """Merge turning points that overlap within 2 minutes, keeping the most severe."""
    if not points:
        return []

    # Sort by minute
    points = sorted(points, key=lambda tp: tp.minute)
    merged: list[TurningPoint] = [points[0]]

    for tp in points[1:]:
        last = merged[-1]
        if tp.minute - last.minute <= 2:
            # Merge: keep the one with higher severity, or larger |swing|
            keep = last
            challenger = tp
            if _SEVERITY_RANK.get(challenger.severity, 0) > _SEVERITY_RANK.get(keep.severity, 0):
                merged[-1] = challenger
            elif (
                _SEVERITY_RANK.get(challenger.severity, 0) == _SEVERITY_RANK.get(keep.severity, 0)
                and abs(challenger.gold_swing) > abs(keep.gold_swing)
            ):
                merged[-1] = challenger
            # else keep existing
        else:
            merged.append(tp)

    return merged


def merge_turning_points(
    swing_points: list[TurningPoint],
    reversal_points: list[TurningPoint],
) -> list[TurningPoint]:
    """
    Combine swing-detected and reversal-detected turning points.

    Deduplicates entries that fall within 2 minutes of each other,
    preferring the higher severity when overlapping.
    """
    combined = list(swing_points) + list(reversal_points)
    return _deduplicate(combined)

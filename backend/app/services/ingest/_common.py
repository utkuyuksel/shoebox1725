"""Shared helpers for api-sports JSON → models mapping.

Three concerns:
- Safe extraction from inconsistent JSON (api-sports sometimes returns
  null where you'd expect a number).
- Idempotent UPSERT helpers tuned for our PK shapes.
- Stat-name → column mapping for fixture statistics (api-sports gives
  human-readable strings like "Shots on Goal" rather than camelCase).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from dateutil import parser as dateparser


def safe_int(v: Any) -> Optional[int]:
    """Parse int from various junk (None, '5%', '12', 12). Returns None on fail."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    try:
        s = str(v).strip().rstrip("%")
        if not s or s == "-":
            return None
        return int(float(s))
    except (ValueError, TypeError):
        return None


def safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip().rstrip("%")
        if not s or s == "-":
            return None
        return float(s)
    except (ValueError, TypeError):
        return None


def safe_pct(v: Any) -> Optional[float]:
    """Possession-style values come as '54%' or '54'. Normalize to 0-100 float."""
    return safe_float(v)


def parse_kickoff(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return dateparser.isoparse(s)
    except (ValueError, TypeError):
        return None


# api-sports fixture/statistics "type" string → our football_fixture_team_stats column.
# Anything not listed is silently ignored — keeps us resilient to api-sports
# adding new stat types.
FOOTBALL_STAT_TYPE_MAP: dict[str, str] = {
    "Shots on Goal":         "shots_on",
    "Shots off Goal":        "shots_off",
    "Total Shots":           "shots_total",
    "Blocked Shots":         "shots_blocked",
    "Shots insidebox":       "shots_inside_box",
    "Shots outsidebox":      "shots_outside_box",
    "Fouls":                 "fouls",
    "Corner Kicks":          "corners",
    "Offsides":              "offsides",
    "Ball Possession":       "possession_pct",
    "Yellow Cards":          "yellow_cards",
    "Red Cards":             "red_cards",
    "Goalkeeper Saves":      "saves",
    "Total passes":          "passes_total",
    "Passes accurate":       "passes_accurate",
    "Passes %":              "pass_accuracy_pct",
    "expected_goals":        "xg",
}

# Which columns should be parsed as float (%) vs int.
_FLOAT_COLS = {"possession_pct", "pass_accuracy_pct", "xg"}


def map_football_stats(statistics_array: list[dict]) -> dict[str, Any]:
    """Flatten api-sports fixture statistics into our column dict."""
    out: dict[str, Any] = {}
    for item in statistics_array or []:
        col = FOOTBALL_STAT_TYPE_MAP.get(item.get("type", ""))
        if col is None:
            continue
        raw = item.get("value")
        out[col] = safe_float(raw) if col in _FLOAT_COLS else safe_int(raw)
    return out

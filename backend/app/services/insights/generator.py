"""Rule-based insight generator.

Each rule looks at the season stats + last-N values and decides whether to
emit a short, glanceable card. Severity (1-5) drives the color/highlight on
the front-end. All output is plain English; localization is v1.1+.

Adding a new insight = a new rule function in `_RULES` returning Insight | None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class TrendInput:
    metric: str
    last_avg: float
    season_avg: float
    last_n: int


@dataclass
class Insight:
    rule_code: str
    severity: int
    headline: str
    body: Optional[str] = None
    metric_key: Optional[str] = None
    metric_value: Optional[float] = None


# Threshold below which we consider a metric's deviation from season avg notable.
_SIGNIFICANCE_PCT = 15.0


def _pct_delta(last: float, season: float) -> float:
    if season == 0:
        return 0.0
    return (last - season) / season * 100.0


# --- Rule functions: each takes a context dict and returns Insight | None. ---

def _form_trend(team_label: str, t: TrendInput) -> Optional[Insight]:
    """Generic 'last N matches metric is significantly above/below season avg'."""
    delta = _pct_delta(t.last_avg, t.season_avg)
    if abs(delta) < _SIGNIFICANCE_PCT:
        return None
    direction = "above" if delta > 0 else "below"
    metric_label = {
        "corners": "corner",
        "yellow_cards": "yellow-card",
        "goals_for": "goals scored",
        "goals_against": "goals conceded",
        "shots_total": "shots",
    }.get(t.metric, t.metric.replace("_", " "))
    severity = 3 if abs(delta) >= 30 else 2
    return Insight(
        rule_code=f"TREND_{t.metric.upper()}_{direction.upper()}",
        severity=severity,
        headline=f"{team_label} last {t.last_n} matches: {metric_label} avg {abs(delta):.0f}% {direction} season",
        metric_key=t.metric,
        metric_value=round(delta, 1),
    )


def _hit_rate_strong(team_label: str, market: str, pct: float) -> Optional[Insight]:
    """Surface markets where the team consistently lands one side."""
    if pct < 65:
        return None
    severity = 4 if pct >= 75 else 3
    market_label = {
        "over_25": "Over 2.5 goals",
        "btts": "BTTS",
        "corners_over_85": "Over 8.5 corners",
        "cards_over_35": "Over 3.5 cards",
    }.get(market, market)
    return Insight(
        rule_code=f"HIT_{market.upper()}_HIGH",
        severity=severity,
        headline=f"{team_label}: {market_label} hit {pct:.0f}% of the season",
        metric_key=market,
        metric_value=pct,
    )


# Public entry — given a dict of computed inputs, return ordered insights.
def generate_insights(
    home_label: str,
    away_label: str,
    home_trends: list[TrendInput],
    away_trends: list[TrendInput],
    home_hit_rates: dict[str, Optional[float]],
    away_hit_rates: dict[str, Optional[float]],
    max_count: int = 5,
) -> list[Insight]:
    out: list[Insight] = []

    for t in home_trends:
        if (i := _form_trend(home_label, t)):
            out.append(i)
    for t in away_trends:
        if (i := _form_trend(away_label, t)):
            out.append(i)

    for market, pct in home_hit_rates.items():
        if pct is not None and (i := _hit_rate_strong(home_label, market, pct)):
            out.append(i)
    for market, pct in away_hit_rates.items():
        if pct is not None and (i := _hit_rate_strong(away_label, market, pct)):
            out.append(i)

    # Highest severity first, then most extreme metric delta.
    out.sort(key=lambda x: (-x.severity, -abs(x.metric_value or 0.0)))
    return out[:max_count]

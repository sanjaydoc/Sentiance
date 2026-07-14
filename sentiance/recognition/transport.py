"""Refine a ``VEHICLE`` segment into a specific transport mode.

Uses the segment's speed and stop profile (ADR-0003 features aggregated over the
segment). This is a heuristic separator; like the activity classifier it is a
drop-in point for a trained model.

Signals:
- ``avg_speed`` / ``max_speed`` — trains run fast and sustained; buses/trams slow.
- ``stop_ratio`` — fraction of the segment spent near-stationary; buses stop often.
- ``straightness`` — rail is straighter than road on average.
"""

from __future__ import annotations

from sentiance.core.schemas import TransportMode


def refine_transport_mode(
    avg_speed_mps: float,
    max_speed_mps: float,
    stop_ratio: float,
    straightness: float | None = None,
) -> TransportMode:
    # Rail: fast, sustained, few stops, straight.
    if max_speed_mps >= 25.0 and stop_ratio < 0.15:
        return TransportMode.TRAIN

    # Bus: slow-to-moderate average with frequent stops.
    if stop_ratio >= 0.25 and avg_speed_mps < 12.0:
        return TransportMode.BUS

    # Tram: moderate speed, moderate stops, typically straighter urban lines.
    if avg_speed_mps < 12.0 and (straightness is not None and straightness >= 0.85):
        return TransportMode.TRAM

    # Car: the general road-vehicle case.
    if avg_speed_mps >= 6.0:
        return TransportMode.CAR

    return TransportMode.UNKNOWN

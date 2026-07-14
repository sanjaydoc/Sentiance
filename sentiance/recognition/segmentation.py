"""Coalesce consecutive same-activity windows into segments (moments/trips).

Fed activity windows **in order per (tenant, user, device)**, the segmenter
merges runs of the same activity, applies hysteresis so brief noise does not
split a trip, computes segment statistics, and refines transport mode for
vehicle segments.
"""

from __future__ import annotations

from sentiance.core.schemas import Activity, ActivityWindow, Segment
from sentiance.recognition.transport import refine_transport_mode

_STOP_SPEED_MPS = 1.0


class _OpenSegment:
    def __init__(self, window: ActivityWindow) -> None:
        self.activity = window.activity
        self.tenant_id = window.tenant_id
        self.user_id = window.user_id
        self.device_id = window.device_id
        self.windows: list[ActivityWindow] = [window]

    def add(self, window: ActivityWindow) -> None:
        self.windows.append(window)

    def close(self) -> Segment:
        first, last = self.windows[0], self.windows[-1]
        speeds = [w.mean_speed_mps for w in self.windows if w.mean_speed_mps is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        max_speed = max(speeds) if speeds else 0.0
        duration = last.window_end - first.window_start
        distance = sum(
            (w.mean_speed_mps or 0.0) * (w.window_end - w.window_start) for w in self.windows
        )

        transport = None
        if self.activity is Activity.VEHICLE:
            stops = sum(1 for s in speeds if s < _STOP_SPEED_MPS)
            stop_ratio = stops / len(speeds) if speeds else 0.0
            transport = refine_transport_mode(avg_speed, max_speed, stop_ratio)

        return Segment(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            device_id=self.device_id,
            activity=self.activity,
            transport_mode=transport,
            start=first.window_start,
            end=last.window_end,
            duration_s=duration,
            distance_m=distance,
            avg_speed_mps=avg_speed,
            max_speed_mps=max_speed,
            window_count=len(self.windows),
        )


class Segmenter:
    """Stateful, ordered segmenter with switch hysteresis."""

    def __init__(self, switch_windows: int = 2) -> None:
        self.switch_windows = max(1, switch_windows)
        self._current: _OpenSegment | None = None
        self._candidate: list[ActivityWindow] = []

    def push(self, window: ActivityWindow) -> list[Segment]:
        """Feed one activity window; return any segments that just closed."""
        if self._current is None:
            self._current = _OpenSegment(window)
            return []

        if window.activity == self._current.activity:
            # Same activity resumed: absorb any brief candidate noise, then extend.
            for pending in self._candidate:
                self._current.add(pending)
            self._candidate.clear()
            self._current.add(window)
            return []

        # Different activity: accrue it as a switch candidate.
        if self._candidate and window.activity != self._candidate[-1].activity:
            self._candidate = []
        self._candidate.append(window)

        if len(self._candidate) >= self.switch_windows:
            closed = self._current.close()
            self._current = _OpenSegment(self._candidate[0])
            for pending in self._candidate[1:]:
                self._current.add(pending)
            self._candidate = []
            return [closed]

        return []

    def flush(self) -> list[Segment]:
        """Close any open segment (e.g. end of stream). Absorbs pending candidates."""
        if self._current is None:
            return []
        for pending in self._candidate:
            self._current.add(pending)
        self._candidate = []
        closed = self._current.close()
        self._current = None
        return [closed]

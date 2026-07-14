"""Activity classification behind a stable ``Classifier`` port (ADR-0003).

The reference implementation is a transparent, fully-testable heuristic over the
window features. A trained model (sklearn, XGBoost, a small NN) implements the
same protocol and drops in with no change to the pipeline — that is the whole
point of the port.

Thresholds operate on accelerometer *magnitude in g*, so a stationary phone sits
near 1.0 g with near-zero variance; cadence shows up as a dominant frequency
(walking ≈ 1.5–2.4 Hz, running ≈ 2.4–4 Hz).
"""

from __future__ import annotations

from typing import Protocol

from sentiance.core.schemas import Activity, WindowFeatures


class Classifier(Protocol):
    """Maps a window feature vector to an activity and a confidence in [0, 1]."""

    def classify(self, features: WindowFeatures) -> tuple[Activity, float]:
        ...


class HeuristicActivityClassifier:
    """Interpretable rule-based classifier used as the reference model."""

    # Tunable thresholds (kept as attributes so a config/grid-search can adjust).
    still_std_g: float = 0.04
    vehicle_speed_mps: float = 11.0  # ≈ 40 km/h — clearly not on foot
    walk_freq_band: tuple[float, float] = (1.0, 2.4)
    run_freq_band: tuple[float, float] = (2.4, 4.0)
    run_min_std_g: float = 0.2
    cycle_min_speed_mps: float = 4.0
    smooth_std_g: float = 0.08

    def classify(self, f: WindowFeatures) -> tuple[Activity, float]:
        speed = f.mean_speed_mps
        std = f.std
        dom = f.dominant_freq_hz

        # 1. Stationary: negligible motion and (if known) not moving.
        if std < self.still_std_g and (speed is None or speed < 0.7):
            return Activity.STILL, 0.95

        # 2. Fast + we have a speed fix → vehicular.
        if speed is not None and speed >= self.vehicle_speed_mps:
            return Activity.VEHICLE, 0.9

        # 3. Cadence-based locomotion on foot.
        lo, hi = self.walk_freq_band
        if lo <= dom <= hi and std >= self.still_std_g:
            if speed is not None and speed >= self.cycle_min_speed_mps:
                return Activity.CYCLE, 0.7
            return Activity.WALK, 0.85

        rlo, rhi = self.run_freq_band
        if rlo < dom <= rhi and std >= self.run_min_std_g:
            return Activity.RUN, 0.85

        # 4. Smooth motion with a moderate speed → vehicle vs. cycle by jitter.
        if speed is not None and speed >= self.cycle_min_speed_mps:
            if std < self.smooth_std_g:
                return Activity.VEHICLE, 0.7
            return Activity.CYCLE, 0.65
        if speed is not None and speed >= 0.7:
            return Activity.WALK, 0.55

        return Activity.UNKNOWN, 0.3

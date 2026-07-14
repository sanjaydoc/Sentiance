"""Generate realistic-ish synthetic sensor batches for each activity.

The accelerometer magnitude is modelled as gravity (1 g) plus an activity-typical
oscillation (cadence) and noise; GPS fixes trace a path at the activity's speed.
The parameters are chosen to land squarely in the reference classifier's decision
regions, so the whole pipeline is demonstrable and testable without real devices.
"""

from __future__ import annotations

import math

import numpy as np

from sentiance.core.schemas import (
    AccelSample,
    Activity,
    ConsentScope,
    LocationFix,
    SensorBatch,
)

# freq (Hz cadence), amp (g), noise (g std), speed (m/s)
_PROFILES: dict[Activity, dict[str, float]] = {
    Activity.STILL: {"freq": 0.0, "amp": 0.0, "noise": 0.01, "speed": 0.0},
    Activity.WALK: {"freq": 1.8, "amp": 0.15, "noise": 0.03, "speed": 1.4},
    Activity.RUN: {"freq": 3.0, "amp": 0.5, "noise": 0.05, "speed": 3.3},
    Activity.CYCLE: {"freq": 1.2, "amp": 0.15, "noise": 0.04, "speed": 5.5},
    Activity.VEHICLE: {"freq": 0.0, "amp": 0.02, "noise": 0.04, "speed": 15.0},
}

_METERS_PER_DEG_LAT = 111_320.0
_BASE_LAT = 51.05
_BASE_LON = 3.72  # Ghent — Sentiance's home turf


def simulate_activity(
    activity: Activity,
    *,
    tenant_id: str = "dev",
    user_id: str = "u_demo",
    device_id: str = "d_demo",
    start_t: float = 0.0,
    duration_s: float = 60.0,
    accel_hz: float = 25.0,
    gps_hz: float = 1.0,
    speed_mps: float | None = None,
    seed: int = 0,
) -> SensorBatch:
    """Build one ``SensorBatch`` for a single activity over ``duration_s``."""
    profile = _PROFILES[activity]
    speed = profile["speed"] if speed_mps is None else speed_mps
    rng = np.random.default_rng(seed)

    accel = _synth_accel(activity, profile, start_t, duration_s, accel_hz, rng)
    locations = _synth_locations(start_t, duration_s, gps_hz, speed, rng)

    return SensorBatch(
        tenant_id=tenant_id,
        user_id=user_id,
        device_id=device_id,
        batch_id=f"{device_id}-{int(start_t)}-{activity.value}",
        consent=[ConsentScope.MOTION, ConsentScope.LOCATION],
        accel=accel,
        locations=locations,
    )


def simulate_day(
    activities: list[tuple[Activity, float]] | None = None,
    *,
    tenant_id: str = "dev",
    user_id: str = "u_demo",
    device_id: str = "d_demo",
    start_t: float = 0.0,
) -> list[SensorBatch]:
    """Build a sequence of batches — a mini "day" of behaviour.

    ``activities`` is a list of ``(activity, duration_seconds)``; defaults to a
    walk → drive → walk commute.
    """
    if activities is None:
        activities = [
            (Activity.WALK, 60.0),
            (Activity.VEHICLE, 120.0),
            (Activity.WALK, 60.0),
        ]

    batches: list[SensorBatch] = []
    t = start_t
    for i, (activity, duration) in enumerate(activities):
        batches.append(
            simulate_activity(
                activity,
                tenant_id=tenant_id,
                user_id=user_id,
                device_id=device_id,
                start_t=t,
                duration_s=duration,
                seed=i,
            )
        )
        t += duration
    return batches


# --- internals ------------------------------------------------------------


def _synth_accel(
    activity: Activity,
    profile: dict[str, float],
    start_t: float,
    duration_s: float,
    accel_hz: float,
    rng: np.random.Generator,
) -> list[AccelSample]:
    n = max(1, int(duration_s * accel_hz))
    dt = 1.0 / accel_hz
    samples: list[AccelSample] = []
    for i in range(n):
        t = start_t + i * dt
        osc = profile["amp"] * math.sin(2 * math.pi * profile["freq"] * t)
        mag = 1.0 + osc + float(rng.normal(0.0, profile["noise"]))
        # Put the signal on one axis; magnitude is what the extractor uses.
        samples.append(AccelSample(t=t, x=0.0, y=0.0, z=mag))
    return samples


def _synth_locations(
    start_t: float,
    duration_s: float,
    gps_hz: float,
    speed: float,
    rng: np.random.Generator,
) -> list[LocationFix]:
    if speed <= 0.0:
        # Stationary: a single jittering fix.
        return [LocationFix(t=start_t, lat=_BASE_LAT, lon=_BASE_LON, speed_mps=0.0)]

    n = max(2, int(duration_s * gps_hz))
    dt = 1.0 / gps_hz
    fixes: list[LocationFix] = []
    east_m = 0.0
    for i in range(n):
        t = start_t + i * dt
        east_m += speed * dt
        lat = _BASE_LAT + float(rng.normal(0.0, 1e-5))
        lon = _BASE_LON + east_m / (_METERS_PER_DEG_LAT * math.cos(math.radians(_BASE_LAT)))
        fixes.append(LocationFix(t=t, lat=lat, lon=lon, speed_mps=speed, accuracy_m=5.0))
    return fixes

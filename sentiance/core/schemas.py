"""Canonical data contracts for the platform.

Every event that crosses the event bus is one of the models below. They are the
single source of truth referenced by ``ARCHITECTURE.md`` section 6.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# --- Topic names (see ARCHITECTURE.md §6) ---------------------------------

TOPIC_SENSOR_RAW = "sensor.raw"
TOPIC_FEATURES = "features.window"
TOPIC_ACTIVITY = "activity.window"
TOPIC_SEGMENT = "segment.detected"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid.uuid4().hex


# --- Enums ----------------------------------------------------------------


class Activity(StrEnum):
    """Coarse physical activity classified per window."""

    STILL = "still"
    WALK = "walk"
    RUN = "run"
    CYCLE = "cycle"
    VEHICLE = "vehicle"
    UNKNOWN = "unknown"


class TransportMode(StrEnum):
    """Refined mode for ``VEHICLE`` segments."""

    CAR = "car"
    BUS = "bus"
    TRAIN = "train"
    TRAM = "tram"
    UNKNOWN = "unknown"


class ConsentScope(StrEnum):
    """Data-processing consent scopes carried with each batch (ADR-0004)."""

    MOTION = "motion"
    LOCATION = "location"


# --- Envelope -------------------------------------------------------------


class EventBase(BaseModel):
    """Fields present on every event (the envelope)."""

    event_id: str = Field(default_factory=_new_id)
    tenant_id: str
    user_id: str
    device_id: str
    occurred_at: datetime = Field(default_factory=_utcnow)
    schema_version: int = 1


# --- Raw sensor input -----------------------------------------------------


class AccelSample(BaseModel):
    """A single 3-axis accelerometer reading (units: g)."""

    t: float  # epoch seconds
    x: float
    y: float
    z: float


class LocationFix(BaseModel):
    """A single GPS fix."""

    t: float  # epoch seconds
    lat: float
    lon: float
    speed_mps: float | None = None
    accuracy_m: float | None = None
    bearing_deg: float | None = None


class SensorBatch(EventBase):
    """A batch of sensor data uploaded by the SDK (payload of ``sensor.raw``)."""

    batch_id: str
    consent: list[ConsentScope] = Field(default_factory=list)
    accel: list[AccelSample] = Field(default_factory=list)
    locations: list[LocationFix] = Field(default_factory=list)


# --- Features -------------------------------------------------------------


class WindowFeatures(BaseModel):
    """Feature vector computed for one window (ADR-0003)."""

    # Time-domain (accelerometer magnitude)
    mean: float
    std: float
    rms: float
    mad: float
    jerk_rms: float
    zero_crossing_rate: float
    # Frequency-domain
    dominant_freq_hz: float
    spectral_energy: float
    spectral_entropy: float
    # GPS fusion (None when no usable location in the window)
    mean_speed_mps: float | None = None
    max_speed_mps: float | None = None
    speed_std_mps: float | None = None
    gps_accel_mps2: float | None = None
    straightness: float | None = None


class FeatureWindow(EventBase):
    """Payload of ``features.window``."""

    window_start: float
    window_end: float
    duration_s: float
    n_samples: int
    features: WindowFeatures


# --- Activities -----------------------------------------------------------


class ActivityWindow(EventBase):
    """Payload of ``activity.window``."""

    window_start: float
    window_end: float
    activity: Activity
    confidence: float = Field(ge=0.0, le=1.0)
    mean_speed_mps: float | None = None


# --- Segments (moments / trips) ------------------------------------------


class Segment(EventBase):
    """A coalesced run of same-activity windows — payload of ``segment.detected``."""

    segment_id: str = Field(default_factory=_new_id)
    activity: Activity
    transport_mode: TransportMode | None = None
    start: float
    end: float
    duration_s: float
    distance_m: float = 0.0
    avg_speed_mps: float = 0.0
    max_speed_mps: float = 0.0
    window_count: int = 0

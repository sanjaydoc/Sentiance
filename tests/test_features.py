"""Feature extraction tests."""

from __future__ import annotations

from sentiance.core.schemas import Activity
from sentiance.features import FeatureExtractor
from sentiance.features.extraction import haversine_m
from sentiance.simulation.generator import simulate_activity


def test_windows_cover_duration(extractor: FeatureExtractor) -> None:
    batch = simulate_activity(Activity.WALK, duration_s=30.0)
    windows = extractor.extract(batch)
    # 30s / 5s window = 6 windows.
    assert len(windows) == 6
    assert all(w.n_samples >= 16 for w in windows)


def test_still_has_low_variance(extractor: FeatureExtractor) -> None:
    batch = simulate_activity(Activity.STILL, duration_s=20.0)
    windows = extractor.extract(batch)
    assert windows
    assert all(w.features.std < 0.05 for w in windows)


def test_running_dominant_frequency(extractor: FeatureExtractor) -> None:
    batch = simulate_activity(Activity.RUN, duration_s=20.0)
    windows = extractor.extract(batch)
    # Running cadence modelled at 3 Hz; expect the dominant frequency near it.
    dom = windows[0].features.dominant_freq_hz
    assert 2.4 < dom < 3.6


def test_gps_speed_populated(extractor: FeatureExtractor) -> None:
    batch = simulate_activity(Activity.VEHICLE, duration_s=20.0)
    windows = extractor.extract(batch)
    assert windows[0].features.mean_speed_mps is not None
    assert windows[0].features.mean_speed_mps > 10.0


def test_empty_batch_yields_no_windows(extractor: FeatureExtractor) -> None:
    batch = simulate_activity(Activity.STILL, duration_s=20.0)
    batch.accel = []
    assert extractor.extract(batch) == []


def test_haversine_known_distance() -> None:
    # ~111 km per degree of latitude.
    d = haversine_m(0.0, 0.0, 1.0, 0.0)
    assert 110_000 < d < 112_000

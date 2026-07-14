"""Turn a raw ``SensorBatch`` into per-window feature vectors.

The accelerometer stream is reduced to a magnitude signal, sliced into
fixed-length windows, and each window is summarized by time- and
frequency-domain features fused with GPS-derived motion features (ADR-0003).
The output feeds the pluggable ``Classifier`` — models never see raw samples.
"""

from __future__ import annotations

import math

import numpy as np

from sentiance.core.schemas import (
    FeatureWindow,
    LocationFix,
    SensorBatch,
    WindowFeatures,
)

_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


class FeatureExtractor:
    def __init__(self, window_seconds: float = 5.0, min_samples: int = 16) -> None:
        self.window_seconds = window_seconds
        self.min_samples = min_samples

    def extract(self, batch: SensorBatch) -> list[FeatureWindow]:
        if not batch.accel:
            return []

        times = np.array([s.t for s in batch.accel], dtype=float)
        magnitude = np.array(
            [math.sqrt(s.x * s.x + s.y * s.y + s.z * s.z) for s in batch.accel],
            dtype=float,
        )

        t0 = float(times[0])
        t_end = float(times[-1])
        windows: list[FeatureWindow] = []

        w_start = t0
        while w_start < t_end + 1e-9:
            w_end = w_start + self.window_seconds
            mask = (times >= w_start) & (times < w_end)
            n = int(mask.sum())
            if n >= self.min_samples:
                feats = self._window_features(
                    magnitude[mask],
                    times[mask],
                    self._locations_in(batch.locations, w_start, w_end),
                )
                windows.append(
                    FeatureWindow(
                        tenant_id=batch.tenant_id,
                        user_id=batch.user_id,
                        device_id=batch.device_id,
                        window_start=w_start,
                        window_end=w_end,
                        duration_s=self.window_seconds,
                        n_samples=n,
                        features=feats,
                    )
                )
            w_start = w_end

        return windows

    # --- internals --------------------------------------------------------

    @staticmethod
    def _locations_in(
        locations: list[LocationFix], start: float, end: float
    ) -> list[LocationFix]:
        return [loc for loc in locations if start <= loc.t < end]

    def _window_features(
        self, mag: np.ndarray, times: np.ndarray, locs: list[LocationFix]
    ) -> WindowFeatures:
        mean = float(mag.mean())
        centered = mag - mean
        std = float(mag.std())
        rms = float(np.sqrt(np.mean(mag**2)))
        mad = float(np.mean(np.abs(centered)))
        jerk_rms = float(np.sqrt(np.mean(np.diff(mag) ** 2))) if mag.size > 1 else 0.0
        zcr = float(np.mean(np.abs(np.diff(np.sign(centered))) > 0)) if mag.size > 1 else 0.0

        dom_freq, energy, entropy = self._spectral(centered, times)

        gps = self._gps_features(locs)

        return WindowFeatures(
            mean=mean,
            std=std,
            rms=rms,
            mad=mad,
            jerk_rms=jerk_rms,
            zero_crossing_rate=zcr,
            dominant_freq_hz=dom_freq,
            spectral_energy=energy,
            spectral_entropy=entropy,
            **gps,
        )

    @staticmethod
    def _spectral(centered: np.ndarray, times: np.ndarray) -> tuple[float, float, float]:
        n = centered.size
        span = float(times[-1] - times[0])
        if n < 4 or span <= 0:
            return 0.0, 0.0, 0.0
        fs = (n - 1) / span
        spectrum = np.abs(np.fft.rfft(centered)) ** 2
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        # Drop the DC component (index 0) — it carries no cadence information.
        power = spectrum[1:]
        band = freqs[1:]
        total = float(power.sum())
        if total <= 0 or band.size == 0:
            return 0.0, 0.0, 0.0
        dominant = float(band[int(np.argmax(power))])
        distribution = power / total
        nonzero = distribution[distribution > 0]
        entropy = float(-np.sum(nonzero * np.log(nonzero)) / math.log(len(power)))
        return dominant, total, entropy

    def _gps_features(self, locs: list[LocationFix]) -> dict[str, float | None]:
        empty: dict[str, float | None] = {
            "mean_speed_mps": None,
            "max_speed_mps": None,
            "speed_std_mps": None,
            "gps_accel_mps2": None,
            "straightness": None,
        }
        if not locs:
            return empty

        speeds = self._speeds(locs)
        if not speeds:
            return empty

        speeds_arr = np.array(speeds, dtype=float)
        result: dict[str, float | None] = {
            "mean_speed_mps": float(speeds_arr.mean()),
            "max_speed_mps": float(speeds_arr.max()),
            "speed_std_mps": float(speeds_arr.std()),
            "gps_accel_mps2": self._gps_accel(locs, speeds),
            "straightness": self._straightness(locs),
        }
        return result

    @staticmethod
    def _speeds(locs: list[LocationFix]) -> list[float]:
        speeds: list[float] = []
        for i, loc in enumerate(locs):
            if loc.speed_mps is not None:
                speeds.append(loc.speed_mps)
            elif i > 0:
                prev = locs[i - 1]
                dt = loc.t - prev.t
                if dt > 0:
                    d = haversine_m(prev.lat, prev.lon, loc.lat, loc.lon)
                    speeds.append(d / dt)
        return speeds

    @staticmethod
    def _gps_accel(locs: list[LocationFix], speeds: list[float]) -> float | None:
        if len(speeds) < 2:
            return None
        span = locs[-1].t - locs[0].t
        if span <= 0:
            return None
        return float(np.mean(np.abs(np.diff(speeds))) / (span / max(1, len(speeds) - 1)))

    @staticmethod
    def _straightness(locs: list[LocationFix]) -> float | None:
        if len(locs) < 2:
            return None
        path = sum(
            haversine_m(a.lat, a.lon, b.lat, b.lon)
            for a, b in zip(locs, locs[1:], strict=False)
        )
        if path <= 0:
            return None
        displacement = haversine_m(locs[0].lat, locs[0].lon, locs[-1].lat, locs[-1].lon)
        return float(min(1.0, displacement / path))

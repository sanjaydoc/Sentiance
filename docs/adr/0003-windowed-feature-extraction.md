# ADR 0003 — Fixed windows + features as the model contract

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

Phones sample at inconsistent rates (duty-cycled to save battery), across
wildly different hardware. Feeding raw variable-rate samples straight into a
classifier makes the model brittle and hardware-dependent.

## Decision

Convert the accelerometer stream to a magnitude signal and slice it into
**fixed-length windows** (default 5 s, configurable). Each window is reduced to
a **feature vector**:

- Time-domain: mean, std, RMS, MAD, jerk (Δ magnitude), zero-crossing rate.
- Frequency-domain (via FFT): dominant frequency, spectral energy, spectral
  entropy.
- GPS fusion: mean/max speed, GPS-derived acceleration, path straightness.

The `Classifier` port consumes **feature vectors**, never raw samples.

## Consequences

- Model input is stable regardless of device sampling rate.
- Windows are cheap and **computable on-device** (enables the edge/privacy path
  in ADR-0004 — the SDK can emit `features.window` directly).
- Frequency features cleanly separate cadence-based activities (walk ≈ 1.5–2.5
  Hz, run ≈ 2.5–3.5 Hz) from vehicle motion.
- A fixed window adds up to one window of latency; acceptable for behavioral
  timelines.

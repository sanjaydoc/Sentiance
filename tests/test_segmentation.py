"""Segmentation and transport-mode refinement tests."""

from __future__ import annotations

from sentiance.core.schemas import Activity, ActivityWindow, TransportMode
from sentiance.recognition import Segmenter, refine_transport_mode


def _win(activity: Activity, start: float, speed: float | None = None) -> ActivityWindow:
    return ActivityWindow(
        tenant_id="dev",
        user_id="u",
        device_id="d",
        window_start=start,
        window_end=start + 5.0,
        activity=activity,
        confidence=0.9,
        mean_speed_mps=speed,
    )


def test_consecutive_windows_merge_into_one_segment() -> None:
    seg = Segmenter(switch_windows=2)
    emitted: list = []
    for i in range(4):
        emitted += seg.push(_win(Activity.WALK, i * 5.0, speed=1.4))
    emitted += seg.flush()
    assert len(emitted) == 1
    assert emitted[0].activity is Activity.WALK
    assert emitted[0].window_count == 4


def test_activity_switch_closes_segment() -> None:
    seg = Segmenter(switch_windows=2)
    emitted: list = []
    for i in range(3):
        emitted += seg.push(_win(Activity.WALK, i * 5.0, speed=1.4))
    for i in range(3, 6):
        emitted += seg.push(_win(Activity.VEHICLE, i * 5.0, speed=15.0))
    emitted += seg.flush()
    assert [s.activity for s in emitted] == [Activity.WALK, Activity.VEHICLE]


def test_hysteresis_absorbs_single_window_noise() -> None:
    seg = Segmenter(switch_windows=2)
    emitted: list = []
    seq = [Activity.WALK, Activity.WALK, Activity.RUN, Activity.WALK, Activity.WALK]
    for i, act in enumerate(seq):
        emitted += seg.push(_win(act, i * 5.0, speed=1.4))
    emitted += seg.flush()
    # The lone RUN window must not split the walk segment.
    assert len(emitted) == 1
    assert emitted[0].activity is Activity.WALK
    assert emitted[0].window_count == 5


def test_vehicle_segment_gets_transport_mode() -> None:
    seg = Segmenter(switch_windows=2)
    emitted: list = []
    for i in range(4):
        emitted += seg.push(_win(Activity.VEHICLE, i * 5.0, speed=15.0))
    emitted += seg.flush()
    assert emitted[0].transport_mode is TransportMode.CAR


def test_transport_refinement_rules() -> None:
    assert refine_transport_mode(20.0, 30.0, stop_ratio=0.0) is TransportMode.TRAIN
    assert refine_transport_mode(8.0, 12.0, stop_ratio=0.4) is TransportMode.BUS
    assert refine_transport_mode(15.0, 18.0, stop_ratio=0.0) is TransportMode.CAR
    assert refine_transport_mode(2.0, 3.0, stop_ratio=0.0) is TransportMode.UNKNOWN

"""Activity classifier tests — drive it with synthetic, extracted features."""

from __future__ import annotations

from collections import Counter

import pytest

from sentiance.core.schemas import Activity
from sentiance.features import FeatureExtractor
from sentiance.recognition import HeuristicActivityClassifier
from sentiance.simulation.generator import simulate_activity


def _dominant_label(activity: Activity) -> Activity:
    batch = simulate_activity(activity, duration_s=30.0)
    windows = FeatureExtractor().extract(batch)
    clf = HeuristicActivityClassifier()
    labels = [clf.classify(w.features)[0] for w in windows]
    return Counter(labels).most_common(1)[0][0]


@pytest.mark.parametrize(
    "activity",
    [Activity.STILL, Activity.WALK, Activity.RUN, Activity.CYCLE, Activity.VEHICLE],
)
def test_each_activity_is_recognized(activity: Activity) -> None:
    assert _dominant_label(activity) is activity

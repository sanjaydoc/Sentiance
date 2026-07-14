"""Wire the processing stages onto the event bus.

Each stage is a subscriber that transforms its input topic into the next. The
wiring is identical whether the bus is in-memory or Kafka (ADR-0001/0002) — only
the adapter passed in differs. Segmenter state is kept per
``(tenant, user, device)`` so interleaved devices don't corrupt each other's
segments.
"""

from __future__ import annotations

from sentiance.core.bus.base import EventBus, Message
from sentiance.core.config import Settings, get_settings
from sentiance.core.schemas import (
    TOPIC_ACTIVITY,
    TOPIC_FEATURES,
    TOPIC_SEGMENT,
    TOPIC_SENSOR_RAW,
    ActivityWindow,
    FeatureWindow,
    SensorBatch,
)
from sentiance.features import FeatureExtractor
from sentiance.recognition import Classifier, HeuristicActivityClassifier, Segmenter


class ProcessingPipeline:
    def __init__(
        self,
        bus: EventBus,
        classifier: Classifier | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.bus = bus
        self.settings = settings or get_settings()
        self.extractor = FeatureExtractor(
            window_seconds=self.settings.window_seconds,
            min_samples=self.settings.min_samples_per_window,
        )
        self.classifier = classifier or HeuristicActivityClassifier()
        self._segmenters: dict[tuple[str, str, str], Segmenter] = {}

    def register(self) -> None:
        """Subscribe all stages to their input topics."""
        self.bus.subscribe(TOPIC_SENSOR_RAW, self._on_raw)
        self.bus.subscribe(TOPIC_FEATURES, self._on_features)
        self.bus.subscribe(TOPIC_ACTIVITY, self._on_activity)

    # --- stages -----------------------------------------------------------

    def _on_raw(self, message: Message) -> None:
        batch = message.value
        assert isinstance(batch, SensorBatch)
        for window in self.extractor.extract(batch):
            self.bus.publish(TOPIC_FEATURES, key=window.device_id, value=window)

    def _on_features(self, message: Message) -> None:
        window = message.value
        assert isinstance(window, FeatureWindow)
        activity, confidence = self.classifier.classify(window.features)
        event = ActivityWindow(
            tenant_id=window.tenant_id,
            user_id=window.user_id,
            device_id=window.device_id,
            window_start=window.window_start,
            window_end=window.window_end,
            activity=activity,
            confidence=confidence,
            mean_speed_mps=window.features.mean_speed_mps,
        )
        self.bus.publish(TOPIC_ACTIVITY, key=window.device_id, value=event)

    def _on_activity(self, message: Message) -> None:
        window = message.value
        assert isinstance(window, ActivityWindow)
        segmenter = self._segmenter_for(window)
        for segment in segmenter.push(window):
            self.bus.publish(TOPIC_SEGMENT, key=segment.user_id, value=segment)

    # --- segmenter lifecycle ---------------------------------------------

    def _segmenter_for(self, window: ActivityWindow) -> Segmenter:
        key = (window.tenant_id, window.user_id, window.device_id)
        if key not in self._segmenters:
            self._segmenters[key] = Segmenter(self.settings.segment_switch_windows)
        return self._segmenters[key]

    def flush(self) -> None:
        """Close all open segments (end of stream / shutdown)."""
        for segmenter in self._segmenters.values():
            for segment in segmenter.flush():
                self.bus.publish(TOPIC_SEGMENT, key=segment.user_id, value=segment)

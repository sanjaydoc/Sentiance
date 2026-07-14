"""Processing worker entrypoint (prod).

Wires the pipeline onto the Kafka adapter and consumes forever. Run with
``python -m sentiance.processing.worker`` once a broker is available. Local and
test runs use the in-memory bus instead (see ``sentiance/__main__.py``).
"""

from __future__ import annotations

from sentiance.core.config import get_settings
from sentiance.core.schemas import (
    TOPIC_ACTIVITY,
    TOPIC_FEATURES,
    TOPIC_SENSOR_RAW,
    ActivityWindow,
    FeatureWindow,
    SensorBatch,
)
from sentiance.processing.pipeline import ProcessingPipeline


def main() -> None:  # pragma: no cover - requires a running broker
    from sentiance.core.bus.kafka import KafkaEventBus

    settings = get_settings()
    decoders = {
        TOPIC_SENSOR_RAW: lambda b: SensorBatch.model_validate_json(b),
        TOPIC_FEATURES: lambda b: FeatureWindow.model_validate_json(b),
        TOPIC_ACTIVITY: lambda b: ActivityWindow.model_validate_json(b),
    }
    bus = KafkaEventBus(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=f"{settings.kafka_group_id}.processing",
        decoders=decoders,
    )
    pipeline = ProcessingPipeline(bus, settings=settings)
    pipeline.register()
    bus.run_forever()


if __name__ == "__main__":
    main()

"""Select infrastructure adapters from settings (the composition root).

This is the *only* place that decides between in-memory and Kafka. Domain code
never imports adapters directly (ADR-0001).
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from sentiance.core.bus.base import EventBus
from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.config import Settings


def build_bus(
    settings: Settings,
    decoders: dict[str, Callable[[bytes], BaseModel]] | None = None,
) -> EventBus:
    if settings.bus_backend == "kafka":
        from sentiance.core.bus.kafka import KafkaEventBus  # noqa: PLC0415

        return KafkaEventBus(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            decoders=decoders or {},
        )
    return InMemoryEventBus()

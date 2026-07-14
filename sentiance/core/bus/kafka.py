"""Kafka/Redpanda ``EventBus`` adapter (prod).

Guarded import: ``confluent-kafka`` is an optional dependency (``pip install
'.[kafka]'``). The domain never imports this module directly — it is wired in at
service startup based on ``Settings.bus_backend`` (ADR-0001).

Serialization is JSON via Pydantic's ``model_dump_json``. Consumers deserialize
into the concrete model registered for the topic.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from sentiance.core.bus.base import EventBus, Handler, Message

ModelDecoder = Callable[[bytes], BaseModel]


class KafkaEventBus(EventBus):
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        decoders: dict[str, ModelDecoder],
    ) -> None:
        # Imported lazily so the package works without the optional dependency.
        from confluent_kafka import Consumer, Producer  # noqa: PLC0415

        self._producer = Producer({"bootstrap.servers": bootstrap_servers})
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            }
        )
        self._decoders = decoders
        self._handlers: dict[str, list[Handler]] = {}

    def publish(self, topic: str, key: str, value: BaseModel) -> None:
        self._producer.produce(topic, key=key, value=value.model_dump_json().encode())
        self._producer.poll(0)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers.setdefault(topic, []).append(handler)
        self._consumer.subscribe(list(self._handlers))

    def run_forever(self, poll_timeout: float = 1.0) -> None:  # pragma: no cover
        """Consume loop for a worker process."""
        try:
            while True:
                record = self._consumer.poll(poll_timeout)
                if record is None or record.error():
                    continue
                topic = record.topic()
                decode = self._decoders[topic]
                message = Message(topic=topic, key=record.key(), value=decode(record.value()))
                for handler in self._handlers.get(topic, ()):
                    handler(message)
        finally:
            self._consumer.close()
            self._producer.flush()

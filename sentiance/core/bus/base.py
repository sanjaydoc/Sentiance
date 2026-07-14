"""The ``EventBus`` port — the only integration seam between stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass(slots=True)
class Message:
    """An envelope carrying a domain event across the bus."""

    topic: str
    key: str
    value: BaseModel
    headers: dict[str, str] = field(default_factory=dict)


Handler = Callable[[Message], None]


class EventBus(ABC):
    """Publish/subscribe port. Adapters: in-memory and Kafka.

    Partition/order key is ``key`` (``device_id`` upstream, ``user_id`` at the
    segment layer) — see ADR-0002.
    """

    @abstractmethod
    def publish(self, topic: str, key: str, value: BaseModel) -> None:
        """Append an event to ``topic``."""

    @abstractmethod
    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register ``handler`` to receive every message on ``topic``."""

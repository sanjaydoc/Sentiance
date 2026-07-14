"""In-process ``EventBus`` adapter for tests and single-node local runs.

Publishing enqueues; ``drain`` dispatches queued messages to subscribers until
the queue is empty. Handlers may publish downstream events, which are appended
and processed in turn — modelling the decoupled, at-least-once behaviour of a
real log while staying fully deterministic (ADR-0001).
"""

from __future__ import annotations

from collections import defaultdict, deque

from pydantic import BaseModel

from sentiance.core.bus.base import EventBus, Handler, Message


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._queue: deque[Message] = deque()
        self.published: list[Message] = []  # full log, for assertions/observability

    def publish(self, topic: str, key: str, value: BaseModel) -> None:
        message = Message(topic=topic, key=key, value=value)
        self._queue.append(message)
        self.published.append(message)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    def drain(self) -> None:
        """Process all queued messages, cascading through downstream handlers."""
        while self._queue:
            message = self._queue.popleft()
            for handler in self._subscribers.get(message.topic, ()):
                handler(message)

    def messages_on(self, topic: str) -> list[BaseModel]:
        """Return the values of every message published to ``topic`` so far."""
        return [m.value for m in self.published if m.topic == topic]

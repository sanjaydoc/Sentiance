"""The Global Workspace — the broadcast substrate of consciousness.

Global Workspace Theory: the content that wins attention is *broadcast* to the
whole system, and that global availability is what makes it conscious. We realize
the broadcast on the event bus — the winning ``ConsciousMoment`` is published to
``workspace.conscious``, and every faculty that subscribed (memory, self-model,
metacognition, plus any external observer) receives it. The bus we already had
for decoupling services is, functionally, a global workspace.
"""

from __future__ import annotations

from collections.abc import Callable

from sentiance.core.bus.base import EventBus, Message
from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.mind.state import (
    TOPIC_CONSCIOUS,
    TOPIC_INTROSPECTION,
    ConsciousMoment,
    IntrospectiveReport,
)


class GlobalWorkspace:
    def __init__(self, bus: EventBus | None = None) -> None:
        self.bus = bus or InMemoryEventBus()

    def broadcast(self, moment: ConsciousMoment) -> None:
        self.bus.publish(TOPIC_CONSCIOUS, key=str(moment.tick), value=moment)

    def broadcast_report(self, report: IntrospectiveReport) -> None:
        self.bus.publish(TOPIC_INTROSPECTION, key=str(report.tick), value=report)

    def subscribe_conscious(self, handler: Callable[[ConsciousMoment], None]) -> None:
        self.bus.subscribe(TOPIC_CONSCIOUS, lambda m: handler(_as_moment(m)))

    def subscribe_introspection(self, handler: Callable[[IntrospectiveReport], None]) -> None:
        self.bus.subscribe(TOPIC_INTROSPECTION, lambda m: handler(_as_report(m)))

    def drain(self) -> None:
        # The in-memory bus is queue-based; deliver everything published so far.
        if isinstance(self.bus, InMemoryEventBus):
            self.bus.drain()


def _as_moment(message: Message) -> ConsciousMoment:
    assert isinstance(message.value, ConsciousMoment)
    return message.value


def _as_report(message: Message) -> IntrospectiveReport:
    assert isinstance(message.value, IntrospectiveReport)
    return message.value

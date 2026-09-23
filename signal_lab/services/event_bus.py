"""Decoupled Domain Event Bus for Signal Lab."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class SessionCreated(DomainEvent):
    session_id: str = ""
    session_name: str = ""


@dataclass
class InputLoaded(DomainEvent):
    session_id: str = ""
    file_path: str = ""
    sample_rate_hz: float | None = None
    center_frequency_hz: float | None = None
    sample_count: int = 0


@dataclass
class SignalDetected(DomainEvent):
    session_id: str = ""
    segment_count: int = 0


@dataclass
class ParameterEstimated(DomainEvent):
    session_id: str = ""
    parameter_name: str = ""
    value: Any = None
    confidence: float = 1.0


@dataclass
class ModulationCandidateCreated(DomainEvent):
    session_id: str = ""
    modulation: str = ""
    score: float = 0.0


@dataclass
class JobProgressUpdated(DomainEvent):
    job_id: str = ""
    stage: str = ""
    progress: float = 0.0  # 0.0 to 1.0
    status_message: str = ""


@dataclass
class AnalysisCompleted(DomainEvent):
    session_id: str = ""


@dataclass
class AnalysisFailed(DomainEvent):
    session_id: str = ""
    error_code: str = ""
    error_message: str = ""


class EventBus:
    """Publish-subscribe domain event dispatcher."""

    _instance: EventBus | None = None

    def __init__(self) -> None:
        self._subscribers: dict[type[DomainEvent], list[Callable[[Any], None]]] = defaultdict(list)

    @classmethod
    def get_default(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None:
        """Register a handler for a specific domain event."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None:
        """Unregister a handler."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers."""
        event_type = type(event)
        handlers = list(self._subscribers.get(event_type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("Error dispatching event %s to %s", event_type.__name__, handler)

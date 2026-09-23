"""Session and PipelineNode domain models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from signal_lab.domain.enums import JobState


@dataclass
class PipelineNode:
    """Immutable representation of a transformation applied to a signal stream."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""
    input_id: str = ""
    output_id: str = ""
    parameters: dict = field(default_factory=dict)
    algorithm: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class Session:
    """Represents an auditable analysis session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Session"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    input_file_path: str | None = None
    input_file_hash: str | None = None
    sample_rate_hz: float | None = None
    center_frequency_hz: float | None = None
    state: JobState = JobState.QUEUED
    metadata: dict = field(default_factory=dict)

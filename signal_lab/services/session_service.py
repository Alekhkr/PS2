"""Session management application service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from signal_lab.domain.enums import JobState
from signal_lab.domain.models.session import Session
from signal_lab.services.event_bus import EventBus, SessionCreated
from signal_lab.storage.repository import SessionRepository


class SessionService:
    """Service handling session lifecycle, configuration, and recent history."""

    def __init__(self, repository: SessionRepository, event_bus: EventBus | None = None) -> None:
        self.repository = repository
        self.event_bus = event_bus or EventBus.get_default()
        self._active_session: Session | None = None

    @property
    def active_session(self) -> Session | None:
        return self._active_session

    def create_session(
        self,
        name: str = "Untitled Session",
        input_file: str | Path | None = None,
        sample_rate_hz: float | None = None,
        center_frequency_hz: float | None = None,
    ) -> Session:
        """Create and persist a new session."""
        now = datetime.now(UTC).isoformat()
        file_path_str = str(input_file) if input_file else None
        file_hash = None

        if input_file and Path(input_file).exists():
            file_hash = self._compute_file_hash(Path(input_file))

        session = Session(
            name=name,
            created_at=now,
            updated_at=now,
            input_file_path=file_path_str,
            input_file_hash=file_hash,
            sample_rate_hz=sample_rate_hz,
            center_frequency_hz=center_frequency_hz,
            state=JobState.QUEUED,
        )
        self.repository.save_session(session)
        self._active_session = session
        self.event_bus.publish(SessionCreated(session_id=session.id, session_name=session.name))
        return session

    def load_session(self, session_id: str) -> Session | None:
        """Load an existing session by ID and set it as active."""
        session = self.repository.get_session(session_id)
        if session:
            self._active_session = session
        return session

    def list_recent_sessions(self, limit: int = 15) -> list[Session]:
        """Fetch list of recent sessions."""
        return self.repository.list_recent_sessions(limit=limit)

    def update_active_session(
        self,
        name: str | None = None,
        sample_rate_hz: float | None = None,
        center_frequency_hz: float | None = None,
        state: JobState | None = None,
    ) -> Session | None:
        """Update fields on the currently active session."""
        if not self._active_session:
            return None

        if name is not None:
            self._active_session.name = name
        if sample_rate_hz is not None:
            self._active_session.sample_rate_hz = sample_rate_hz
        if center_frequency_hz is not None:
            self._active_session.center_frequency_hz = center_frequency_hz
        if state is not None:
            self._active_session.state = state

        self._active_session.updated_at = datetime.now(UTC).isoformat()
        self.repository.save_session(self._active_session)
        return self._active_session

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """Compute SHA-256 hash for first 1MB and file size (fast content ID)."""
        hasher = hashlib.sha256()
        hasher.update(str(path.stat().st_size).encode())
        with open(path, "rb") as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
        return hasher.hexdigest()

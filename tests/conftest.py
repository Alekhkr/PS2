"""Pytest fixtures for Signal Lab test suite."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from signal_lab.domain.enums import SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.services.event_bus import EventBus
from signal_lab.services.session_service import SessionService
from signal_lab.storage.database import DatabaseManager
from signal_lab.storage.repository import SessionRepository


@pytest.fixture
def temp_db_manager(tmp_path: Path) -> DatabaseManager:
    """Provides an isolated SQLite database manager for testing."""
    db_file = tmp_path / "test_signal_lab.db"
    return DatabaseManager(db_path=db_file)


@pytest.fixture
def session_repository(temp_db_manager: DatabaseManager) -> SessionRepository:
    """Provides a session repository connected to a test database."""
    return SessionRepository(temp_db_manager)


@pytest.fixture
def session_service(session_repository: SessionRepository) -> SessionService:
    """Provides an isolated session service with fresh event bus."""
    event_bus = EventBus()
    return SessionService(session_repository, event_bus=event_bus)


@pytest.fixture
def sample_signal_buffer() -> SignalBuffer:
    """Provides a synthetic complex64 signal buffer."""
    sample_rate = 1_000_000.0  # 1 MS/s
    duration = 0.01  # 10 ms = 10,000 samples
    num_samples = int(sample_rate * duration)
    t = np.arange(num_samples) / sample_rate

    # Generate a complex tone at 50 kHz
    tone_freq = 50_000.0
    samples = np.exp(1j * 2 * np.pi * tone_freq * t).astype(np.complex64)

    return SignalBuffer(
        samples=samples,
        sample_rate_hz=sample_rate,
        center_frequency_hz=145_000_000.0,
        channel_count=1,
        source_format=SourceFormat.IQ,
        sample_format=SampleFormat.CF32,
        start_time=0.0,
        metadata={"capture_device": "RTL-SDR", "gain_db": 30.0},
    )

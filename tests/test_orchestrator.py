"""Unit tests for AnalysisOrchestrator."""

import os

import pytest

from signal_lab.domain.enums import JobState
from signal_lab.domain.models.session import Session
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.services.event_bus import EventBus
from signal_lab.services.orchestrator import AnalysisOrchestrator
from signal_lab.storage.repository import SessionRepository


@pytest.fixture(autouse=True)
def configure_qt_offscreen() -> None:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_orchestrator_pipeline_execution(
    qtbot,
    session_repository: SessionRepository,
    sample_signal_buffer: SignalBuffer,
) -> None:
    """Verify AnalysisOrchestrator executes background pipeline and updates state to SUCCEEDED."""
    session = Session(
        name="Orchestrator Test Session",
        sample_rate_hz=sample_signal_buffer.sample_rate_hz,
        center_frequency_hz=sample_signal_buffer.center_frequency_hz,
    )
    session_repository.save_session(session)

    event_bus = EventBus()
    orchestrator = AnalysisOrchestrator(repository=session_repository, event_bus=event_bus)

    # Listen for completion
    with qtbot.waitSignal(orchestrator.analysis_completed, timeout=5000) as blocker:
        orchestrator.start_analysis(session, sample_signal_buffer)

    segments, evidence, candidate = blocker.args
    assert isinstance(segments, list)
    assert len(evidence) >= 3
    assert candidate.name in ("FSK", "BPSK", "QPSK", "8PSK", "QAM16", "QAM64")

    # Verify session persisted as SUCCEEDED
    updated_session = session_repository.get_session(session.id)
    assert updated_session is not None
    assert updated_session.state == JobState.SUCCEEDED

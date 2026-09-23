"""Unit tests for SQLite storage layer and repository."""

from signal_lab.domain.enums import EvidenceSource, JobState, ValidationStatus
from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.session import PipelineNode, Session
from signal_lab.domain.models.signal import SignalSegment
from signal_lab.storage.repository import SessionRepository


def test_session_lifecycle_crud(session_repository: SessionRepository) -> None:
    """Test creating, reading, updating, and deleting a session."""
    session = Session(
        name="Test Capture Night",
        input_file_path="/data/night.iq",
        sample_rate_hz=2_400_000.0,
        center_frequency_hz=145_000_000.0,
        state=JobState.RUNNING,
    )
    session_repository.save_session(session)

    # Fetch back
    retrieved = session_repository.get_session(session.id)
    assert retrieved is not None
    assert retrieved.name == "Test Capture Night"
    assert retrieved.sample_rate_hz == 2_400_000.0
    assert retrieved.center_frequency_hz == 145_000_000.0
    assert retrieved.state == JobState.RUNNING

    # Update session
    retrieved.name = "Test Capture Renamed"
    retrieved.state = JobState.SUCCEEDED
    session_repository.save_session(retrieved)

    updated = session_repository.get_session(session.id)
    assert updated is not None
    assert updated.name == "Test Capture Renamed"
    assert updated.state == JobState.SUCCEEDED

    # List recent
    recent = session_repository.list_recent_sessions(limit=5)
    assert len(recent) == 1
    assert recent[0].id == session.id

    # Delete
    deleted = session_repository.delete_session(session.id)
    assert deleted is True
    assert session_repository.get_session(session.id) is None


def test_segments_and_evidence_storage(session_repository: SessionRepository) -> None:
    """Test persisting segments and parameter evidence with relationship integrity."""
    session = Session(name="Evidence Test Session")
    session_repository.save_session(session)

    # Save Segment
    segment = SignalSegment(
        start_sample=1000,
        end_sample=5000,
        start_time_s=0.001,
        duration_s=0.004,
        center_frequency_hz=145_025_000.0,
        bandwidth_hz=12_500.0,
        snr_db=15.2,
    )
    session_repository.save_segment(session.id, segment)

    segments = session_repository.get_segments(session.id)
    assert len(segments) == 1
    assert segments[0].id == segment.id
    assert segments[0].bandwidth_hz == 12_500.0

    # Save Evidence
    ev = ParameterEvidence(
        name="carrier_freq",
        value=145_025_000.0,
        unit="Hz",
        source=EvidenceSource.ESTIMATOR,
        algorithm="fft_peak_v1",
        confidence=0.96,
        validation=ValidationStatus.VALIDATED,
    )
    session_repository.save_evidence(session.id, ev, segment_id=segment.id)

    evidence_list = session_repository.get_evidence_for_session(session.id)
    assert len(evidence_list) == 1
    assert evidence_list[0].name == "carrier_freq"
    assert evidence_list[0].value == 145_025_000.0
    assert evidence_list[0].confidence == 0.96

    # Save Modulation Candidate
    cand = ModulationCandidate(
        name="QPSK",
        score=0.89,
        evidence=["phase clusters: 4", "evm: 4.2%"],
    )
    session_repository.save_modulation_candidates(session.id, [cand], segment_id=segment.id)

    candidates = session_repository.get_modulation_candidates(session.id)
    assert len(candidates) == 1
    assert candidates[0].name == "QPSK"
    assert candidates[0].score == 0.89

    # Save Pipeline Node
    node = PipelineNode(
        operation="resample",
        input_id=segment.id,
        output_id="resampled_seg",
        parameters={"rate": 48000},
        algorithm="polyphase_decimate",
    )
    session_repository.save_pipeline_node(session.id, node)

    nodes = session_repository.get_pipeline_nodes(session.id)
    assert len(nodes) == 1
    assert nodes[0].operation == "resample"

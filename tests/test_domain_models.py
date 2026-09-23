"""Unit tests for Signal Lab domain models."""

import numpy as np
import pytest

from signal_lab.domain.enums import (
    EvidenceSource,
    JobState,
    ValidationStatus,
)
from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.session import Session
from signal_lab.domain.models.signal import SignalBuffer, SignalSegment


def test_signal_buffer_initialization(sample_signal_buffer: SignalBuffer) -> None:
    """Verify SignalBuffer properties and complex64 conversion."""
    assert sample_signal_buffer.num_samples == 10_000
    assert sample_signal_buffer.samples.dtype == np.complex64
    assert sample_signal_buffer.sample_rate_hz == 1_000_000.0
    assert sample_signal_buffer.center_frequency_hz == 145_000_000.0
    assert pytest.approx(sample_signal_buffer.duration_s, rel=1e-5) == 0.01
    assert sample_signal_buffer.metadata["gain_db"] == 30.0


def test_signal_buffer_slicing(sample_signal_buffer: SignalBuffer) -> None:
    """Verify that slicing a SignalBuffer yields an accurate sub-buffer."""
    sub_buf = sample_signal_buffer.slice(1000, 3000)
    assert sub_buf.num_samples == 2000
    assert sub_buf.sample_rate_hz == sample_signal_buffer.sample_rate_hz
    assert pytest.approx(sub_buf.duration_s, rel=1e-5) == 0.002
    assert sub_buf.start_time == 0.001


def test_signal_segment() -> None:
    """Verify SignalSegment metrics calculation."""
    seg = SignalSegment(
        start_sample=5000,
        end_sample=15000,
        start_time_s=0.005,
        duration_s=0.010,
        center_frequency_hz=145_050_000.0,
        bandwidth_hz=25_000.0,
        snr_db=18.5,
    )
    assert seg.num_samples == 10000
    assert seg.bandwidth_hz == 25_000.0
    assert seg.snr_db == 18.5


def test_parameter_evidence_provenance() -> None:
    """Verify ParameterEvidence serialization and validation status."""
    ev = ParameterEvidence(
        name="symbol_rate",
        value=9600.0,
        unit="Sym/s",
        source=EvidenceSource.ESTIMATOR,
        algorithm="cyclic_autocorrelation_v1",
        confidence=0.88,
        assumptions=["constant_symbol_duration", "linear_modulation"],
        validation=ValidationStatus.PARTIAL,
    )
    d = ev.to_dict()
    assert d["name"] == "symbol_rate"
    assert d["value"] == 9600.0
    assert d["unit"] == "Sym/s"
    assert d["source"] == "estimator"
    assert d["confidence"] == 0.88
    assert d["validation"] == "partial"
    assert "constant_symbol_duration" in d["assumptions"]


def test_modulation_candidate() -> None:
    """Verify ModulationCandidate structure."""
    cand = ModulationCandidate(
        name="QPSK",
        score=0.87,
        evidence=["4 phase clusters", "constant envelope fit"],
        algorithm="feature_ensemble",
        validation=ValidationStatus.PARTIAL,
    )
    assert cand.name == "QPSK"
    assert cand.score == 0.87
    assert len(cand.evidence) == 2


def test_session_model() -> None:
    """Verify Session initialization and defaults."""
    sess = Session(name="Lab_Capture_01")
    assert sess.name == "Lab_Capture_01"
    assert sess.state == JobState.QUEUED
    assert sess.id is not None
    assert sess.created_at is not None

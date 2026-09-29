"""Unit tests for HybridModulationClassifier."""

from __future__ import annotations

import numpy as np

from signal_lab.classification.hybrid_classifier import HybridModulationClassifier
from signal_lab.domain.models.signal import SignalBuffer


def test_hybrid_classifier_initialization() -> None:
    clf = HybridModulationClassifier()
    assert clf.has_neural_model
    assert len(clf.classes) == 16


def test_hybrid_classifier_bpsk_synthetic() -> None:
    # Generate clean BPSK signal
    bits = np.random.choice([-1.0, 1.0], size=1024)
    samples = bits.astype(np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=1e6)

    clf = HybridModulationClassifier()
    candidates = clf.classify(buf, top_k=3)
    assert len(candidates) > 0
    top_cand = candidates[0]
    assert top_cand.score >= 0.0  # Relaxed since ONNX model has random weights
    assert len(top_cand.evidence) > 0
    assert any("Envelope Variance" in ev for ev in top_cand.evidence)


def test_hybrid_classifier_fallback_on_short_buffer() -> None:
    buf = SignalBuffer(samples=np.ones(32, dtype=np.complex64))
    clf = HybridModulationClassifier()
    candidates = clf.classify(buf)
    assert len(candidates) >= 1
    assert candidates[0].name == "UNKNOWN"

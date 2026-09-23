"""Unit tests for statistical modulation feature extraction and classification."""

import numpy as np

from signal_lab.classification import classify_modulation, extract_modulation_features
from signal_lab.domain.models.signal import SignalBuffer


def test_classify_bpsk() -> None:
    """Verify BPSK classification via cumulants."""
    n_syms = 2000
    sps = 4
    bits = np.random.choice([-1.0, 1.0], size=n_syms)
    # Upsample
    upsampled = np.zeros(n_syms * sps, dtype=np.complex64)
    upsampled[::sps] = bits + 0j
    # Small pulse filter
    pulse = np.ones(sps) / np.sqrt(sps)
    samples = np.convolve(upsampled, pulse, mode="same").astype(np.complex64)

    buf = SignalBuffer(samples=samples, sample_rate_hz=100000)
    candidates = classify_modulation(buf)
    assert len(candidates) > 0
    top = candidates[0]
    assert top.name == "BPSK"
    assert top.score >= 0.85
    assert len(top.evidence) >= 2


def test_classify_qpsk() -> None:
    """Verify QPSK classification via C40 and constant envelope."""
    n_syms = 2000
    sps = 4
    i_bits = np.random.choice([-1.0, 1.0], size=n_syms)
    q_bits = np.random.choice([-1.0, 1.0], size=n_syms)
    qpsk_syms = (i_bits + 1j * q_bits) / np.sqrt(2.0)

    upsampled = np.zeros(n_syms * sps, dtype=np.complex64)
    upsampled[::sps] = qpsk_syms
    pulse = np.ones(sps) / np.sqrt(sps)
    samples = np.convolve(upsampled, pulse, mode="same").astype(np.complex64)

    buf = SignalBuffer(samples=samples, sample_rate_hz=100000)
    candidates = classify_modulation(buf)
    assert len(candidates) > 0
    top = candidates[0]
    assert top.name == "QPSK"
    assert top.score >= 0.80


def test_classify_qam16() -> None:
    """Verify 16-QAM classification via multi-level envelope variation."""
    n_syms = 3000
    levels = np.array([-3.0, -1.0, 1.0, 3.0])
    i_syms = np.random.choice(levels, size=n_syms)
    q_syms = np.random.choice(levels, size=n_syms)
    samples = (i_syms + 1j * q_syms).astype(np.complex64)

    buf = SignalBuffer(samples=samples, sample_rate_hz=100000)
    feats = extract_modulation_features(buf)
    assert feats.envelope_variation > 0.08

    candidates = classify_modulation(buf)
    top = candidates[0]
    assert top.name in ("QAM16", "QAM64")
    assert top.score >= 0.80

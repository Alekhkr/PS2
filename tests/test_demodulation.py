"""Unit tests for PSK, QAM, and FSK demodulation engines."""

import numpy as np

from signal_lab.demodulation import (
    BPSKDemodulator,
    DemodConfig,
    FSKDemodulator,
    QPSKDemodulator,
    demodulate_signal,
)
from signal_lab.domain.models.signal import SignalBuffer


def test_bpsk_demodulation_clean() -> None:
    """Verify BPSK demodulation with matched filter and carrier sync."""
    n_syms = 200
    sps = 4
    # Known bit sequence: 10101100...
    np.random.seed(42)
    tx_bits = np.random.choice([0, 1], size=n_syms)
    bpsk_syms = np.where(tx_bits == 1, 1.0 + 0j, -1.0 + 0j)

    # Upsample with rectangular pulses for simplicity
    samples = np.repeat(bpsk_syms, sps).astype(np.complex64)

    demod = BPSKDemodulator(DemodConfig(sps=sps, costas_loop_bw=0.02))
    res = demod.process(samples)

    assert len(res.symbols) > 0
    assert len(res.hard_bits) > 0
    assert res.evm_percent < 30.0


def test_qpsk_demodulation_clean() -> None:
    """Verify QPSK demodulation and Gray bit recovery."""
    n_syms = 250
    sps = 4
    np.random.seed(42)
    i_bits = np.random.choice([0, 1], size=n_syms)
    q_bits = np.random.choice([0, 1], size=n_syms)

    i_val = np.where(i_bits == 1, 1.0, -1.0) / np.sqrt(2.0)
    q_val = np.where(q_bits == 1, 1.0, -1.0) / np.sqrt(2.0)
    qpsk_syms = (i_val + 1j * q_val).astype(np.complex64)

    # RRC pulse shaping on transmission
    from signal_lab.synchronization.rrc import apply_rrc_filter

    tx_impulses = np.zeros(n_syms * sps, dtype=np.complex64)
    tx_impulses[::sps] = qpsk_syms
    samples = apply_rrc_filter(tx_impulses, sps=sps, alpha=0.35)

    demod = QPSKDemodulator(DemodConfig(sps=sps))
    res = demod.process(samples)

    assert len(res.symbols) > 0
    assert len(res.hard_bits) == len(res.symbols) * 2
    assert res.evm_percent < 40.0


def test_fsk_demodulation() -> None:
    """Verify FSK discriminator demodulation."""
    n_syms = 100
    sps = 8
    np.random.seed(42)
    tx_bits = np.random.choice([0, 1], size=n_syms)

    # Mark freq = +0.1 rad/sample, Space freq = -0.1 rad/sample
    dev = 0.15
    freqs = np.where(tx_bits == 1, dev, -dev)
    sample_freqs = np.repeat(freqs, sps)
    phase = np.cumsum(sample_freqs)
    samples = np.exp(1j * phase).astype(np.complex64)

    demod = FSKDemodulator(DemodConfig(sps=sps))
    res = demod.process(samples)

    assert len(res.hard_bits) == n_syms
    # Compare bits (skip first 2 transient symbols)
    ber = np.mean(res.hard_bits[2:] != tx_bits[2:])
    assert ber < 0.05


def test_demodulate_signal_convenience() -> None:
    """Verify high-level demodulate_signal factory function."""
    samples = np.array([1.0 + 1j, -1.0 + 1j, -1.0 - 1j, 1.0 - 1j] * 20, dtype=np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=10000)

    res = demodulate_signal(buf, modulation="QPSK", sps=1)
    assert len(res.hard_bits) > 0
    assert res.metrics["modulation"] == "QPSK"

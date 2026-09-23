"""Unit tests for DSP conditioning routines."""

import numpy as np
import pytest

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.dsp.conditioning import (
    correct_iq_imbalance,
    frequency_shift,
    normalize_amplitude,
    remove_dc_offset,
    resample_signal,
)


def test_remove_dc_offset() -> None:
    """Test DC offset cancellation on complex signal."""
    t = np.linspace(0, 1, 1000)
    sig = np.exp(1j * 2 * np.pi * 50 * t) + (0.5 + 0.3j)
    buf = SignalBuffer(samples=sig, sample_rate_hz=1000)

    cleaned = remove_dc_offset(buf)
    mean_val = np.mean(cleaned.samples)
    assert pytest.approx(float(np.abs(mean_val)), abs=1e-5) == 0.0
    assert "dc_offset_removed" in cleaned.metadata


def test_normalize_amplitude() -> None:
    """Test amplitude scaling to target peak."""
    samples = np.array([2.0 + 3.0j, -4.0 + 1.0j], dtype=np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=100)

    norm_buf = normalize_amplitude(buf, target_peak=1.0)
    peak = float(np.max(np.abs(norm_buf.samples)))
    assert pytest.approx(peak, rel=1e-5) == 1.0


def test_frequency_shift() -> None:
    """Test mixing with complex exponential."""
    fs = 10000.0
    t = np.arange(1000) / fs
    f0 = 100.0
    samples = np.exp(1j * 2 * np.pi * f0 * t).astype(np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=fs, center_frequency_hz=1000.0)

    # Shift by -100 Hz -> signal should become DC (constant phase)
    shifted = frequency_shift(buf, freq_shift_hz=-100.0)
    diffs = np.diff(np.angle(shifted.samples[:50]))
    assert pytest.approx(float(np.mean(np.abs(diffs))), abs=1e-4) == 0.0
    assert shifted.center_frequency_hz == 900.0


def test_correct_iq_imbalance() -> None:
    """Test correction of amplitude and phase skew in IQ samples."""
    n = 10000
    t = np.linspace(0, 100, n)
    i_pure = np.cos(t)
    q_pure = np.sin(t)

    # Introduce 20% amplitude imbalance and 15 deg phase skew
    phi = np.deg2rad(15)
    i_impaired = i_pure
    q_impaired = 1.2 * (q_pure * np.cos(phi) + i_pure * np.sin(phi))
    samples = (i_impaired + 1j * q_impaired).astype(np.complex64)

    buf = SignalBuffer(samples=samples, sample_rate_hz=1000)
    corrected = correct_iq_imbalance(buf)

    corr_i = np.real(corrected.samples)
    corr_q = np.imag(corrected.samples)

    # Check power balance
    p_i = np.mean(corr_i**2)
    p_q = np.mean(corr_q**2)
    assert pytest.approx(p_i, rel=0.1) == p_q


def test_resample_signal() -> None:
    """Test polyphase resampling."""
    fs = 10000.0
    t = np.arange(1000) / fs
    samples = np.exp(1j * 2 * np.pi * 500 * t).astype(np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=fs)

    target_fs = 20000.0
    resampled = resample_signal(buf, target_sample_rate_hz=target_fs)
    assert resampled.sample_rate_hz == 20000.0
    assert resampled.num_samples == 2000

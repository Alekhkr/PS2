"""Unit tests for signal detection and parameter estimation."""

import numpy as np
import pytest

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.estimation import (
    analyze_signal_parameters,
    detect_signal_regions,
    estimate_carrier_frequency,
    estimate_occupied_bandwidth,
    estimate_snr,
    estimate_symbol_rate,
)


def test_carrier_frequency_estimation() -> None:
    """Verify carrier frequency estimation with quadratic peak interpolation."""
    fs = 1_000_000.0  # 1 MHz
    target_fc = 45_250.0  # 45.25 kHz offset
    t = np.arange(20000) / fs
    samples = np.exp(1j * 2 * np.pi * target_fc * t).astype(np.complex64)
    buf = SignalBuffer(samples=samples, sample_rate_hz=fs, center_frequency_hz=145_000_000.0)

    ev = estimate_carrier_frequency(buf)
    assert ev.name == "carrier_frequency"
    assert ev.unit == "Hz"
    # Absolute carrier = center (145 MHz) + offset (45.25 kHz)
    expected_abs = 145_000_000.0 + target_fc
    assert pytest.approx(ev.value, abs=500.0) == expected_abs
    assert ev.confidence >= 0.8


def test_occupied_bandwidth_estimation() -> None:
    """Verify 99% occupied bandwidth calculation on bandpass noise."""
    fs = 500_000.0
    n = 20000
    # Generate white noise and lowpass filter it to 50 kHz cutoff (100 kHz complex bandwidth)
    noise = (np.random.randn(n) + 1j * np.random.randn(n)).astype(np.complex64)
    # Simple moving average filter to shape bandwidth
    filtered = np.convolve(noise, np.ones(5) / 5.0, mode="same").astype(np.complex64)
    buf = SignalBuffer(samples=filtered, sample_rate_hz=fs)

    ev = estimate_occupied_bandwidth(buf, power_ratio=0.99)
    assert ev.name == "bandwidth_99pct"
    assert ev.value > 0.0
    assert ev.confidence > 0.5


def test_snr_estimation() -> None:
    """Verify SNR estimator returns reasonable dB values for clean vs noisy signals."""
    fs = 100_000.0
    t = np.arange(10000) / fs
    clean_sig = np.exp(1j * 2 * np.pi * 10000 * t).astype(np.complex64)

    # Clean buffer
    clean_buf = SignalBuffer(samples=clean_sig, sample_rate_hz=fs)
    ev_clean = estimate_snr(clean_buf)
    assert ev_clean.value > 15.0

    # Noisy buffer (+ 1.0 noise power)
    noise = (np.random.randn(10000) + 1j * np.random.randn(10000)).astype(np.complex64)
    noisy_buf = SignalBuffer(samples=clean_sig + noise, sample_rate_hz=fs)
    ev_noisy = estimate_snr(noisy_buf)
    assert ev_noisy.value < ev_clean.value


def test_symbol_rate_estimation() -> None:
    """Verify symbol rate peak extraction using envelope squaring."""
    fs = 200_000.0
    symbol_rate = 10_000.0  # 10 kBaud
    sps = int(fs / symbol_rate)  # 20 samples per symbol
    num_symbols = 500
    bits = np.random.choice([-1, 1], size=num_symbols)
    # Upsample with pulses
    samples = np.zeros(num_symbols * sps, dtype=np.complex64)
    samples[::sps] = bits + 1j * bits
    # Add pulse shaping (simple RC filter)
    pulse = np.hanning(sps)
    shaped = np.convolve(samples, pulse, mode="same").astype(np.complex64)

    buf = SignalBuffer(samples=shaped, sample_rate_hz=fs)
    candidates = estimate_symbol_rate(buf)
    assert len(candidates) > 0
    # Top candidate should be close to 10 kHz
    top_cand = candidates[0]
    assert pytest.approx(top_cand.value, rel=0.1) == symbol_rate


def test_detect_signal_regions_and_unified_analysis() -> None:
    """Verify burst detector isolates signal periods from silence."""
    fs = 100_000.0
    # 0.1s silence + 0.05s burst + 0.1s silence
    n_silence = int(0.05 * fs)
    n_burst = int(0.05 * fs)
    t_burst = np.arange(n_burst) / fs
    burst = (np.exp(1j * 2 * np.pi * 5000 * t_burst) * 2.0).astype(np.complex64)

    noise_silence1 = (
        np.random.randn(n_silence) * 0.01 + 1j * np.random.randn(n_silence) * 0.01
    ).astype(np.complex64)
    noise_silence2 = (
        np.random.randn(n_silence) * 0.01 + 1j * np.random.randn(n_silence) * 0.01
    ).astype(np.complex64)

    full_samples = np.concatenate([noise_silence1, burst, noise_silence2])
    buf = SignalBuffer(samples=full_samples, sample_rate_hz=fs, center_frequency_hz=145_000_000.0)

    segments = detect_signal_regions(buf, threshold_db=6.0)
    assert len(segments) >= 1
    # Check that the burst was detected around 0.05s
    seg = segments[0]
    assert pytest.approx(seg.start_time_s, abs=0.03) == 0.05

    # Test unified analysis
    segs, evidence = analyze_signal_parameters(buf)
    assert len(segs) >= 1
    assert len(evidence) >= 4  # carrier, bandwidth, snr, symbol rates

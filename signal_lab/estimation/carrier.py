"""Carrier and Center Frequency Estimation."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.enums import EvidenceSource, ValidationStatus
from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer


def estimate_carrier_frequency(buffer: SignalBuffer, nperseg: int = 4096) -> ParameterEvidence:
    """Estimates the dominant carrier/center frequency with sub-bin quadratic interpolation."""
    if buffer.num_samples < 16:
        return ParameterEvidence(
            name="carrier_frequency",
            value=buffer.center_frequency_hz or 0.0,
            unit="Hz",
            source=EvidenceSource.ESTIMATOR,
            algorithm="none",
            confidence=0.0,
            validation=ValidationStatus.REJECTED,
        )

    fs = buffer.sample_rate_hz or 1.0
    nperseg = min(nperseg, buffer.num_samples)

    freqs, psd = signal.welch(
        buffer.samples,
        fs=fs,
        window="hann",
        nperseg=nperseg,
        return_onesided=False,
        scaling="density",
    )

    freqs = np.fft.fftshift(freqs)
    psd = np.fft.fftshift(psd)

    peak_idx = int(np.argmax(psd))

    # Quadratic interpolation around peak for sub-bin resolution
    if 0 < peak_idx < len(psd) - 1:
        alpha = float(psd[peak_idx - 1])
        beta = float(psd[peak_idx])
        gamma = float(psd[peak_idx + 1])
        delta = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma + 1e-15)
        bin_spacing = fs / nperseg
        sub_bin_offset = delta * bin_spacing
    else:
        sub_bin_offset = 0.0

    carrier_offset_hz = float(freqs[peak_idx]) + sub_bin_offset
    absolute_carrier_hz = (
        (buffer.center_frequency_hz + carrier_offset_hz)
        if buffer.center_frequency_hz is not None
        else carrier_offset_hz
    )

    # Confidence estimation from peak-to-median ratio (PMR)
    median_psd = float(np.median(psd))
    peak_psd = float(psd[peak_idx])
    pmr = peak_psd / (median_psd + 1e-18)
    confidence = float(np.clip(1.0 - np.exp(-pmr / 20.0), 0.1, 0.99))

    return ParameterEvidence(
        name="carrier_frequency",
        value=round(absolute_carrier_hz, 2),
        unit="Hz",
        source=EvidenceSource.ESTIMATOR,
        algorithm="welch_psd_quadratic_peak_v1",
        confidence=round(confidence, 3),
        assumptions=["single_dominant_carrier", "stationary_over_window"],
        validation=ValidationStatus.PARTIAL,
    )

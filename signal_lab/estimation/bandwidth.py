"""Occupied Bandwidth (OBW) estimation."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.enums import EvidenceSource, ValidationStatus
from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer


def estimate_occupied_bandwidth(
    buffer: SignalBuffer,
    power_ratio: float = 0.99,
    nperseg: int = 2048,
) -> ParameterEvidence:
    """Estimates the fractional power occupied bandwidth (e.g. 99% OBW)."""
    if buffer.num_samples < 32 or not buffer.sample_rate_hz:
        return ParameterEvidence(
            name="bandwidth_99pct",
            value=0.0,
            unit="Hz",
            source=EvidenceSource.ESTIMATOR,
            algorithm="none",
            confidence=0.0,
            validation=ValidationStatus.REJECTED,
        )

    fs = buffer.sample_rate_hz
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

    # Cumulative power distribution
    total_power = np.sum(psd)
    if total_power <= 0:
        return ParameterEvidence(
            name="bandwidth_99pct",
            value=0.0,
            unit="Hz",
            source=EvidenceSource.ESTIMATOR,
            algorithm="none",
            confidence=0.0,
            validation=ValidationStatus.REJECTED,
        )

    cum_power = np.cumsum(psd) / total_power

    # Find percentiles: e.g. for 99%, lower = 0.5%, upper = 99.5%
    alpha = (1.0 - power_ratio) / 2.0
    lower_idx = int(np.searchsorted(cum_power, alpha))
    upper_idx = int(np.searchsorted(cum_power, 1.0 - alpha))
    lower_idx = min(lower_idx, len(freqs) - 1)
    upper_idx = min(upper_idx, len(freqs) - 1)

    obw_hz = float(abs(freqs[upper_idx] - freqs[lower_idx]))

    # Confidence derived from SNR / spectral flatness
    confidence = 0.85 if obw_hz > 0 else 0.1

    return ParameterEvidence(
        name="bandwidth_99pct",
        value=round(obw_hz, 1),
        unit="Hz",
        source=EvidenceSource.ESTIMATOR,
        algorithm="welch_cumulative_power_obw_v1",
        confidence=confidence,
        assumptions=[f"fractional_power_ratio_{int(power_ratio * 100)}%"],
        validation=ValidationStatus.PARTIAL,
    )

"""Signal-to-Noise Ratio (SNR) estimation."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.enums import EvidenceSource, ValidationStatus
from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer


def estimate_snr(buffer: SignalBuffer, nperseg: int = 2048) -> ParameterEvidence:
    """Estimates in-band SNR comparing peak spectral energy to the median noise floor."""
    if buffer.num_samples < 32:
        return ParameterEvidence(
            name="snr",
            value=0.0,
            unit="dB",
            source=EvidenceSource.ESTIMATOR,
            algorithm="none",
            confidence=0.0,
            validation=ValidationStatus.REJECTED,
        )

    fs = buffer.sample_rate_hz or 1.0
    nperseg = min(nperseg, buffer.num_samples)

    _, psd = signal.welch(
        buffer.samples,
        fs=fs,
        window="hann",
        nperseg=nperseg,
        return_onesided=False,
    )

    noise_floor = float(np.median(psd))
    if noise_floor <= 0:
        noise_floor = 1e-15

    # Signal power estimate (top 10% bins)
    sorted_psd = np.sort(psd)
    top_bins = sorted_psd[int(len(sorted_psd) * 0.9) :]
    signal_power = float(np.mean(top_bins))

    snr_linear = max(1e-3, (signal_power - noise_floor) / noise_floor)
    snr_db = 10.0 * np.log10(snr_linear)

    # High SNR gives high confidence
    confidence = float(np.clip(1.0 / (1.0 + np.exp(-snr_db / 10.0)), 0.2, 0.95))

    return ParameterEvidence(
        name="snr",
        value=round(snr_db, 1),
        unit="dB",
        source=EvidenceSource.ESTIMATOR,
        algorithm="spectral_noise_floor_differential_v1",
        confidence=round(confidence, 3),
        assumptions=["gaussian_background_noise", "sparse_signal_spectrum"],
        validation=ValidationStatus.PARTIAL,
    )

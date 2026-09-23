"""Symbol Rate (Baud Rate) estimation using cyclostationary non-linear envelope spectrum."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.enums import EvidenceSource, ValidationStatus
from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer


def estimate_symbol_rate(
    buffer: SignalBuffer,
    n_candidates: int = 3,
) -> list[ParameterEvidence]:
    """Estimates symbol rate candidates using envelope squaring / delay-multiply spectral line analysis."""
    if buffer.num_samples < 256 or not buffer.sample_rate_hz:
        return []

    fs = buffer.sample_rate_hz

    # 1. Non-linear envelope transformation (squaring of magnitude)
    envelope = np.abs(buffer.samples) ** 2
    envelope = envelope - np.mean(envelope)  # Remove DC

    # 2. Compute PSD of the squared envelope
    nperseg = min(4096, len(envelope))
    freqs, psd = signal.welch(
        envelope,
        fs=fs,
        window="hann",
        nperseg=nperseg,
        return_onesided=True,
    )

    # Exclude DC and very low frequencies (< fs / 200)
    min_freq_idx = max(2, int(len(freqs) * 0.01))
    valid_freqs = freqs[min_freq_idx:]
    valid_psd = psd[min_freq_idx:]

    if len(valid_psd) < 5:
        return []

    # Find prominent peaks in envelope spectrum
    median_pwr = np.median(valid_psd)
    peaks, _ = signal.find_peaks(
        valid_psd,
        prominence=median_pwr * 2.0,
        distance=max(2, nperseg // 100),
    )

    if len(peaks) == 0:
        # Fallback to absolute highest peak
        peaks = np.array([np.argmax(valid_psd)])

    # Sort peaks by prominence / height
    peak_heights = valid_psd[peaks]
    sorted_indices = np.argsort(peak_heights)[::-1][:n_candidates]

    results: list[ParameterEvidence] = []
    for rank, idx in enumerate(sorted_indices):
        p_idx = peaks[idx]
        cand_rate = float(valid_freqs[p_idx])
        peak_pwr = float(valid_psd[p_idx])

        # Confidence scored relative to median floor and rank
        snr_metric = peak_pwr / (median_pwr + 1e-15)
        raw_conf = float(np.clip(snr_metric / 15.0, 0.2, 0.95))
        discounted_conf = raw_conf * (0.9**rank)

        evidence = ParameterEvidence(
            name=f"symbol_rate_candidate_{rank + 1}",
            value=round(cand_rate, 1),
            unit="Sym/s",
            source=EvidenceSource.ESTIMATOR,
            algorithm="envelope_squaring_cyclostationary_v1",
            confidence=round(discounted_conf, 3),
            assumptions=["linear_modulation_timing_periodicity", "oversampled_symbols"],
            validation=ValidationStatus.PARTIAL,
        )
        results.append(evidence)

    return results

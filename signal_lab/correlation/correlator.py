"""Bitstream correlation and frame length detection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class CorrelationMatch:
    offset_bits: int
    correlation_score: float  # [0.0, 1.0]
    matched_pattern_length: int
    candidate_frame_length: int | None = None
    status: str = "candidate"


STANDARD_SYNC_WORDS: dict[str, list[int]] = {
    "Barker_13": [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    "Barker_11": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "Barker_7": [1, 1, 1, 0, 0, 1, 0],
    "CCSDS_ASM_32": [0x1A, 0xCF, 0xFC, 0x1D],  # 00011010110011111111110000011101
    "AX25_FLAG": [0, 1, 1, 1, 1, 1, 1, 0],
}


def correlate_sync_word(
    bitstream: np.ndarray,
    sync_pattern: list[int] | np.ndarray,
    threshold: float = 0.85,
) -> list[CorrelationMatch]:
    """Finds occurrences of a known sync word in the bitstream via sliding cross-correlation."""
    pattern = np.array(sync_pattern, dtype=np.int8)
    pat_len = len(pattern)
    n_bits = len(bitstream)

    if n_bits < pat_len:
        return []

    # Map {0, 1} to {-1, +1} for fast zero-mean bipolar correlation
    bipolar_stream = (bitstream.astype(np.int8) * 2) - 1
    bipolar_pattern = (pattern * 2) - 1

    # Cross correlation using 1D convolution
    corr = np.convolve(bipolar_stream, bipolar_pattern[::-1], mode="valid") / float(pat_len)

    matches: list[CorrelationMatch] = []
    peak_indices = np.where(corr >= threshold)[0]

    for idx in peak_indices:
        score = float(corr[idx])
        matches.append(
            CorrelationMatch(
                offset_bits=int(idx),
                correlation_score=round(score, 3),
                matched_pattern_length=pat_len,
            )
        )

    # Detect frame length periodicity if multiple sync peaks are found
    if len(matches) >= 2:
        diffs = np.diff([m.offset_bits for m in matches])
        common_frame_len = int(np.median(diffs))
        for m in matches:
            m.candidate_frame_length = common_frame_len

    return matches


def detect_frame_periodicity(bitstream: np.ndarray, max_lag: int = 4096) -> int | None:
    """Estimates unknown frame length by finding autocorrelation peaks of the bitstream."""
    n = len(bitstream)
    if n < 128:
        return None

    bipolar = (bitstream[: min(n, 16384)].astype(np.float32) * 2.0) - 1.0
    bipolar -= np.mean(bipolar)

    # Compute autocorrelation via FFT
    n_fft = 1 << (len(bipolar) * 2 - 1).bit_length()
    fx = np.fft.fft(bipolar, n=n_fft)
    acorr = np.fft.ifft(fx * np.conj(fx)).real
    acorr = acorr[: len(bipolar)]
    acorr = acorr / (acorr[0] + 1e-12)

    # Look for peaks between lag 64 and max_lag
    min_lag = 32
    max_search = min(len(acorr) // 2, max_lag)
    if max_search <= min_lag:
        return None

    search_region = acorr[min_lag:max_search]
    peak_offset = int(np.argmax(search_region))
    peak_lag = min_lag + peak_offset
    peak_height = float(search_region[peak_offset])

    if peak_height > 0.15:
        return peak_lag

    return None

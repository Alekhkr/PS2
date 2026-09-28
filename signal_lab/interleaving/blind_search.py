"""Blind Block Interleaver Parameter Discovery Engine.

Detects unknown interleaver period and matrix dimensions (Rows x Columns)
directly from raw demodulated bitstreams using GF(2) matrix rank deficiency
and bit-transition auto-correlation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class InterleaverCandidate:
    """A detected candidate interleaver dimension with evidence scoring."""

    period: int
    rank_defect: int
    normalized_score: float
    confidence: float
    method: str  # "rank_deficiency" or "autocorrelation"


def gf2_rank(matrix: np.ndarray) -> int:
    """Computes the exact rank of a binary matrix over GF(2) using Gaussian elimination."""
    m, n = matrix.shape
    mat = (matrix % 2).astype(np.uint8).copy()
    rank = 0

    col = 0
    for row in range(m):
        if col >= n:
            break
        # Find pivot in current column
        pivot = row
        while pivot < m and mat[pivot, col] == 0:
            pivot += 1

        if pivot == m:
            # No pivot in this column, move to next column
            col += 1
            continue

        # Swap rows
        if pivot != row:
            mat[[row, pivot]] = mat[[pivot, row]]

        # Eliminate entries below and above pivot
        for r in range(m):
            if r != row and mat[r, col] == 1:
                mat[r, :] ^= mat[row, :]

        rank += 1
        col += 1

    return rank


class BlindInterleaverAnalyzer:
    """Discovers unknown interleaver parameters from demodulated bitstreams."""

    @classmethod
    def search_candidates(
        cls,
        bits: np.ndarray,
        min_width: int = 4,
        max_width: int = 128,
        num_rows: int = 64,
    ) -> list[InterleaverCandidate]:
        """Performs rank-deficiency and auto-correlation search across candidate interleaver widths.

        Returns candidates sorted in descending order of confidence.
        """
        hard_bits = (bits > 0).astype(np.uint8)
        if len(hard_bits) < min_width * 8:
            return []

        candidates: list[InterleaverCandidate] = []

        # 1. Rank Deficiency Analysis over candidate widths
        for w in range(min_width, min(max_width + 1, len(hard_bits) // 8)):
            m = min(num_rows, len(hard_bits) // w)
            if m < 4:
                continue

            matrix = hard_bits[: m * w].reshape(m, w)
            r = gf2_rank(matrix)
            expected_full_rank = min(m, w)
            defect = expected_full_rank - r

            if defect > 0:
                # Rank defect is a strong indicator of linear parity dependencies
                score = defect / expected_full_rank
                conf = min(0.95, 0.4 + 0.6 * score)
                candidates.append(
                    InterleaverCandidate(
                        period=w,
                        rank_defect=defect,
                        normalized_score=float(score),
                        confidence=float(conf),
                        method="rank_deficiency",
                    )
                )

        # 2. Transition Auto-Correlation
        diffs = (hard_bits[1:] ^ hard_bits[:-1]).astype(np.float32)
        diffs -= np.mean(diffs)
        var = np.var(diffs)
        if var > 1e-6 and len(diffs) > max_width * 2:
            autocorr = np.correlate(diffs, diffs, mode="full")
            mid = len(diffs) - 1
            lags = autocorr[mid + 1 : mid + max_width + 1] / (var * len(diffs))

            for lag_idx, corr_val in enumerate(lags, start=1):
                if corr_val > 0.15 and lag_idx >= min_width:
                    conf = min(0.90, float(corr_val * 2.0))
                    candidates.append(
                        InterleaverCandidate(
                            period=lag_idx,
                            rank_defect=0,
                            normalized_score=float(corr_val),
                            confidence=conf,
                            method="autocorrelation",
                        )
                    )

        # Deduplicate and sort by confidence descending
        dedup: dict[int, InterleaverCandidate] = {}
        for cand in candidates:
            if cand.period not in dedup or cand.confidence > dedup[cand.period].confidence:
                dedup[cand.period] = cand

        results = sorted(dedup.values(), key=lambda c: c.confidence, reverse=True)
        return results


@dataclass
class ConvolutionalInterleaverCandidate:
    """Detected candidate convolutional interleaver (Forney/Ramsey) structure."""

    branches: int  # Number of shift register delay branches B
    base_delay: int  # Delay step multiplier M
    period: int  # Effective period B * M
    confidence: float
    score: float


def blind_convolutional_interleaver_search(
    bits: np.ndarray,
    min_branches: int = 2,
    max_branches: int = 16,
    max_delay: int = 8,
) -> list[ConvolutionalInterleaverCandidate]:
    """Blind search for Forney/Ramsey convolutional interleaver parameters (B, M).

    Analyzes periodic auto-correlation of symbol transition sequences and
    cyclic branch variance.
    """
    hard_bits = (bits > 0).astype(np.int8)
    n = len(hard_bits)
    if n < max_branches * max_delay * 8:
        return []

    # Map bits to bipolar {-1, +1}
    bipolar = 2 * hard_bits.astype(np.float32) - 1.0
    candidates: list[ConvolutionalInterleaverCandidate] = []

    # Fast autocorrelation across candidate periods B * M
    max_lag = max_branches * max_delay + 2
    autocorr = np.zeros(max_lag, dtype=np.float32)
    for lag in range(1, max_lag):
        autocorr[lag] = np.mean(bipolar[:-lag] * bipolar[lag:])

    for b in range(min_branches, max_branches + 1):
        for m in range(1, max_delay + 1):
            period = b * m
            if period < max_lag:
                corr_peak = float(abs(autocorr[period]))
                # Check harmonic at 2 * period
                harmonic = float(abs(autocorr[2 * period])) if 2 * period < max_lag else 0.0

                score = corr_peak + 0.5 * harmonic
                if score > 0.08:
                    conf = min(0.92, float(score * 2.5))
                    candidates.append(
                        ConvolutionalInterleaverCandidate(
                            branches=b,
                            base_delay=m,
                            period=period,
                            confidence=conf,
                            score=score,
                        )
                    )

    # Sort descending by confidence
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates


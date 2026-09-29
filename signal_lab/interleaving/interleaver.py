"""Interleaver hypothesis generator and consistency validation."""

from __future__ import annotations

import numpy as np

from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import InterleaverCandidate
from signal_lab.fec import evaluate_fec_hypotheses


def interleave_block(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Applies block interleaver where transmitter writes row-wise and reads col-wise."""
    block_size = rows * cols
    n_blocks = len(bits) // block_size
    if n_blocks == 0:
        return bits

    out = np.empty_like(bits[: n_blocks * block_size])
    for b in range(n_blocks):
        chunk = bits[b * block_size : (b + 1) * block_size]
        # Write rows x cols, read cols x rows
        matrix = chunk.reshape((rows, cols)).T
        out[b * block_size : (b + 1) * block_size] = matrix.flatten()
    return out


def deinterleave_block(bits: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Reverses block interleaver where transmitter writes row-wise and reads col-wise."""
    block_size = rows * cols
    n_blocks = len(bits) // block_size
    if n_blocks == 0:
        return bits

    out = np.empty_like(bits[: n_blocks * block_size])
    for b in range(n_blocks):
        chunk = bits[b * block_size : (b + 1) * block_size]
        # Invert: chunk was read by columns, so shape is (cols, rows). Transpose to restore original (rows, cols)
        matrix = chunk.reshape((cols, rows)).T
        out[b * block_size : (b + 1) * block_size] = matrix.flatten()

    return out


def evaluate_interleaver_hypotheses(
    coded_bits: np.ndarray,
    candidate_dims: list[tuple[int, int]] | None = None,
) -> list[InterleaverCandidate]:
    """Tests block and diagonal interleaver hypotheses, validating each against downstream FEC."""
    if len(coded_bits) < 64:
        return []

    dims = candidate_dims or [
        (8, 8),
        (8, 16),
        (16, 16),
        (16, 32),
        (32, 32),
    ]

    # Baseline FEC score without de-interleaving
    baseline_fec = evaluate_fec_hypotheses(coded_bits)
    baseline_score = baseline_fec[0].syndrome_score if baseline_fec else 0.0

    candidates: list[InterleaverCandidate] = []

    for rows, cols in dims:
        if rows * cols > len(coded_bits):
            continue

        depermuted = deinterleave_block(coded_bits, rows=rows, cols=cols)
        fec_results = evaluate_fec_hypotheses(depermuted)
        score = fec_results[0].syndrome_score if fec_results else 0.0

        # Only promote if downstream FEC improves or achieves high syndrome validity
        if score > baseline_score + 0.05 or score > 0.85:
            cand = InterleaverCandidate(
                type="block",
                parameters={"rows": rows, "cols": cols, "block_size": rows * cols},
                score=score,
                status=ValidationStatus.VALIDATED if score > 0.85 else ValidationStatus.PARTIAL,
            )
            candidates.append(cand)

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates

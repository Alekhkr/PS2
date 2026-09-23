"""Unit tests for block interleaver and hypothesis search."""

import numpy as np

from signal_lab.interleaving import deinterleave_block, evaluate_interleaver_hypotheses


def test_deinterleave_block_inversion() -> None:
    """Verify block interleaver row-write col-read inversion."""
    rows = 4
    cols = 6
    block_size = rows * cols
    original_bits = np.arange(block_size, dtype=np.uint8)

    # Interleave: write rows, read cols
    matrix = original_bits.reshape((rows, cols))
    interleaved = matrix.T.flatten()

    # De-interleave
    recovered = deinterleave_block(interleaved, rows=rows, cols=cols)
    assert np.array_equal(original_bits, recovered)


def test_interleaver_hypotheses_search() -> None:
    """Verify interleaver hypothesis test executes without errors."""
    bits = np.random.choice([0, 1], size=512).astype(np.uint8)
    candidates = evaluate_interleaver_hypotheses(bits, candidate_dims=[(8, 8), (16, 16)])
    assert isinstance(candidates, list)

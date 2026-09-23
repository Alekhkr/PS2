"""Unit tests for bitstream cross-correlation and frame periodicity detection."""

import numpy as np

from signal_lab.correlation import (
    STANDARD_SYNC_WORDS,
    correlate_sync_word,
    detect_frame_periodicity,
)


def test_correlate_sync_word_exact() -> None:
    """Verify exact match of Barker-13 sync word at specific offset."""
    barker13 = STANDARD_SYNC_WORDS["Barker_13"]

    # Frame structure: [40 random bits] + [Barker-13] + [50 random bits]
    np.random.seed(123)
    prefix = np.random.choice([0, 1], size=40)
    suffix = np.random.choice([0, 1], size=50)
    stream = np.concatenate([prefix, barker13, suffix]).astype(np.uint8)

    matches = correlate_sync_word(stream, barker13, threshold=0.99)
    assert len(matches) == 1
    assert matches[0].offset_bits == 40
    assert matches[0].correlation_score == 1.0


def test_correlate_sync_word_periodic_frame_len() -> None:
    """Verify candidate frame length detection across multiple sync word occurrences."""
    barker13 = STANDARD_SYNC_WORDS["Barker_13"]
    frame_len = 100

    stream = np.zeros(frame_len * 3, dtype=np.uint8)
    # Insert sync words at offset 10, 110, 210
    stream[10 : 10 + len(barker13)] = barker13
    stream[110 : 110 + len(barker13)] = barker13
    stream[210 : 210 + len(barker13)] = barker13

    matches = correlate_sync_word(stream, barker13, threshold=0.99)
    assert len(matches) == 3
    assert matches[0].candidate_frame_length == 100


def test_detect_frame_periodicity() -> None:
    """Verify autocorrelation detects recurring frame structure."""
    frame_len = 120
    n_frames = 15
    np.random.seed(99)
    base_frame = np.random.choice([0, 1], size=frame_len)
    repeated = np.tile(base_frame, n_frames).astype(np.uint8)

    inferred_len = detect_frame_periodicity(repeated, max_lag=500)
    assert inferred_len == frame_len

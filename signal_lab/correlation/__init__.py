"""Correlation module exports."""

from signal_lab.correlation.correlator import (
    STANDARD_SYNC_WORDS,
    CorrelationMatch,
    correlate_sync_word,
    detect_frame_periodicity,
)

__all__ = [
    "STANDARD_SYNC_WORDS",
    "CorrelationMatch",
    "correlate_sync_word",
    "detect_frame_periodicity",
]

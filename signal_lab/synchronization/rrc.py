"""Root-Raised Cosine (RRC) matched filter implementation."""

from __future__ import annotations

import numpy as np
from scipy import signal


def rrc_taps(sps: int, span: int, alpha: float) -> np.ndarray:
    """Generates Root-Raised-Cosine (RRC) filter impulse response taps.

    Parameters:
        sps: Samples per symbol (oversampling factor)
        span: Filter length in symbols
        alpha: Roll-off factor [0.0, 1.0]
    """
    n_taps = span * sps + 1
    t = np.arange(-span * sps // 2, span * sps // 2 + 1) / sps
    taps = np.zeros(n_taps, dtype=np.float32)

    for i, t_val in enumerate(t):
        if np.isclose(t_val, 0.0):
            taps[i] = 1.0 - alpha + (4.0 * alpha / np.pi)
        elif alpha != 0 and np.isclose(np.abs(t_val), 1.0 / (4.0 * alpha)):
            taps[i] = (alpha / np.sqrt(2.0)) * (
                ((1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * alpha)))
                + ((1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * alpha)))
            )
        else:
            numer = np.sin(np.pi * t_val * (1.0 - alpha)) + 4.0 * alpha * t_val * np.cos(
                np.pi * t_val * (1.0 + alpha)
            )
            denom = np.pi * t_val * (1.0 - (4.0 * alpha * t_val) ** 2)
            taps[i] = numer / denom

    # Normalize to unit energy
    taps = taps / np.sqrt(np.sum(taps**2))
    return taps


def apply_rrc_filter(
    samples: np.ndarray,
    sps: int = 4,
    span: int = 8,
    alpha: float = 0.35,
) -> np.ndarray:
    """Applies RRC matched filtering to complex IQ samples."""
    taps = rrc_taps(sps=sps, span=span, alpha=alpha)
    filtered = signal.convolve(samples, taps, mode="same")
    return filtered.astype(np.complex64)

"""Base demodulator interface and result data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class DemodConfig:
    """Demodulation configuration parameters."""

    sps: int = 4
    rrc_alpha: float = 0.35
    costas_damping: float = 0.707
    costas_loop_bw: float = 0.05
    fsk_deviation_hz: float | None = None


@dataclass
class DemodResult:
    """Auditable demodulation output containing symbols, bits, and EVM quality metrics."""

    symbols: np.ndarray
    hard_bits: np.ndarray
    soft_bits: np.ndarray | None = None
    evm_percent: float = 0.0
    converged: bool = False
    metrics: dict = field(default_factory=dict)


class Demodulator(Protocol):
    """Protocol interface for all modulation-specific demodulators."""

    def configure(self, config: DemodConfig) -> None: ...

    def process(self, samples: np.ndarray) -> DemodResult: ...

    def metrics(self) -> dict: ...

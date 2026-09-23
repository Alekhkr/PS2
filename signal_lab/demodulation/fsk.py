"""Frequency Shift Keying (FSK) Demodulator via quadrature discriminator."""

from __future__ import annotations

import numpy as np

from signal_lab.demodulation.base import DemodConfig, DemodResult


class FSKDemodulator:
    """Demodulates FSK signals using a delay-conjugate phase discriminator."""

    def __init__(self, config: DemodConfig | None = None) -> None:
        self.config = config or DemodConfig()
        self._last_metrics: dict = {}

    def configure(self, config: DemodConfig) -> None:
        self.config = config

    def process(self, samples: np.ndarray) -> DemodResult:
        if len(samples) < 16:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 1. Delay-conjugate product: x[n] * conj(x[n-1])
        prod = samples[1:] * np.conj(samples[:-1])
        inst_freq = np.angle(prod)

        # 2. Downsample by samples-per-symbol (sps) at center strobe
        sps = max(1, self.config.sps)
        offset = sps // 2
        symbols_freq = inst_freq[offset::sps]

        # Normalize frequency deviation
        mean_offset = float(np.mean(symbols_freq))
        centered_freq = symbols_freq - mean_offset

        # 3. Bit decision: freq > 0 -> Mark (1), freq <= 0 -> Space (0)
        bits = (centered_freq > 0).astype(np.uint8)

        # 4. Construct analytic constellation from discriminator output
        complex_symbols = (centered_freq + 1j * np.zeros_like(centered_freq)).astype(np.complex64)

        # Quality metric: frequency separation ratio
        mark_power = float(np.mean(centered_freq[bits == 1] ** 2)) if np.any(bits == 1) else 1e-6
        space_power = float(np.mean(centered_freq[bits == 0] ** 2)) if np.any(bits == 0) else 1e-6
        evm_percent = min(
            100.0,
            float(np.abs(mark_power - space_power) / (mark_power + space_power + 1e-12)) * 50.0,
        )

        self._last_metrics = {
            "modulation": "FSK",
            "symbol_count": len(bits),
            "mean_frequency_offset_rad": mean_offset,
            "evm_percent": evm_percent,
        }

        return DemodResult(
            symbols=complex_symbols,
            hard_bits=bits,
            soft_bits=centered_freq.astype(np.float32),
            evm_percent=evm_percent,
            converged=True,
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics

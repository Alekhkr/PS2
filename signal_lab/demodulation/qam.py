"""QAM Demodulators (QAM16 and QAM64) with multi-level grid slicing."""

from __future__ import annotations

import numpy as np

from signal_lab.demodulation.base import DemodConfig, DemodResult
from signal_lab.synchronization.carrier_recovery import CostasLoop
from signal_lab.synchronization.rrc import apply_rrc_filter
from signal_lab.synchronization.timing_recovery import MuellerMullerTimingRecovery


class QAM16Demodulator:
    """16-QAM Demodulator (4 bits/symbol: 2 I bits, 2 Q bits) on normalized grid."""

    def __init__(self, config: DemodConfig | None = None) -> None:
        self.config = config or DemodConfig()
        self._last_metrics: dict = {}

    def configure(self, config: DemodConfig) -> None:
        self.config = config

    def process(self, samples: np.ndarray) -> DemodResult:
        if len(samples) < 16:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 1. Matched Filter
        filtered = apply_rrc_filter(samples, sps=self.config.sps, alpha=self.config.rrc_alpha)

        # 2. Carrier Recovery
        costas = CostasLoop(
            order=4, damping=self.config.costas_damping, loop_bw=self.config.costas_loop_bw
        )
        carrier_sync, c_metrics = costas.process(filtered)

        # 3. Timing Recovery
        ted = MuellerMullerTimingRecovery(sps=self.config.sps)
        symbols, t_metrics = ted.process(carrier_sync)

        if len(symbols) == 0:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 4. Scale so average symbol power = 10 (ideal grid levels are -3, -1, 1, 3)
        # Average power of 16-QAM with levels {-3, -1, 1, 3} is: (2*(1+9)/4)*2 = 10
        rms_pwr = float(np.sqrt(np.mean(np.abs(symbols) ** 2)))
        scale = np.sqrt(10.0) / (rms_pwr + 1e-12)
        grid_symbols = (symbols * scale).astype(np.complex64)

        # Slicing I and Q onto {-3, -1, 1, 3}
        grid_levels = np.array([-3.0, -1.0, 1.0, 3.0])

        i_real = np.real(grid_symbols)
        q_imag = np.imag(grid_symbols)

        i_idx = np.argmin(np.abs(i_real[:, None] - grid_levels[None, :]), axis=1)
        q_idx = np.argmin(np.abs(q_imag[:, None] - grid_levels[None, :]), axis=1)

        # Gray mapping for 4 levels: 00 -> -3, 01 -> -1, 11 -> 1, 10 -> 3
        # indices 0->00, 1->01, 2->11, 3->10
        gray_bits = np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.uint8)

        i_bits = gray_bits[i_idx]
        q_bits = gray_bits[q_idx]

        # Interleave bits: [I0, I1, Q0, Q1]
        bits = np.empty((len(symbols), 4), dtype=np.uint8)
        bits[:, 0:2] = i_bits
        bits[:, 2:4] = q_bits
        flat_bits = bits.flatten()

        # EVM calculation against ideal grid
        ideal_syms = grid_levels[i_idx] + 1j * grid_levels[q_idx]
        error = grid_symbols - ideal_syms
        rms_err = float(np.sqrt(np.mean(np.abs(error) ** 2)))
        evm_percent = min(100.0, (rms_err / np.sqrt(10.0)) * 100.0)

        self._last_metrics = {
            **c_metrics,
            **t_metrics,
            "evm_percent": evm_percent,
            "modulation": "QAM16",
        }

        return DemodResult(
            symbols=grid_symbols / np.sqrt(10.0),
            hard_bits=flat_bits,
            evm_percent=evm_percent,
            converged=c_metrics.get("converged", False),
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics


class QAM64Demodulator:
    """64-QAM Demodulator (6 bits/symbol: 3 I bits, 3 Q bits) on normalized grid."""

    def __init__(self, config: DemodConfig | None = None) -> None:
        self.config = config or DemodConfig()
        self._last_metrics: dict = {}

    def configure(self, config: DemodConfig) -> None:
        self.config = config

    def process(self, samples: np.ndarray) -> DemodResult:
        if len(samples) < 16:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        filtered = apply_rrc_filter(samples, sps=self.config.sps, alpha=self.config.rrc_alpha)
        costas = CostasLoop(
            order=4, damping=self.config.costas_damping, loop_bw=self.config.costas_loop_bw
        )
        carrier_sync, c_metrics = costas.process(filtered)

        ted = MuellerMullerTimingRecovery(sps=self.config.sps)
        symbols, t_metrics = ted.process(carrier_sync)

        if len(symbols) == 0:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # Ideal 64-QAM grid: {-7, -5, -3, -1, 1, 3, 5, 7}, avg power = 42
        rms_pwr = float(np.sqrt(np.mean(np.abs(symbols) ** 2)))
        scale = np.sqrt(42.0) / (rms_pwr + 1e-12)
        grid_symbols = (symbols * scale).astype(np.complex64)

        grid_levels = np.array([-7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0])
        i_real = np.real(grid_symbols)
        q_imag = np.imag(grid_symbols)

        i_idx = np.argmin(np.abs(i_real[:, None] - grid_levels[None, :]), axis=1)
        q_idx = np.argmin(np.abs(q_imag[:, None] - grid_levels[None, :]), axis=1)

        gray_bits = np.array(
            [
                [0, 0, 0],
                [0, 0, 1],
                [0, 1, 1],
                [0, 1, 0],
                [1, 1, 0],
                [1, 1, 1],
                [1, 0, 1],
                [1, 0, 0],
            ],
            dtype=np.uint8,
        )

        i_bits = gray_bits[i_idx]
        q_bits = gray_bits[q_idx]

        bits = np.empty((len(symbols), 6), dtype=np.uint8)
        bits[:, 0:3] = i_bits
        bits[:, 3:6] = q_bits
        flat_bits = bits.flatten()

        ideal_syms = grid_levels[i_idx] + 1j * grid_levels[q_idx]
        error = grid_symbols - ideal_syms
        rms_err = float(np.sqrt(np.mean(np.abs(error) ** 2)))
        evm_percent = min(100.0, (rms_err / np.sqrt(42.0)) * 100.0)

        self._last_metrics = {
            **c_metrics,
            **t_metrics,
            "evm_percent": evm_percent,
            "modulation": "QAM64",
        }

        return DemodResult(
            symbols=grid_symbols / np.sqrt(42.0),
            hard_bits=flat_bits,
            evm_percent=evm_percent,
            converged=c_metrics.get("converged", False),
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics

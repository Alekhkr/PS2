"""PSK Demodulator implementations (BPSK, QPSK, 8PSK)."""

from __future__ import annotations

import numpy as np

from signal_lab.demodulation.base import DemodConfig, DemodResult
from signal_lab.synchronization.carrier_recovery import CostasLoop
from signal_lab.synchronization.rrc import apply_rrc_filter
from signal_lab.synchronization.timing_recovery import MuellerMullerTimingRecovery


class BPSKDemodulator:
    """BPSK Demodulator with RRC filtering, Costas carrier sync, and EVM calculation."""

    def __init__(self, config: DemodConfig | None = None) -> None:
        self.config = config or DemodConfig()
        self._last_metrics: dict = {}

    def configure(self, config: DemodConfig) -> None:
        self.config = config

    def process(self, samples: np.ndarray) -> DemodResult:
        if len(samples) < 16:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 1. RRC Matched Filter
        filtered = apply_rrc_filter(samples, sps=self.config.sps, alpha=self.config.rrc_alpha)

        # 2. Carrier Recovery (Order 2 for BPSK)
        costas = CostasLoop(
            order=2, damping=self.config.costas_damping, loop_bw=self.config.costas_loop_bw
        )
        carrier_sync, c_metrics = costas.process(filtered)

        # 3. Timing Recovery
        ted = MuellerMullerTimingRecovery(sps=self.config.sps)
        symbols, t_metrics = ted.process(carrier_sync)

        if len(symbols) == 0:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 4. Normalize Symbols
        scale = float(np.mean(np.abs(np.real(symbols))))
        norm_symbols = (symbols / (scale + 1e-12)).astype(np.complex64)

        # 5. Bit Slicing: Real > 0 -> 1, Real <= 0 -> 0
        real_parts = np.real(norm_symbols)
        bits = (real_parts > 0).astype(np.uint8)

        # 6. EVM Calculation: Ideal points are -1.0 and +1.0
        ideal_syms = np.where(bits == 1, 1.0 + 0j, -1.0 + 0j)
        error_vectors = norm_symbols - ideal_syms
        rms_error = float(np.sqrt(np.mean(np.abs(error_vectors) ** 2)))
        evm_percent = min(100.0, rms_error * 100.0)

        # Soft bits (LLRs proportional to real part)
        soft_bits = real_parts.astype(np.float32)

        self._last_metrics = {
            **c_metrics,
            **t_metrics,
            "evm_percent": evm_percent,
            "modulation": "BPSK",
        }

        return DemodResult(
            symbols=norm_symbols,
            hard_bits=bits,
            soft_bits=soft_bits,
            evm_percent=evm_percent,
            converged=c_metrics.get("converged", False)
            and t_metrics.get("timing_converged", False),
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics


class QPSKDemodulator:
    """QPSK Demodulator with Gray de-mapping and constellation metrics."""

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

        # 2. Carrier Recovery (Order 4 for QPSK)
        costas = CostasLoop(
            order=4, damping=self.config.costas_damping, loop_bw=self.config.costas_loop_bw
        )
        carrier_sync, c_metrics = costas.process(filtered)

        # 3. Timing Recovery
        ted = MuellerMullerTimingRecovery(sps=self.config.sps)
        symbols, t_metrics = ted.process(carrier_sync)

        if len(symbols) == 0:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        # 4. Normalize constellation power to 1.0 (ideal points at (+-1 +- 1j) / sqrt(2))
        rms_pwr = float(np.sqrt(np.mean(np.abs(symbols) ** 2)))
        norm_symbols = (symbols / (rms_pwr + 1e-12)).astype(np.complex64)

        # 5. Gray Slicing:
        # bit0: sign(I) > 0 -> 1, else 0
        # bit1: sign(Q) > 0 -> 1, else 0
        i_sign = np.real(norm_symbols) > 0
        q_sign = np.imag(norm_symbols) > 0

        bits = np.empty(len(norm_symbols) * 2, dtype=np.uint8)
        bits[0::2] = i_sign.astype(np.uint8)
        bits[1::2] = q_sign.astype(np.uint8)

        # 6. EVM Calculation
        ideal_i = np.where(i_sign, 1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0))
        ideal_q = np.where(q_sign, 1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0))
        ideal_syms = ideal_i + 1j * ideal_q
        error_vectors = norm_symbols - ideal_syms
        rms_error = float(np.sqrt(np.mean(np.abs(error_vectors) ** 2)))
        evm_percent = min(100.0, rms_error * 100.0)

        # Soft bits
        soft_bits = np.empty(len(norm_symbols) * 2, dtype=np.float32)
        soft_bits[0::2] = np.real(norm_symbols)
        soft_bits[1::2] = np.imag(norm_symbols)

        self._last_metrics = {
            **c_metrics,
            **t_metrics,
            "evm_percent": evm_percent,
            "modulation": "QPSK",
        }

        return DemodResult(
            symbols=norm_symbols,
            hard_bits=bits,
            soft_bits=soft_bits,
            evm_percent=evm_percent,
            converged=c_metrics.get("converged", False)
            and t_metrics.get("timing_converged", False),
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics


class PSK8Demodulator:
    """8PSK Demodulator with 3 bits per symbol phase de-mapping."""

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
            order=8, damping=self.config.costas_damping, loop_bw=self.config.costas_loop_bw
        )
        carrier_sync, c_metrics = costas.process(filtered)

        ted = MuellerMullerTimingRecovery(sps=self.config.sps)
        symbols, t_metrics = ted.process(carrier_sync)

        if len(symbols) == 0:
            return DemodResult(symbols=np.array([]), hard_bits=np.array([], dtype=np.uint8))

        rms_pwr = float(np.sqrt(np.mean(np.abs(symbols) ** 2)))
        norm_symbols = (symbols / (rms_pwr + 1e-12)).astype(np.complex64)

        # Map phase angles to 8 sectors
        angles = (np.angle(norm_symbols) + 2 * np.pi) % (2 * np.pi)
        sector_idx = np.round(angles / (np.pi / 4.0)).astype(int) % 8

        # Gray mapping table for 8PSK
        gray_table = np.array(
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

        bits = gray_table[sector_idx].flatten()

        ideal_angles = sector_idx * (np.pi / 4.0)
        ideal_syms = np.exp(1j * ideal_angles)
        error = norm_symbols - ideal_syms
        evm_percent = min(100.0, float(np.sqrt(np.mean(np.abs(error) ** 2))) * 100.0)

        self._last_metrics = {
            **c_metrics,
            **t_metrics,
            "evm_percent": evm_percent,
            "modulation": "8PSK",
        }

        return DemodResult(
            symbols=norm_symbols,
            hard_bits=bits,
            evm_percent=evm_percent,
            converged=c_metrics.get("converged", False),
            metrics=self._last_metrics,
        )

    def metrics(self) -> dict:
        return self._last_metrics

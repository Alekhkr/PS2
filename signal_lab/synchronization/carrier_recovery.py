"""Carrier frequency and phase recovery via Costas loop and M-th power tracking."""

from __future__ import annotations

import numpy as np


class CostasLoop:
    """Decision-directed / Costas Loop for carrier frequency and phase synchronization."""

    def __init__(
        self,
        order: int = 4,  # 2 for BPSK, 4 for QPSK/QAM, 8 for 8PSK
        damping: float = 0.707,
        loop_bw: float = 0.05,
    ) -> None:
        self.order = order
        self.damping = damping
        self.loop_bw = loop_bw
        # Loop filter gains
        denom = 1.0 + 2.0 * damping * loop_bw + loop_bw**2
        self.alpha = (4.0 * damping * loop_bw) / denom
        self.beta = (4.0 * loop_bw**2) / denom

    def process(self, samples: np.ndarray) -> tuple[np.ndarray, dict]:
        """Synchronizes carrier phase across samples.

        Returns:
            synchronized_samples: Phase-corrected samples
            metrics: Convergence metrics including residual phase error and estimated frequency offset
        """
        try:
            from signal_lab.dsp._fast_kernels import costas_loop_process
            out, metrics = costas_loop_process(
                samples.astype(np.complex64),
                self.order,
                self.damping,
                self.loop_bw
            )
            return out, metrics
        except ImportError:
            n = len(samples)
            out = np.zeros(n, dtype=np.complex64)

            phase = 0.0
            freq = 0.0
            phase_errors = np.zeros(n, dtype=np.float32)

            for i in range(n):
                s = samples[i] * np.exp(-1j * phase)
                out[i] = s

                if self.order == 2:
                    error = float(np.real(s) * np.imag(s))
                elif self.order == 4:
                    error = float(np.sign(np.real(s)) * np.imag(s) - np.sign(np.imag(s)) * np.real(s))
                elif self.order == 8:
                    angle = np.angle(s)
                    nearest_ray = np.round(angle / (np.pi / 4.0)) * (np.pi / 4.0)
                    error = float(np.sin(angle - nearest_ray))
                else:
                    error = float(np.imag(s))

                phase_errors[i] = error

                freq += self.beta * error
                phase += freq + self.alpha * error
                phase = (phase + np.pi) % (2 * np.pi) - np.pi

            steady_errors = phase_errors[n // 2 :] if n >= 20 else phase_errors
            rms_phase_error = float(np.sqrt(np.mean(steady_errors**2)))
            converged = rms_phase_error < 0.35

            metrics = {
                "converged": converged,
                "rms_phase_error_rad": rms_phase_error,
                "residual_frequency_offset": float(freq),
            }

            return out, metrics

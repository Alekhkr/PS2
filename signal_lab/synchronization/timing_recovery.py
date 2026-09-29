"""Symbol timing recovery via Gardner and Mueller-Müller Timing Error Detectors (TED)."""

from __future__ import annotations

import numpy as np


class MuellerMullerTimingRecovery:
    """Decision-directed Mueller-Müller symbol timing synchronizer."""

    def __init__(self, sps: int = 4, loop_gain: float = 0.02) -> None:
        self.sps = sps
        self.gain = loop_gain

    def process(self, samples: np.ndarray) -> tuple[np.ndarray, dict]:
        """Recovers symbol clock and downsamples to 1 sample per symbol.

        Returns:
            symbols: Array of downsampled, symbol-synchronized complex points
            metrics: Timing error metrics
        """
        try:
            from signal_lab.dsp._fast_kernels import mueller_muller_timing_recovery
            out, metrics = mueller_muller_timing_recovery(
                samples.astype(np.complex64),
                self.sps,
                self.gain
            )
            return out, dict(metrics)
        except ImportError:
            n = len(samples)
            if n < self.sps * 4:
                return samples[:: max(1, self.sps)], {"timing_converged": False}

            symbols: list[complex] = []
            timing_errors: list[float] = []

            idx = 0.0
            last_sym = 0.0 + 0j
            last_dec = 0.0 + 0j

            while int(idx) < n - 2:
                base_idx = int(idx)
                frac = idx - base_idx

                s = samples[base_idx] * (1.0 - frac) + samples[base_idx + 1] * frac
                dec = np.sign(np.real(s)) + 1j * np.sign(np.imag(s))
                symbols.append(s)

                err = float(np.real(s * np.conj(last_dec) - last_sym * np.conj(dec)))
                timing_errors.append(err)

                last_sym = s
                last_dec = dec

                idx += self.sps + self.gain * err

            sym_arr = np.array(symbols, dtype=np.complex64)
            steady_errors = (
                timing_errors[len(timing_errors) // 2 :] if len(timing_errors) > 20 else timing_errors
            )
            rms_err = float(np.sqrt(np.mean(np.array(steady_errors) ** 2))) if steady_errors else 1.0

            metrics = {
                "timing_converged": rms_err < 0.5,
                "rms_timing_error": rms_err,
                "symbol_count": len(sym_arr),
            }

            return sym_arr, metrics

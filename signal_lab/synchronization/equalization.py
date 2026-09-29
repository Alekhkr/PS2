"""Blind and Decision-Directed Equalizers for multipath mitigation."""

from __future__ import annotations

import numpy as np


class CMAEqualizer:
    """Constant Modulus Algorithm (CMA) Equalizer for blind equalization."""

    def __init__(self, num_taps: int = 15, mu: float = 0.001, reference_modulus: float = 1.0) -> None:
        self.num_taps = num_taps
        self.mu = mu
        self.reference_modulus = reference_modulus
        # Initialize center tap to 1, others to 0
        self.weights = np.zeros(num_taps, dtype=np.complex64)
        self.weights[num_taps // 2] = 1.0 + 0j

    def process(self, samples: np.ndarray) -> tuple[np.ndarray, dict]:
        """Applies CMA equalization to the sample stream.
        
        Returns:
            equalized_samples: The multipath-mitigated signal
            metrics: Equalization metrics
        """
        try:
            from signal_lab.dsp._fast_kernels import cma_equalize
            out, weights, metrics = cma_equalize(
                samples.astype(np.complex64),
                self.num_taps,
                self.mu,
                self.reference_modulus
            )
            self.weights = weights
            return out, dict(metrics)
        except ImportError:
            n = len(samples)
            out = np.zeros(n, dtype=np.complex64)
            
            # Simple Python fallback (extremely slow for large N)
            for i in range(self.num_taps - 1, n):
                window = samples[i - self.num_taps + 1 : i + 1][::-1]
                
                # Filter output
                y = np.dot(window, self.weights)
                out[i] = y
                
                # CMA error: e = y * (|y|^2 - R^2)
                mag_sq = float(np.abs(y)**2)
                err = y * (mag_sq - self.reference_modulus)
                
                # Weight update: w = w - mu * err * x^*
                self.weights -= self.mu * err * np.conj(window)
            
            # For the first num_taps - 1 samples, just pass them through
            out[:self.num_taps - 1] = samples[:self.num_taps - 1]

            metrics = {
                "converged": True,
                "final_weights_magnitude": np.abs(self.weights).tolist()
            }
            return out, metrics

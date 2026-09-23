"""Viterbi Convolutional Decoder with syndromic consistency scoring."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ViterbiResult:
    decoded_bits: np.ndarray
    syndrome_score: float  # [0.0, 1.0] (1.0 = perfect match / 0 syndrome error)
    bit_errors_corrected: int
    converged: bool


class ViterbiDecoder:
    """Standard Rate 1/2, Constraint Length K=7 Convolutional Decoder.

    Generator polynomials: G1 = 171 (octal) = 0b1111001, G2 = 133 (octal) = 0b1011011
    """

    def __init__(self, k: int = 7, polys: tuple[int, int] = (0o171, 0o133)) -> None:
        self.k = k
        self.polys = polys
        self.num_states = 1 << (k - 1)  # 64 states for K=7
        self._build_trellis()

    def _build_trellis(self) -> None:
        """Precompute state transitions and output parity bits."""
        self.next_states = np.zeros((self.num_states, 2), dtype=np.int32)
        self.outputs = np.zeros((self.num_states, 2, 2), dtype=np.uint8)

        for state in range(self.num_states):
            for bit in (0, 1):
                # Shift bit in at MSB: [bit, state_bits...]
                reg = (bit << (self.k - 1)) | state
                next_st = reg >> 1

                # Parity 0
                p0 = (reg & self.polys[0]).bit_count() % 2
                # Parity 1
                p1 = (reg & self.polys[1]).bit_count() % 2

                self.next_states[state, bit] = next_st
                self.outputs[state, bit, 0] = p0
                self.outputs[state, bit, 1] = p1

    def decode(self, coded_bits: np.ndarray) -> ViterbiResult:
        """Decodes rate 1/2 coded bits using soft/hard Viterbi path traceback."""
        n_pairs = len(coded_bits) // 2
        if n_pairs == 0:
            return ViterbiResult(
                decoded_bits=np.array([], dtype=np.uint8),
                syndrome_score=0.0,
                bit_errors_corrected=0,
                converged=False,
            )

        pairs = coded_bits[: n_pairs * 2].reshape(n_pairs, 2)

        # Path metrics array initialized with infinity except state 0
        path_metrics = np.full(self.num_states, 1e6, dtype=np.float32)
        path_metrics[0] = 0.0

        # Traceback history: [step, state] stores (prev_state, input_bit)
        history = np.zeros((n_pairs, self.num_states), dtype=np.int32)

        for t in range(n_pairs):
            rx_pair = pairs[t]
            new_metrics = np.full(self.num_states, 1e6, dtype=np.float32)

            for st in range(self.num_states):
                current_cost = path_metrics[st]
                if current_cost >= 1e5:
                    continue

                for bit in (0, 1):
                    nxt = self.next_states[st, bit]
                    out = self.outputs[st, bit]
                    # Hamming branch metric
                    bm = int(out[0] != rx_pair[0]) + int(out[1] != rx_pair[1])
                    cost = current_cost + bm

                    if cost < new_metrics[nxt]:
                        new_metrics[nxt] = cost
                        history[t, nxt] = st | (bit << 16)

            path_metrics = new_metrics

        # Traceback from minimum cost state
        best_state = int(np.argmin(path_metrics))
        total_errors = int(path_metrics[best_state])

        decoded_bits = np.zeros(n_pairs, dtype=np.uint8)
        curr_state = best_state

        for t in range(n_pairs - 1, -1, -1):
            packed = history[t, curr_state]
            prev_state = packed & 0xFFFF
            bit = (packed >> 16) & 0x1
            decoded_bits[t] = bit
            curr_state = prev_state

        # Consistency score: 1.0 - (branch_metric_errors / total_coded_bits)
        syndrome_score = float(max(0.0, 1.0 - (total_errors / (n_pairs * 2.0))))
        converged = syndrome_score > 0.70

        return ViterbiResult(
            decoded_bits=decoded_bits,
            syndrome_score=round(syndrome_score, 3),
            bit_errors_corrected=total_errors,
            converged=converged,
        )

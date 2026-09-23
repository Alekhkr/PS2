"""Low-Density Parity-Check (LDPC) Decoder and Syndrome Verifier.

Implements iterative Min-Sum message-passing algorithm on the Tanner graph
with standard IEEE 802.11n and generic parity-check matrix support.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from signal_lab.domain.enums import FECType, ValidationStatus
from signal_lab.domain.models.evidence import DecodingResult


@dataclass
class LDPCProfile:
    """Descriptor for an LDPC parity check code."""

    name: str
    codeword_length: int
    data_length: int
    rate: float
    h_matrix: np.ndarray  # (M, N) binary parity check matrix


def generate_802_11n_h_matrix(n: int = 648, rate: str = "1/2") -> np.ndarray:
    """Generates the standard IEEE 802.11n quasi-cyclic LDPC parity-check matrix.

    For N=648, sub-block size Z = 27.
    For rate 1/2: matrix size is 12x24 sub-blocks = 324 x 648.
    """
    z = n // 24  # For 648, z = 27
    if rate == "1/2":
        # Standard IEEE 802.11n Rate 1/2 prototype base matrix (12 x 24)
        # Shift values (-1 represents all-zero ZxZ block)
        base = [
            [0, -1, -1, -1, 0, 0, -1, -1, 0, -1, -1, 0, 1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [22, 0, -1, -1, 17, -1, 0, 0, 12, -1, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [6, -1, 0, -1, 10, -1, -1, -1, 24, -1, 0, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, 0, -1, -1, -1, -1, 0, -1, -1, 18, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1, -1, -1],
            [1, -1, -1, -1, -1, 0, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1, -1],
            [-1, 25, 0, -1, -1, -1, -1, -1, 20, -1, 14, -1, -1, -1, -1, -1, -1, 0, 0, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, 15, -1, 0, -1, -1, -1, -1, 14, -1, -1, -1, -1, -1, -1, 0, 0, -1, -1, -1, -1],
            [0, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, 0, 0, -1, -1, -1],
            [-1, 0, 20, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 0, -1, -1],
            [-1, -1, -1, 0, -1, -1, -1, -1, 1, -1, -1, 25, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 0, -1],
            [-1, -1, 0, -1, -1, 10, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 0],
            [-1, -1, -1, -1, 0, -1, 17, -1, -1, 0, -1, -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0],
        ]
    else:
        # Default regular (3, 6) Gallager matrix for arbitrary rate
        num_checks = n // 2
        h = np.zeros((num_checks, n), dtype=np.uint8)
        for i in range(num_checks):
            h[i, (2 * i) % n] = 1
            h[i, (2 * i + 1) % n] = 1
            h[i, (2 * i + 3) % n] = 1
        return h

    num_rows = len(base)
    num_cols = len(base[0])
    h = np.zeros((num_rows * z, num_cols * z), dtype=np.uint8)

    # Expand cyclic permutation sub-blocks
    for r in range(num_rows):
        for c in range(num_cols):
            shift = base[r][c]
            if shift >= 0:
                sub_block = np.roll(np.eye(z, dtype=np.uint8), shift, axis=1)
                h[r * z : (r + 1) * z, c * z : (c + 1) * z] = sub_block

    return h


class LDPCDecoder:
    """Iterative Min-Sum LDPC Decoder and Syndrome Evaluator."""

    def __init__(self, h_matrix: np.ndarray, max_iterations: int = 25) -> None:
        self.h = h_matrix.astype(np.uint8)
        self.num_checks, self.codeword_len = self.h.shape
        self.max_iterations = max_iterations

        # Precompute sparse check and variable adjacency lists for fast message passing
        self.check_nodes: list[np.ndarray] = [
            np.where(self.h[m, :] == 1)[0] for m in range(self.num_checks)
        ]
        self.var_nodes: list[np.ndarray] = [
            np.where(self.h[:, n] == 1)[0] for n in range(self.codeword_len)
        ]

    def compute_syndrome(self, hard_bits: np.ndarray) -> np.ndarray:
        """Computes the syndrome s = H * c^T (mod 2). Returns all-zeros for valid codeword."""
        return (self.h @ (hard_bits % 2)) % 2

    def decode_min_sum(
        self,
        llrs: np.ndarray,
    ) -> tuple[np.ndarray, bool, int, float]:
        """Runs Min-Sum LDPC belief propagation.

        Args:
            llrs: Channel log-likelihood ratios for one codeword (len == codeword_len).
                  Positive means bit 0 is more likely, negative means bit 1 is more likely.

        Returns:
            decoded_bits: Decoded binary vector (len == codeword_len).
            converged: True if syndrome is all-zero.
            iterations: Number of iterations performed.
            syndrome_ratio: Fraction of satisfied parity checks (0.0 to 1.0).
        """
        if len(llrs) != self.codeword_len:
            raise ValueError(
                f"LLR length ({len(llrs)}) does not match LDPC codeword length ({self.codeword_len})"
            )

        # Initialize variable-to-check messages Q_{n -> m} with channel LLRs
        # We store messages on edges: shape (M, N) sparsely or indexed
        # Using dictionary or dense array for small blocks:
        q_messages = np.zeros((self.num_checks, self.codeword_len), dtype=np.float32)
        for n in range(self.codeword_len):
            for m in self.var_nodes[n]:
                q_messages[m, n] = llrs[n]

        r_messages = np.zeros((self.num_checks, self.codeword_len), dtype=np.float32)

        converged = False
        iteration = 0
        decoded_bits = (llrs < 0).astype(np.uint8)

        for it in range(self.max_iterations):
            iteration = it + 1

            # 1. Check Node Update (Min-Sum approximation):
            # R_{m -> n} = prod(sign(Q)) * min(|Q|) * damping_factor
            for m in range(self.num_checks):
                vars_in_check = self.check_nodes[m]
                if len(vars_in_check) == 0:
                    continue
                q_vals = q_messages[m, vars_in_check]
                signs = np.sign(q_vals)
                signs[signs == 0] = 1.0
                abs_vals = np.abs(q_vals)

                total_sign = float(np.prod(signs))

                # For each edge, exclude itself
                for n in vars_in_check:
                    other_abs = [abs_vals[k] for k, v in enumerate(vars_in_check) if v != n]
                    min_val = min(other_abs) if other_abs else 0.0
                    edge_sign = total_sign * (1.0 if q_messages[m, n] >= 0 else -1.0)
                    r_messages[m, n] = 0.8 * edge_sign * min_val  # 0.8 damping factor

            # 2. Variable Node Update & Marginal Logits:
            total_llrs = np.copy(llrs)
            for n in range(self.codeword_len):
                checks_in_var = self.var_nodes[n]
                sum_r = float(np.sum(r_messages[checks_in_var, n]))
                total_llrs[n] += sum_r
                for m in checks_in_var:
                    q_messages[m, n] = llrs[n] + (sum_r - r_messages[m, n])

            # 3. Hard Decision & Syndrome Check
            decoded_bits = (total_llrs < 0).astype(np.uint8)
            syndrome = self.compute_syndrome(decoded_bits)
            if np.all(syndrome == 0):
                converged = True
                break

        final_syndrome = self.compute_syndrome(decoded_bits)
        satisfied_ratio = 1.0 - (float(np.sum(final_syndrome)) / self.num_checks)

        return decoded_bits, converged, iteration, satisfied_ratio

    def evaluate_hypothesis(self, soft_or_hard_bits: np.ndarray) -> DecodingResult:
        """Evaluates an LDPC decoding hypothesis on a block of bits/LLRs."""
        num_blocks = len(soft_or_hard_bits) // self.codeword_len
        if num_blocks == 0:
            return DecodingResult(
                fec_type=FECType.LDPC,
                corrected_bits=np.zeros(0, dtype=np.uint8),
                bit_error_rate_estimate=1.0,
                confidence=0.0,
                validation=ValidationStatus.REJECTED,
                notes="Bitstream too short for LDPC codeword length",
            )

        total_converged = 0
        total_satisfied = 0.0
        all_decoded = []

        for b in range(num_blocks):
            block = soft_or_hard_bits[b * self.codeword_len : (b + 1) * self.codeword_len]
            # If input is binary (0/1), convert to pseudo-LLR
            if np.issubdtype(block.dtype, np.integer) or np.all(
                np.isin(block, [0, 1, 0.0, 1.0])
            ):
                llrs = np.where(block == 0, 4.0, -4.0).astype(np.float32)
            else:
                llrs = block.astype(np.float32)

            dec_bits, conv, _, sat_ratio = self.decode_min_sum(llrs)
            if conv:
                total_converged += 1
            total_satisfied += sat_ratio
            all_decoded.append(dec_bits)

        avg_satisfied = total_satisfied / num_blocks
        conv_rate = total_converged / num_blocks
        confidence = float(0.6 * conv_rate + 0.4 * avg_satisfied)

        status = ValidationStatus.VALIDATED if conv_rate > 0.5 else (
            ValidationStatus.PARTIAL if avg_satisfied > 0.85 else ValidationStatus.REJECTED
        )

        return DecodingResult(
            fec_type=FECType.LDPC,
            corrected_bits=np.concatenate(all_decoded) if all_decoded else np.zeros(0, dtype=np.uint8),
            bit_error_rate_estimate=1.0 - avg_satisfied,
            confidence=confidence,
            validation=status,
            notes=(
                f"LDPC N={self.codeword_len}, M={self.num_checks}: "
                f"{total_converged}/{num_blocks} blocks converged ({conv_rate*100:.1f}%), "
                f"check satisfaction: {avg_satisfied*100:.1f}%"
            ),
        )

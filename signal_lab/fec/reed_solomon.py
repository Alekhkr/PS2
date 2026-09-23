"""Reed-Solomon FEC Code evaluator and syndrome calculator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class GF256:
    """Galois Field GF(2^8) arithmetic using lookup tables with primitive polynomial 0x11D."""

    def __init__(self, prim_poly: int = 0x11D) -> None:
        self.exp = [0] * 512
        self.log = [0] * 256
        x = 1
        for i in range(255):
            self.exp[i] = x
            self.exp[i + 255] = x
            self.log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= prim_poly

    def mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return self.exp[self.log[a] + self.log[b]]


@dataclass
class RSResult:
    syndrome_score: float
    zero_syndromes_ratio: float
    is_valid_codeword: bool


class ReedSolomonEvaluator:
    """Evaluates Reed-Solomon RS(255, 223) or RS(255, 239) hypotheses over byte streams."""

    def __init__(self, n: int = 255, k: int = 223) -> None:
        self.n = n
        self.k = k
        self.nroots = n - k
        self.gf = GF256()

    def evaluate(self, byte_data: np.ndarray) -> RSResult:
        """Evaluates syndrome polynomial S_i = sum(byte_data[j] * alpha^(i*j))."""
        if len(byte_data) < self.nroots:
            return RSResult(syndrome_score=0.0, zero_syndromes_ratio=0.0, is_valid_codeword=False)

        eval_block = byte_data[: self.n] if len(byte_data) >= self.n else byte_data
        zero_syndromes = 0

        for root in range(1, self.nroots + 1):
            s = 0
            # S_root = sum_{j=0}^{N-1} c_j * alpha^(root*j)
            alpha_root = self.gf.exp[root]
            for byte_val in eval_block:
                s = self.gf.mul(s, alpha_root) ^ int(byte_val)
            if s == 0:
                zero_syndromes += 1

        ratio = zero_syndromes / float(self.nroots)
        is_valid = ratio > 0.95

        return RSResult(
            syndrome_score=round(ratio, 3),
            zero_syndromes_ratio=round(ratio, 3),
            is_valid_codeword=is_valid,
        )

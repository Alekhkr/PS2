"""Forward Error Correction (FEC) hypothesis testing engine."""

from __future__ import annotations

import numpy as np

from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import FECCandidate
from signal_lab.fec.reed_solomon import ReedSolomonEvaluator
from signal_lab.fec.viterbi import ViterbiDecoder


def evaluate_fec_hypotheses(bits: np.ndarray) -> list[FECCandidate]:
    """Tests candidate FEC codes against recovered bits and returns scored hypotheses."""
    candidates: list[FECCandidate] = []
    if len(bits) < 32:
        return candidates

    # 1. Test Viterbi Convolutional K=7, R=1/2
    viterbi = ViterbiDecoder(k=7)
    v_res = viterbi.decode(bits)

    v_status = (
        ValidationStatus.VALIDATED
        if v_res.syndrome_score > 0.85
        else (
            ValidationStatus.PARTIAL if v_res.syndrome_score > 0.65 else ValidationStatus.UNVERIFIED
        )
    )

    cand_viterbi = FECCandidate(
        type="viterbi_k7_r12",
        parameters={"k": 7, "rate": "1/2", "polys": ["171", "133"]},
        syndrome_score=v_res.syndrome_score,
        corrections_count=v_res.bit_errors_corrected,
        status=v_status,
    )
    candidates.append(cand_viterbi)

    # 2. Test Reed-Solomon RS(255, 223)
    if len(bits) >= 8 * 16:
        n_bytes = len(bits) // 8
        byte_arr = np.packbits(bits[: n_bytes * 8])
        rs = ReedSolomonEvaluator(n=255, k=223)
        rs_res = rs.evaluate(byte_arr)

        rs_status = (
            ValidationStatus.VALIDATED
            if rs_res.is_valid_codeword
            else (
                ValidationStatus.PARTIAL
                if rs_res.syndrome_score > 0.4
                else ValidationStatus.UNVERIFIED
            )
        )

        cand_rs = FECCandidate(
            type="reed_solomon_255_223",
            parameters={"n": 255, "k": 223, "roots": 32},
            syndrome_score=rs_res.syndrome_score,
            status=rs_status,
        )
        candidates.append(cand_rs)

    # Sort descending by syndrome score
    candidates.sort(key=lambda c: c.syndrome_score, reverse=True)
    return candidates


__all__ = ["ReedSolomonEvaluator", "ViterbiDecoder", "evaluate_fec_hypotheses"]

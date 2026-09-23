"""Concatenated FEC Decoding Pipeline (Inner Viterbi + Outer Reed-Solomon).

Standard physical layer architecture in space communications (CCSDS), DVB,
and high-reliability terrestrial HF links.
"""

from __future__ import annotations

import numpy as np

from signal_lab.domain.enums import FECType, ValidationStatus
from signal_lab.domain.models.evidence import DecodingResult
from signal_lab.fec.reed_solomon import ReedSolomonEvaluator
from signal_lab.fec.viterbi import ViterbiDecoder
from signal_lab.interleaving.interleaver import deinterleave_block


class ConcatenatedFECPipeline:
    """Joint decoding engine for Inner Convolutional (Viterbi) + De-interleaver + Outer Reed-Solomon."""

    def __init__(
        self,
        viterbi_decoder: ViterbiDecoder | None = None,
        rs_evaluator: ReedSolomonEvaluator | None = None,
        interleaver_rows: int = 16,
        interleaver_cols: int = 16,
    ) -> None:
        self.viterbi = viterbi_decoder or ViterbiDecoder()
        self.rs = rs_evaluator or ReedSolomonEvaluator(n=255, k=223)
        self.interleaver_rows = interleaver_rows
        self.interleaver_cols = interleaver_cols

    def decode_and_evaluate(
        self,
        soft_llrs: np.ndarray,
        use_deinterleaver: bool = True,
    ) -> DecodingResult:
        """Runs the joint concatenated decoding chain:

        soft_llrs -> Viterbi Inner -> (Optional Deinterleaver) -> RS Outer.
        """
        if len(soft_llrs) < 64:
            return DecodingResult(
                fec_type=FECType.CONCATENATED,
                corrected_bits=np.zeros(0, dtype=np.uint8),
                bit_error_rate_estimate=1.0,
                confidence=0.0,
                validation=ValidationStatus.REJECTED,
                notes="LLR sequence too short for concatenated decoding",
            )

        # 1. Inner Viterbi Decoding
        hard_bits = (soft_llrs < 0).astype(np.uint8)
        viterbi_res = self.viterbi.decode(hard_bits)
        inner_bits = viterbi_res.decoded_bits

        if len(inner_bits) == 0:
            return DecodingResult(
                fec_type=FECType.CONCATENATED,
                corrected_bits=np.zeros(0, dtype=np.uint8),
                bit_error_rate_estimate=1.0,
                confidence=0.0,
                validation=ValidationStatus.REJECTED,
                notes="Inner Viterbi decoder produced 0 bits",
            )

        # 2. De-interleaving (if requested)
        if use_deinterleaver:
            deint_bits = deinterleave_block(
                inner_bits, rows=self.interleaver_rows, cols=self.interleaver_cols
            )
        else:
            deint_bits = inner_bits

        # 3. Pack bits to bytes for Outer Reed-Solomon evaluation
        num_bytes = len(deint_bits) // 8
        if num_bytes == 0:
            return DecodingResult(
                fec_type=FECType.CONCATENATED,
                corrected_bits=deint_bits,
                bit_error_rate_estimate=viterbi_res.bit_error_rate_estimate,
                confidence=viterbi_res.confidence * 0.5,
                validation=ValidationStatus.PARTIAL,
                notes="Deinterleaved stream too short for Reed-Solomon byte frame",
            )

        truncated_bits = deint_bits[: num_bytes * 8]
        bit_matrix = truncated_bits.reshape(num_bytes, 8)
        # MSB first bit packing
        powers = 2 ** np.arange(7, -1, -1, dtype=np.uint8)
        byte_data = np.sum(bit_matrix * powers, axis=1, dtype=np.uint8)

        # 4. Outer Reed-Solomon Evaluation
        rs_res = self.rs.evaluate(byte_data)

        # 5. Combined Confidence Fusion
        # High confidence when both Viterbi path metric is clean AND RS syndrome ratio is high
        viterbi_score = viterbi_res.syndrome_score
        rs_score = rs_res.zero_syndromes_ratio

        combined_conf = float(0.5 * viterbi_score + 0.5 * rs_score)
        if rs_res.is_valid_codeword:
            status = ValidationStatus.VALIDATED
            combined_conf = max(combined_conf, 0.95)
        elif combined_conf > 0.7:
            status = ValidationStatus.PARTIAL
        else:
            status = ValidationStatus.REJECTED

        return DecodingResult(
            fec_type=FECType.CONCATENATED,
            corrected_bits=truncated_bits,
            bit_error_rate_estimate=float(1.0 - rs_score),
            confidence=combined_conf,
            validation=status,
            notes=(
                f"Concatenated Inner Viterbi (conf={viterbi_score:.2f}) + "
                f"Outer RS({self.rs.n},{self.rs.k}) (zero_syndrome={rs_score*100:.1f}%)"
            ),
        )

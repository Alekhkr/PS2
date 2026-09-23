"""Evidence and Confidence Aggregation Engine."""

from __future__ import annotations

from signal_lab.demodulation.base import DemodResult
from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import FECCandidate, ModulationCandidate, ParameterEvidence


class EvidenceEngine:
    """Aggregates multi-source evidence across DSP, classification, synchronization, and decoding."""

    @staticmethod
    def aggregate_evidence(
        parameters: list[ParameterEvidence],
        modulation_candidates: list[ModulationCandidate],
        demod_result: DemodResult | None = None,
        fec_candidates: list[FECCandidate] | None = None,
    ) -> tuple[ModulationCandidate, float, list[str]]:
        """Computes confidence-ranked result with supporting explanation trail.

        Returns:
            top_candidate: The validated or most likely modulation hypothesis
            final_confidence: Calibrated overall confidence score [0.0, 1.0]
            evidence_summary: Human-readable audit points explaining the decision
        """
        if not modulation_candidates:
            fallback = ModulationCandidate(
                name="UNKNOWN",
                score=0.0,
                evidence=["Insufficient signal data to classify"],
                validation=ValidationStatus.UNVERIFIED,
            )
            return fallback, 0.0, fallback.evidence

        top_cand = modulation_candidates[0]
        evidence_points: list[str] = list(top_cand.evidence)

        # Baseline score from modulation classifier
        score = top_cand.score

        # 1. Integrate Demodulation & Synchronization Metrics
        if demod_result is not None:
            if demod_result.converged:
                score = min(0.98, score + 0.08)
                evidence_points.append(
                    f"Carrier & timing synchronization converged (EVM: {demod_result.evm_percent:.1f}%)"
                )
                top_cand.validation = ValidationStatus.PARTIAL
            elif demod_result.evm_percent > 60.0:
                score = max(0.20, score - 0.15)
                evidence_points.append(
                    f"Poor EVM fit ({demod_result.evm_percent:.1f}%) under hypothesis"
                )

        # 2. Integrate Forward Error Correction (FEC) Validation
        if fec_candidates and len(fec_candidates) > 0:
            top_fec = fec_candidates[0]
            if top_fec.syndrome_score > 0.85:
                score = min(0.99, score + 0.10)
                evidence_points.append(
                    f"Downstream FEC ({top_fec.type}) validated with syndrome score {top_fec.syndrome_score:.2f}"
                )
                top_cand.validation = ValidationStatus.VALIDATED
            elif top_fec.syndrome_score > 0.65:
                evidence_points.append(
                    f"Partial FEC agreement ({top_fec.type}: score {top_fec.syndrome_score:.2f})"
                )

        # 3. Integrate Measured DSP Parameters
        for p in parameters:
            if p.name == "snr" and isinstance(p.value, (int, float)):
                if p.value < 6.0:
                    evidence_points.append(
                        f"Low SNR ({p.value:.1f} dB) limits classification certainty"
                    )
                    score *= 0.90
                else:
                    evidence_points.append(f"Sufficient SNR ({p.value:.1f} dB)")

        final_conf = round(float(np_clip(score, 0.05, 0.99)), 3)
        top_cand.score = final_conf
        top_cand.evidence = evidence_points

        return top_cand, final_conf, evidence_points


def np_clip(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))

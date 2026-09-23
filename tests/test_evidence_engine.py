"""Unit tests for the Evidence and Confidence Engine."""

import numpy as np

from signal_lab.demodulation.base import DemodResult
from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import FECCandidate, ModulationCandidate, ParameterEvidence
from signal_lab.services.evidence_engine import EvidenceEngine


def test_evidence_aggregation_with_fec_validation() -> None:
    """Verify evidence engine promotes candidate to VALIDATED when downstream FEC converges."""
    param = ParameterEvidence(name="snr", value=18.5, confidence=0.95)
    cand = ModulationCandidate(name="QPSK", score=0.85, evidence=["4 phase clusters"])
    demod = DemodResult(
        symbols=np.array([]),
        hard_bits=np.array([]),
        evm_percent=8.5,
        converged=True,
    )
    fec = FECCandidate(type="viterbi_k7_r12", syndrome_score=0.96)

    final_cand, conf, evidence = EvidenceEngine.aggregate_evidence(
        parameters=[param],
        modulation_candidates=[cand],
        demod_result=demod,
        fec_candidates=[fec],
    )

    assert final_cand.name == "QPSK"
    assert conf > 0.90
    assert final_cand.validation == ValidationStatus.VALIDATED
    assert any("Downstream FEC" in e for e in evidence)


def test_evidence_aggregation_low_snr_penalty() -> None:
    """Verify evidence engine lowers confidence when SNR is deficient."""
    param = ParameterEvidence(name="snr", value=3.2, confidence=0.5)
    cand = ModulationCandidate(name="BPSK", score=0.80, evidence=["Constant envelope"])

    _final_cand, conf, evidence = EvidenceEngine.aggregate_evidence(
        parameters=[param],
        modulation_candidates=[cand],
    )

    assert conf < 0.80
    assert any("Low SNR" in e for e in evidence)

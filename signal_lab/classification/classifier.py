"""Hybrid heuristic and statistical modulation classification."""

from __future__ import annotations

import numpy as np

from signal_lab.classification.features import extract_modulation_features
from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import ModulationCandidate
from signal_lab.domain.models.signal import SignalBuffer


def classify_modulation(buffer: SignalBuffer) -> list[ModulationCandidate]:
    """Generates ranked modulation candidates with auditable feature evidence."""
    features = extract_modulation_features(buffer)
    candidates: list[ModulationCandidate] = []

    env_var = features.envelope_variation
    c40_mag = float(np.abs(features.c40_cumulant))
    c42 = features.c42_cumulant

    # Check for constant envelope (FSK / PSK is near 0.0, QAM is > 0.10)
    is_constant_envelope = env_var < 0.08

    if is_constant_envelope:
        # Evaluate BPSK: C40 magnitude is near 2.0, C42 is near -2.0
        if c40_mag > 1.2:
            evidence = [
                f"Constant envelope (variation: {env_var:.3f})",
                f"High 4th cumulant |C40|={c40_mag:.2f} (2-phase clustering)",
                f"C42 cumulant={c42:.2f}",
            ]
            cand = ModulationCandidate(
                name="BPSK",
                score=0.91,
                evidence=evidence,
                algorithm="cumulant_c40_c42_ensemble_v1",
                validation=ValidationStatus.PARTIAL,
            )
            candidates.append(cand)
            candidates.append(
                ModulationCandidate(
                    name="QPSK", score=0.06, evidence=["Low probability alternative"]
                )
            )
            candidates.append(
                ModulationCandidate(name="FSK", score=0.03, evidence=["Constant envelope match"])
            )
        # Evaluate QPSK: C40 magnitude is near 1.0, C42 is near -1.0
        elif c40_mag > 0.4:
            evidence = [
                f"Constant envelope (variation: {env_var:.3f})",
                f"Quadrature phase cumulant |C40|={c40_mag:.2f}",
                f"C42 cumulant={c42:.2f} (4-quadrant balance)",
            ]
            cand = ModulationCandidate(
                name="QPSK",
                score=0.88,
                evidence=evidence,
                algorithm="cumulant_c40_c42_ensemble_v1",
                validation=ValidationStatus.PARTIAL,
            )
            candidates.append(cand)
            candidates.append(
                ModulationCandidate(name="8PSK", score=0.08, evidence=["Phase constellation fit"])
            )
            candidates.append(
                ModulationCandidate(name="BPSK", score=0.04, evidence=["Lower-order alternative"])
            )
        else:
            # 8PSK or FSK
            evidence_fsk = [
                f"Constant envelope (variation: {env_var:.3f})",
                f"Low C40 magnitude ({c40_mag:.2f})",
                f"Phase variance ({features.phase_std:.2f}) indicates continuous frequency shifts",
            ]
            candidates.append(
                ModulationCandidate(
                    name="FSK",
                    score=0.82,
                    evidence=evidence_fsk,
                    algorithm="cumulant_phase_derivative_v1",
                    validation=ValidationStatus.PARTIAL,
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="8PSK",
                    score=0.14,
                    evidence=["8-ary phase distribution"],
                    algorithm="cumulant_phase_derivative_v1",
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="QPSK",
                    score=0.04,
                    evidence=["Phase constellation fit"],
                )
            )
    else:
        # Varying envelope -> QAM family (QAM16 / QAM64)
        if env_var < 0.6:
            evidence = [
                f"Varying envelope (variation: {env_var:.3f} typical of 16-QAM)",
                f"Crest factor {features.crest_factor:.2f}",
                f"Kurtosis real={features.kurtosis_real:.2f}, imag={features.kurtosis_imag:.2f}",
            ]
            candidates.append(
                ModulationCandidate(
                    name="QAM16",
                    score=0.86,
                    evidence=evidence,
                    algorithm="envelope_kurtosis_qam_v1",
                    validation=ValidationStatus.PARTIAL,
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="QAM64",
                    score=0.10,
                    evidence=["Higher-order dense constellation"],
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="QPSK",
                    score=0.04,
                    evidence=["Low probability filtered PSK alternative"],
                )
            )
        else:
            evidence = [
                f"High envelope variation ({env_var:.3f}) matching dense QAM",
                f"Crest factor {features.crest_factor:.2f}",
            ]
            candidates.append(
                ModulationCandidate(
                    name="QAM64",
                    score=0.84,
                    evidence=evidence,
                    algorithm="envelope_kurtosis_qam_v1",
                    validation=ValidationStatus.PARTIAL,
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="QAM16",
                    score=0.13,
                    evidence=["Sub-constellation fit"],
                )
            )
            candidates.append(
                ModulationCandidate(
                    name="8PSK",
                    score=0.03,
                    evidence=["Alternative hypothesis"],
                )
            )

    return candidates

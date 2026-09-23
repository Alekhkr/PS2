"""Provenance and evidence data models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from signal_lab.domain.enums import EvidenceSource, ValidationStatus


@dataclass
class ParameterEvidence:
    """Carries full provenance, algorithm identifier, and confidence for any parameter.

    Every inferred parameter must be auditable and explainable rather than
    presented as an unexplained ground truth.
    """

    name: str
    value: object
    unit: str | None = None
    source: EvidenceSource | str = EvidenceSource.ESTIMATOR
    algorithm: str | None = None
    confidence: float = 1.0  # Normalized [0.0, 1.0]
    assumptions: list[str] = field(default_factory=list)
    validation: ValidationStatus | str = ValidationStatus.UNVERIFIED
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "source": str(self.source.value if hasattr(self.source, "value") else self.source),
            "algorithm": self.algorithm,
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "validation": str(
                self.validation.value if hasattr(self.validation, "value") else self.validation
            ),
        }


@dataclass
class ModulationCandidate:
    """Hypothesis for signal modulation family with confidence and supporting features."""

    name: str  # e.g., "QPSK", "BPSK", "FSK"
    score: float  # Confidence [0.0, 1.0]
    evidence: list[str] = field(default_factory=list)
    algorithm: str = "dsp_feature_ensemble"
    validation: ValidationStatus | str = ValidationStatus.PARTIAL
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class InterleaverCandidate:
    """Hypothesis for interleaver structure."""

    type: str  # block, convolutional, diagonal, etc.
    parameters: dict = field(default_factory=dict)
    score: float = 0.0
    status: ValidationStatus | str = ValidationStatus.UNVERIFIED
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class FECCandidate:
    """Hypothesis for forward error correction scheme."""

    type: str  # viterbi, reed_solomon, ldpc, etc.
    parameters: dict = field(default_factory=dict)
    syndrome_score: float = 0.0
    corrections_count: int = 0
    status: ValidationStatus | str = ValidationStatus.UNVERIFIED
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

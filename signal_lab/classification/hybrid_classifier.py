"""Hybrid Modulation Classifier combining Deep 1D-CNN (RadioMod-R16) with Deterministic DSP Cumulants.

Produces explainable, confidence-ranked modulation hypotheses with full provenance.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from signal_lab.classification.features import extract_modulation_features
from signal_lab.domain.enums import ModulationFamily, ValidationStatus
from signal_lab.domain.models.evidence import ModulationCandidate
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.ml.model import MODULATION_CLASSES_R16, ModulationResNet1D

# Map R16 string labels to domain ModulationFamily enums where applicable
R16_TO_DOMAIN_MAP: dict[str, ModulationFamily] = {
    "BPSK": ModulationFamily.BPSK,
    "QPSK": ModulationFamily.QPSK,
    "8PSK": ModulationFamily.PSK8,
    "16QAM": ModulationFamily.QAM16,
    "64QAM": ModulationFamily.QAM64,
    "2FSK": ModulationFamily.FSK,
    "4FSK": ModulationFamily.FSK,
    "MSK": ModulationFamily.FSK,
    "CPFSK": ModulationFamily.FSK,
    "GMSK": ModulationFamily.FSK,
    "GFSK": ModulationFamily.FSK,
}


class HybridModulationClassifier:
    """Fuses deep 1D ResNet predictions with deterministic cumulants and envelope properties."""

    def __init__(
        self,
        weights_path: str | Path | None = None,
        device_str: str = "cpu",
    ) -> None:
        self.device = torch.device(device_str)
        self.classes = MODULATION_CLASSES_R16
        self._model: ModulationResNet1D | None = None

        # Resolve weights path
        p = (
            Path(weights_path)
            if weights_path
            else Path(__file__).parent.parent / "ml" / "weights" / "modulation_r16_resnet.pt"
        )
        if p.exists():
            try:
                self._model = ModulationResNet1D(num_classes=len(self.classes)).to(self.device)
                state = torch.load(p, map_location=self.device, weights_only=True)
                self._model.load_state_dict(state)
                self._model.eval()
            except (RuntimeError, ValueError, OSError):
                self._model = None

    @property
    def has_neural_model(self) -> bool:
        return self._model is not None

    def classify(
        self,
        buffer: SignalBuffer,
        top_k: int = 5,
        max_windows: int = 16,
    ) -> list[ModulationCandidate]:
        """Runs the hybrid classification pipeline on the signal buffer."""
        samples = buffer.samples
        if len(samples) < 64:
            return [
                ModulationCandidate(
                    name="UNKNOWN",
                    score=0.0,
                    evidence=["Buffer has fewer than 64 samples"],
                    validation=ValidationStatus.REJECTED,
                )
            ]

        # 1. Deterministic Cumulants & Envelope Features
        feat = extract_modulation_features(buffer)
        env_var = feat.envelope_variation
        abs_c40 = float(np.abs(feat.c40_cumulant))
        abs_c42 = float(np.abs(feat.c42_cumulant))

        dsp_evidence = [
            f"Envelope Variance σ²={env_var:.3f}",
            f"|C₄₀|={abs_c40:.2f}, |C₄₂|={abs_c42:.2f}",
        ]

        # Constant envelope indicator (PSK / FSK typically < 0.08)
        is_constant_envelope = env_var < 0.08
        if is_constant_envelope:
            dsp_evidence.append("Constant envelope (consistent with PSK/FSK/MSK)")
        else:
            dsp_evidence.append("Multi-amplitude envelope (consistent with QAM/APSK)")

        # 2. Deep Learning 1D-CNN Inference
        neural_probs: np.ndarray | None = None
        if self._model is not None and len(samples) >= 512:
            # Segment into non-overlapping 512-sample windows
            num_windows = min(max_windows, len(samples) // 512)
            windows_raw = samples[: num_windows * 512].reshape(num_windows, 512)

            # Normalization per window
            mags = np.sqrt(np.mean(np.abs(windows_raw) ** 2, axis=1, keepdims=True)) + 1e-12
            windows_norm = windows_raw / mags

            # Reshape to (B, 2, 512): channel 0 = I, channel 1 = Q
            x_tensor = np.empty((num_windows, 2, 512), dtype=np.float32)
            x_tensor[:, 0, :] = np.real(windows_norm)
            x_tensor[:, 1, :] = np.imag(windows_norm)

            with torch.no_grad():
                tensor_input = torch.from_numpy(x_tensor).to(self.device)
                probs = self._model.predict_probabilities(tensor_input).cpu().numpy()
                neural_probs = np.mean(probs, axis=0)  # Average across windows

        # 3. Decision Fusion
        candidates: list[ModulationCandidate] = []

        if neural_probs is not None:
            # Rank top-k predictions from the neural model and validate with DSP features
            top_indices = np.argsort(neural_probs)[::-1]
            for idx in top_indices[:top_k]:
                cls_name = self.classes[idx]
                raw_prob = float(neural_probs[idx])
                reasons = list(dsp_evidence)
                reasons.append(f"1D-ResNet neural probability: {raw_prob * 100:.1f}%")

                score = raw_prob

                # Consistency checks between neural model and physical DSP
                if "QAM" in cls_name or "APSK" in cls_name:
                    if is_constant_envelope:
                        # Penalty: constant envelope contradicts QAM
                        score *= 0.3
                        reasons.append("Discrepancy: Constant envelope contradicts QAM/APSK")
                    else:
                        score = min(0.99, score * 1.15)
                elif "PSK" in cls_name or "FSK" in cls_name or "MSK" in cls_name:
                    if is_constant_envelope:
                        score = min(0.99, score * 1.15)
                    else:
                        score *= 0.6
                        reasons.append("Discrepancy: Non-constant envelope contradicts PSK/FSK")

                status = (
                    ValidationStatus.VALIDATED
                    if score > 0.8
                    else (ValidationStatus.PARTIAL if score > 0.4 else ValidationStatus.UNVERIFIED)
                )

                candidates.append(
                    ModulationCandidate(
                        name=cls_name,
                        score=float(score),
                        evidence=reasons,
                        algorithm="hybrid_resnet1d_cumulant_fusion",
                        validation=status,
                    )
                )
        else:
            # Deterministic fallback when neural model is not available
            from signal_lab.classification.classifier import ModulationClassifier

            candidates = ModulationClassifier.classify(buffer)

        # Re-sort candidates by calibrated score
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:top_k]

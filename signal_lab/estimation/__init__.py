"""Unified parameter estimation interface."""

from __future__ import annotations

from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.estimation.bandwidth import estimate_occupied_bandwidth
from signal_lab.estimation.carrier import estimate_carrier_frequency
from signal_lab.estimation.detector import detect_signal_regions, estimate_noise_floor_db
from signal_lab.estimation.snr import estimate_snr
from signal_lab.estimation.symbol_rate import estimate_symbol_rate


def analyze_signal_parameters(
    buffer: SignalBuffer,
) -> tuple[list[SignalSegment], list[ParameterEvidence]]:
    """Runs automated signal detection and comprehensive parameter estimation."""
    evidence_list: list[ParameterEvidence] = []

    # 1. Burst Detection
    segments = detect_signal_regions(buffer)

    # 2. Carrier Frequency
    carrier_ev = estimate_carrier_frequency(buffer)
    evidence_list.append(carrier_ev)

    # 3. Occupied Bandwidth
    obw_ev = estimate_occupied_bandwidth(buffer)
    evidence_list.append(obw_ev)

    # 4. SNR
    snr_ev = estimate_snr(buffer)
    evidence_list.append(snr_ev)

    # 5. Symbol Rate Candidates
    sym_rates = estimate_symbol_rate(buffer, n_candidates=2)
    evidence_list.extend(sym_rates)

    return segments, evidence_list


__all__ = [
    "analyze_signal_parameters",
    "detect_signal_regions",
    "estimate_carrier_frequency",
    "estimate_noise_floor_db",
    "estimate_occupied_bandwidth",
    "estimate_snr",
    "estimate_symbol_rate",
]

"""Demodulation engine exports and factory interface."""

from __future__ import annotations

from signal_lab.demodulation.base import DemodConfig, DemodResult, Demodulator
from signal_lab.demodulation.fsk import FSKDemodulator
from signal_lab.demodulation.psk import BPSKDemodulator, PSK8Demodulator, QPSKDemodulator
from signal_lab.demodulation.qam import QAM16Demodulator, QAM64Demodulator
from signal_lab.domain.models.signal import SignalBuffer

DEMODULATOR_MAP: dict[str, type] = {
    "FSK": FSKDemodulator,
    "BPSK": BPSKDemodulator,
    "QPSK": QPSKDemodulator,
    "8PSK": PSK8Demodulator,
    "QAM16": QAM16Demodulator,
    "16QAM": QAM16Demodulator,
    "QAM64": QAM64Demodulator,
    "64QAM": QAM64Demodulator,
}


def get_demodulator(modulation: str, config: DemodConfig | None = None) -> Demodulator:
    """Instantiate appropriate Demodulator for the modulation family."""
    mod_key = modulation.upper().replace("-", "")
    cls = DEMODULATOR_MAP.get(mod_key, QPSKDemodulator)
    return cls(config=config)


def demodulate_signal(
    buffer: SignalBuffer,
    modulation: str,
    sps: int = 4,
    rrc_alpha: float = 0.35,
) -> DemodResult:
    """Convenience function to demodulate complex samples from a SignalBuffer."""
    config = DemodConfig(sps=sps, rrc_alpha=rrc_alpha)
    demod = get_demodulator(modulation, config=config)
    return demod.process(buffer.samples)


__all__ = [
    "BPSKDemodulator",
    "DemodConfig",
    "DemodResult",
    "Demodulator",
    "FSKDemodulator",
    "PSK8Demodulator",
    "QAM16Demodulator",
    "QAM64Demodulator",
    "QPSKDemodulator",
    "demodulate_signal",
    "get_demodulator",
]

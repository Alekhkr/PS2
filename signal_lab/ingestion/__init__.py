"""Unified signal ingestion interface."""

from __future__ import annotations

from pathlib import Path

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.ingestion.iq_parser import IQFormatConfig, RawIQParser
from signal_lab.ingestion.wav_parser import WavParser


def load_signal_file(
    filepath: str | Path,
    iq_config: IQFormatConfig | None = None,
    center_frequency_hz: float | None = None,
) -> SignalBuffer:
    """Intelligently load a WAV or IQ capture into a canonical SignalBuffer."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext in (".wav", ".wave"):
        return WavParser.parse_file(
            path,
            center_frequency_hz=center_frequency_hz,
        )
    else:
        # Defaults to binary IQ
        cfg = iq_config or IQFormatConfig()
        if center_frequency_hz is not None:
            cfg.center_frequency_hz = center_frequency_hz
        return RawIQParser.parse_file(path, config=cfg)


__all__ = ["IQFormatConfig", "RawIQParser", "WavParser", "load_signal_file"]

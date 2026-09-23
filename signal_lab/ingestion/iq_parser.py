"""Configurable Raw and Binary IQ capture parser."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from signal_lab.domain.enums import ByteOrder, SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer


@dataclass
class IQFormatConfig:
    """Configuration descriptor for arbitrary binary IQ streams."""

    sample_format: SampleFormat = SampleFormat.CF32
    byte_order: ByteOrder = ByteOrder.LITTLE_ENDIAN
    sample_rate_hz: float | None = None
    center_frequency_hz: float | None = None
    scale_auto: bool = True
    manual_scale: float = 1.0
    start_time: float | None = 0.0


class RawIQParser:
    """Parses arbitrary binary IQ files into canonical complex64 SignalBuffers."""

    @staticmethod
    def parse_file(
        filepath: str | Path,
        config: IQFormatConfig | None = None,
        max_samples: int | None = None,
    ) -> SignalBuffer:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"IQ file not found: {path}")

        cfg = config or IQFormatConfig()
        endian_prefix = "<" if cfg.byte_order == ByteOrder.LITTLE_ENDIAN else ">"

        # Determine numpy dtype
        if cfg.sample_format == SampleFormat.CF32:
            dtype = np.dtype(f"{endian_prefix}f4")
            normalize_factor = 1.0
        elif cfg.sample_format == SampleFormat.CF64:
            dtype = np.dtype(f"{endian_prefix}f8")
            normalize_factor = 1.0
        elif cfg.sample_format == SampleFormat.CI16:
            dtype = np.dtype(f"{endian_prefix}i2")
            normalize_factor = 32768.0
        elif cfg.sample_format == SampleFormat.CI8:
            dtype = np.dtype("i1")
            normalize_factor = 128.0
        elif cfg.sample_format == SampleFormat.CI32:
            dtype = np.dtype(f"{endian_prefix}i4")
            normalize_factor = 2147483648.0
        else:
            raise ValueError(f"Unsupported sample format: {cfg.sample_format}")

        count = (max_samples * 2) if max_samples else -1
        raw_arr = np.fromfile(path, dtype=dtype, count=count)

        if len(raw_arr) % 2 != 0:
            # Truncate partial sample pair
            raw_arr = raw_arr[:-1]

        # Interleaved [I0, Q0, I1, Q1, ...] -> complex64
        i_samples = raw_arr[0::2].astype(np.float32) / normalize_factor
        q_samples = raw_arr[1::2].astype(np.float32) / normalize_factor
        complex_samples = (i_samples + 1j * q_samples).astype(np.complex64)

        if cfg.scale_auto and len(complex_samples) > 0:
            peak = float(np.max(np.abs(complex_samples)))
            if peak > 1e-9:
                complex_samples = (complex_samples / peak).astype(np.complex64)
        elif not cfg.scale_auto and cfg.manual_scale != 1.0:
            complex_samples = (complex_samples * cfg.manual_scale).astype(np.complex64)

        metadata = {
            "source_path": str(path),
            "file_size_bytes": path.stat().st_size,
            "raw_dtype": str(dtype),
            "sample_format": cfg.sample_format.value,
        }

        return SignalBuffer(
            samples=complex_samples,
            sample_rate_hz=cfg.sample_rate_hz,
            center_frequency_hz=cfg.center_frequency_hz,
            channel_count=1,
            source_format=SourceFormat.IQ,
            sample_format=cfg.sample_format,
            start_time=cfg.start_time,
            metadata=metadata,
        )

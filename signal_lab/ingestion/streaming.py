"""High-throughput Memory-Mapped Streaming Signal Buffer.

Enables zero-copy, instantaneous exploration of multi-hundred-megabyte and gigabyte
raw IQ captures (such as 320 MB 802.11 WLAN captures) with bounded RAM usage (< 100 MB).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from signal_lab.domain.enums import ByteOrder, SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.ingestion.iq_parser import IQFormatConfig


@dataclass
class DecimatedOverview:
    """Pre-computed min/max/RMS decimation pyramid for fast visual navigation."""

    decimation_factor: int
    min_envelope: np.ndarray
    max_envelope: np.ndarray
    power_db: np.ndarray


class StreamingSignalBuffer:
    """Memory-mapped streaming signal buffer backed by disk without loading all samples into RAM.

    Provides on-demand chunk access, slicing into standard SignalBuffer objects,
    and fast multi-resolution decimation caches for UI rendering.
    """

    def __init__(
        self,
        filepath: str | Path,
        config: IQFormatConfig | None = None,
    ) -> None:
        self.path = Path(filepath)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

        self.config = config or IQFormatConfig()
        self.sample_rate_hz: float | None = self.config.sample_rate_hz
        self.center_frequency_hz: float | None = self.config.center_frequency_hz
        self.sample_format: SampleFormat = self.config.sample_format
        self.byte_order: ByteOrder = self.config.byte_order

        # Determine numpy dtype and scalar normalization factor
        endian = "<" if self.byte_order == ByteOrder.LITTLE_ENDIAN else ">"
        if self.sample_format == SampleFormat.CI16:
            self._raw_dtype = np.dtype(f"{endian}i2")
            self._norm_factor = 32768.0
        elif self.sample_format == SampleFormat.CF32:
            self._raw_dtype = np.dtype(f"{endian}f4")
            self._norm_factor = 1.0
        elif self.sample_format == SampleFormat.CF64:
            self._raw_dtype = np.dtype(f"{endian}f8")
            self._norm_factor = 1.0
        elif self.sample_format == SampleFormat.CI8:
            self._raw_dtype = np.dtype("i1")
            self._norm_factor = 128.0
        elif self.sample_format == SampleFormat.CI32:
            self._raw_dtype = np.dtype(f"{endian}i4")
            self._norm_factor = 2147483648.0
        else:
            raise ValueError(f"Unsupported streaming format: {self.sample_format}")

        file_bytes = self.path.stat().st_size
        bytes_per_sample = self._raw_dtype.itemsize * 2  # 2 scalar elements (I + Q) per complex sample
        self.total_samples = file_bytes // bytes_per_sample

        # Open memory-map in read-only mode (zero memory copy)
        self._mmap = np.memmap(
            self.path,
            dtype=self._raw_dtype,
            mode="r",
            shape=(self.total_samples * 2,),
        )

        self._cached_overview: DecimatedOverview | None = None
        self.metadata: dict[str, Any] = {
            "file_size_bytes": file_bytes,
            "streaming": True,
            "raw_dtype": str(self._raw_dtype),
        }

    @property
    def num_samples(self) -> int:
        return self.total_samples

    @property
    def duration_s(self) -> float | None:
        if self.sample_rate_hz and self.sample_rate_hz > 0:
            return self.total_samples / self.sample_rate_hz
        return None

    def read_chunk(self, start_idx: int, length: int) -> np.ndarray:
        """Reads a bounded slice of samples into memory and converts to complex64.

        Only the requested range is paged from disk.
        """
        start = max(0, min(start_idx, self.total_samples))
        end = max(start, min(start + length, self.total_samples))
        if start == end:
            return np.zeros(0, dtype=np.complex64)

        raw_slice = self._mmap[start * 2 : end * 2].astype(np.float32)
        if self._norm_factor != 1.0:
            raw_slice /= self._norm_factor

        i_data = raw_slice[0::2]
        q_data = raw_slice[1::2]
        return (i_data + 1j * q_data).astype(np.complex64)

    def slice_to_signal_buffer(self, start_idx: int, end_idx: int) -> SignalBuffer:
        """Instantiates an in-memory SignalBuffer from a designated range of the stream."""
        length = end_idx - start_idx
        samples = self.read_chunk(start_idx, length)
        start_time = (start_idx / self.sample_rate_hz) if self.sample_rate_hz else 0.0

        return SignalBuffer(
            samples=samples,
            sample_rate_hz=self.sample_rate_hz,
            center_frequency_hz=self.center_frequency_hz,
            source_format=SourceFormat.RAW,
            sample_format=self.sample_format,
            start_time=start_time,
            metadata={"source_file": str(self.path), "stream_start_idx": start_idx},
        )

    def compute_decimated_overview(self, target_points: int = 4096) -> DecimatedOverview:
        """Generates a decimated envelope representation for instantaneous display

        of the entire capture without loading the full file into RAM.
        """
        if self._cached_overview is not None:
            return self._cached_overview

        factor = max(1, self.total_samples // target_points)
        num_blocks = self.total_samples // factor

        # Stride through the memory map taking peak and RMS measurements
        min_env = np.empty(num_blocks, dtype=np.float32)
        max_env = np.empty(num_blocks, dtype=np.float32)
        power_db = np.empty(num_blocks, dtype=np.float32)

        chunk_size_samples = 65536  # Process 64k samples per stride
        for b in range(num_blocks):
            sub_chunk = self.read_chunk(b * factor, min(factor, chunk_size_samples))
            if len(sub_chunk) == 0:
                min_env[b] = 0.0
                max_env[b] = 0.0
                power_db[b] = -120.0
                continue
            mag = np.abs(sub_chunk)
            min_env[b] = float(np.min(mag))
            max_env[b] = float(np.max(mag))
            pwr = np.mean(mag**2) + 1e-15
            power_db[b] = float(10.0 * np.log10(pwr))

        self._cached_overview = DecimatedOverview(
            decimation_factor=factor,
            min_envelope=min_env,
            max_envelope=max_env,
            power_db=power_db,
        )
        return self._cached_overview

    def close(self) -> None:
        """Closes the underlying memory map."""
        if hasattr(self, "_mmap") and self._mmap is not None:
            del self._mmap

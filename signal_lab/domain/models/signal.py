"""Signal data models: SignalBuffer and SignalSegment."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import numpy as np

from signal_lab.domain.enums import SampleFormat, SourceFormat


@dataclass
class SignalBuffer:
    """Canonical in-memory container for complex signal samples.

    The rest of the system operates on canonical complex64 representation,
    regardless of whether the original file was WAV, raw IQ, or binary capture.
    """

    samples: np.ndarray
    sample_rate_hz: float | None = None
    center_frequency_hz: float | None = None
    channel_count: int = 1
    source_format: SourceFormat | str = SourceFormat.IQ
    sample_format: SampleFormat | str = SampleFormat.CF32
    start_time: float | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.samples, np.ndarray):
            raise TypeError(f"samples must be a numpy.ndarray, got {type(self.samples)}")
        if not np.iscomplexobj(self.samples):
            # Convert real or interleaved to complex64 if needed
            self.samples = self.samples.astype(np.complex64)
        elif self.samples.dtype != np.complex64:
            self.samples = self.samples.astype(np.complex64)

    @property
    def num_samples(self) -> int:
        return len(self.samples)

    @property
    def duration_s(self) -> float | None:
        if self.sample_rate_hz and self.sample_rate_hz > 0:
            return self.num_samples / self.sample_rate_hz
        return None

    def slice(self, start_idx: int, end_idx: int) -> SignalBuffer:
        """Create a new SignalBuffer from a sample slice."""
        sliced_samples = self.samples[start_idx:end_idx]
        start_time_offset = None
        if self.start_time is not None:
            offset_s = (start_idx / self.sample_rate_hz) if self.sample_rate_hz else 0.0
            start_time_offset = self.start_time + offset_s
        return SignalBuffer(
            samples=sliced_samples,
            sample_rate_hz=self.sample_rate_hz,
            center_frequency_hz=self.center_frequency_hz,
            channel_count=self.channel_count,
            source_format=self.source_format,
            sample_format=self.sample_format,
            start_time=start_time_offset,
            metadata=dict(self.metadata),
        )


@dataclass
class SignalSegment:
    """Represents a detected or user-selected region of signal interest."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_sample: int = 0
    end_sample: int = 0
    start_time_s: float = 0.0
    duration_s: float = 0.0
    center_frequency_hz: float | None = None
    bandwidth_hz: float | None = None
    snr_db: float | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def num_samples(self) -> int:
        return max(0, self.end_sample - self.start_sample)

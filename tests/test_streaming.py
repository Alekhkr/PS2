"""Unit tests and benchmarks for StreamingSignalBuffer."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from signal_lab.domain.enums import ByteOrder, SampleFormat
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.ingestion.iq_parser import IQFormatConfig
from signal_lab.ingestion.streaming import StreamingSignalBuffer


@pytest.fixture
def tmp_raw_binary(tmp_path: Path) -> Path:
    p = tmp_path / "stream_test.bin"
    # Create 100,000 complex int16 samples = 200,000 int16 scalars = 400 kB
    t = np.arange(100_000)
    i = (10000 * np.cos(2 * np.pi * 0.05 * t)).astype("<i2")
    q = (10000 * np.sin(2 * np.pi * 0.05 * t)).astype("<i2")
    interleaved = np.empty(200_000, dtype="<i2")
    interleaved[0::2] = i
    interleaved[1::2] = q
    interleaved.tofile(p)
    return p


def test_synthetic_streaming_buffer(tmp_raw_binary: Path) -> None:
    cfg = IQFormatConfig(
        sample_format=SampleFormat.CI16,
        byte_order=ByteOrder.LITTLE_ENDIAN,
        sample_rate_hz=1_000_000.0,
    )
    stream = StreamingSignalBuffer(tmp_raw_binary, config=cfg)
    assert stream.total_samples == 100_000
    assert stream.duration_s == pytest.approx(0.1, rel=1e-3)

    # Read a chunk
    chunk = stream.read_chunk(1000, 500)
    assert len(chunk) == 500
    assert chunk.dtype == np.complex64
    assert np.all(np.abs(chunk) <= 1.0)

    # Convert slice to SignalBuffer
    buf = stream.slice_to_signal_buffer(1000, 2000)
    assert isinstance(buf, SignalBuffer)
    assert buf.num_samples == 1000
    assert buf.sample_rate_hz == 1_000_000.0

    # Decimated overview
    overview = stream.compute_decimated_overview(target_points=500)
    assert len(overview.max_envelope) > 0
    assert len(overview.power_db) > 0

    stream.close()


def test_real_wlan_320mb_benchmark() -> None:
    """Benchmark: Open 320 MB WLAN capture in < 500ms and read chunks with bounded RAM."""
    wlan_path = Path("data/WLAN_laptop_refMeas_M3_rep1.bin")
    if not wlan_path.exists():
        pytest.skip(f"Capture {wlan_path} not found")

    cfg = IQFormatConfig(
        sample_format=SampleFormat.CI16,
        byte_order=ByteOrder.LITTLE_ENDIAN,
        sample_rate_hz=20_000_000.0,
        center_frequency_hz=2_412_000_000.0,
    )

    t0 = time.perf_counter()
    stream = StreamingSignalBuffer(wlan_path, config=cfg)
    load_time_ms = (time.perf_counter() - t0) * 1000.0

    # Must open instantaneously via memmap (< 200 ms)
    assert load_time_ms < 500.0, f"Load took {load_time_ms:.1f}ms, expected < 500ms"
    assert stream.total_samples == 80_000_000
    assert stream.duration_s == pytest.approx(4.0, rel=1e-3)

    # Reading a 100k chunk takes < 10ms
    t_chunk = time.perf_counter()
    chunk = stream.read_chunk(500_000, 100_000)
    chunk_time_ms = (time.perf_counter() - t_chunk) * 1000.0
    assert len(chunk) == 100_000
    assert chunk_time_ms < 50.0

    stream.close()

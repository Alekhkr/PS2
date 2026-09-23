"""Unit tests for SigMF Parser and Exporter."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from signal_lab.domain.enums import SourceFormat
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.ingestion.sigmf_parser import SigMFParser


@pytest.fixture
def tmp_sigmf_dataset(tmp_path: Path) -> Path:
    """Creates a temporary synthetic SigMF dataset."""
    prefix = tmp_path / "test_sigmf"
    meta_path = tmp_path / "test_sigmf.sigmf-meta"
    data_path = tmp_path / "test_sigmf.sigmf-data"

    meta_content = {
        "global": {
            "core:datatype": "cf32_le",
            "core:sample_rate": 2048000.0,
            "core:version": "1.0.0",
            "core:description": "Synthetic BPSK test capture",
            "core:author": "Test Suite",
        },
        "captures": [
            {
                "core:sample_start": 0,
                "core:frequency": 433920000.0,
                "core:datetime": "2026-09-23T12:00:00Z",
            }
        ],
        "annotations": [
            {
                "core:sample_start": 100,
                "core:sample_count": 500,
                "core:label": "burst_1",
            }
        ],
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_content, f)

    # 1000 complex samples: sinusoidal test tone
    t = np.arange(1000)
    samples = np.exp(1j * 2 * np.pi * 0.1 * t).astype(np.complex64)
    interleaved = np.empty(2000, dtype="<f4")
    interleaved[0::2] = np.real(samples)
    interleaved[1::2] = np.imag(samples)
    interleaved.tofile(data_path)

    return prefix


def test_parse_valid_sigmf(tmp_sigmf_dataset: Path) -> None:
    buf = SigMFParser.parse_file(tmp_sigmf_dataset)
    assert isinstance(buf, SignalBuffer)
    assert buf.sample_rate_hz == 2048000.0
    assert buf.center_frequency_hz == 433920000.0
    assert buf.source_format == SourceFormat.SIGMF
    assert buf.num_samples == 1000
    assert len(buf.metadata["sigmf_annotations"]) == 1
    assert buf.metadata["sigmf_annotations"][0]["core:label"] == "burst_1"


def test_parse_sigmf_with_max_samples(tmp_sigmf_dataset: Path) -> None:
    buf = SigMFParser.parse_file(tmp_sigmf_dataset, max_samples=250)
    assert buf.num_samples == 250


def test_export_and_reimport_roundtrip(tmp_path: Path) -> None:
    # Create original buffer
    t = np.arange(500)
    samples = (0.5 * np.cos(2 * np.pi * 0.05 * t) + 1j * 0.5 * np.sin(2 * np.pi * 0.05 * t)).astype(
        np.complex64
    )
    orig_buf = SignalBuffer(
        samples=samples,
        sample_rate_hz=1000000.0,
        center_frequency_hz=144390000.0,
    )

    out_prefix = tmp_path / "roundtrip_test"
    meta_p, data_p = SigMFParser.export_file(orig_buf, out_prefix)
    assert meta_p.exists()
    assert data_p.exists()

    # Reimport
    reimported = SigMFParser.parse_file(out_prefix)
    assert reimported.sample_rate_hz == orig_buf.sample_rate_hz
    assert reimported.center_frequency_hz == orig_buf.center_frequency_hz
    assert reimported.num_samples == orig_buf.num_samples
    # Samples should match to single-precision float precision
    np.testing.assert_allclose(reimported.samples, orig_buf.samples, atol=1e-6)


def test_missing_files_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        SigMFParser.parse_file(tmp_path / "non_existent_file")

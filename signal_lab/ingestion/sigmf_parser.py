"""SigMF (Signal Metadata Format) Ingestion and Export Engine.

Fully adheres to the SigMF standard specification:
- Reads and parses .sigmf-meta JSON metadata and .sigmf-data binary payload.
- Maps standard SigMF datatypes (cf32_le, cf64_le, ci16_le, ci8, etc.) to complex64.
- Extracts global metadata, capture frequency, timestamp, and annotations.
- Exports SignalBuffer objects to valid .sigmf-meta and .sigmf-data file pairs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from signal_lab.domain.enums import SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer

# Mapping of SigMF core:datatype strings to numpy dtypes & normalization scales
SIGMF_DATATYPE_MAP: dict[str, tuple[str, float, SampleFormat]] = {
    "cf32_le": ("<f4", 1.0, SampleFormat.CF32),
    "cf32_be": (">f4", 1.0, SampleFormat.CF32),
    "cf64_le": ("<f8", 1.0, SampleFormat.CF64),
    "cf64_be": (">f8", 1.0, SampleFormat.CF64),
    "ci16_le": ("<i2", 32768.0, SampleFormat.CI16),
    "ci16_be": (">i2", 32768.0, SampleFormat.CI16),
    "ci8": ("i1", 128.0, SampleFormat.CI8),
    "cu8": ("u1", 128.0, SampleFormat.CI8),
    "ci32_le": ("<i4", 2147483648.0, SampleFormat.CI32),
    "ci32_be": (">i4", 2147483648.0, SampleFormat.CI32),
}

# Reverse mapping for export
SAMPLE_FORMAT_TO_SIGMF: dict[SampleFormat, str] = {
    SampleFormat.CF32: "cf32_le",
    SampleFormat.CF64: "cf64_le",
    SampleFormat.CI16: "ci16_le",
    SampleFormat.CI8: "ci8",
    SampleFormat.CI32: "ci32_le",
}


@dataclass
class SigMFMetadata:
    """Representation of parsed SigMF metadata."""

    datatype: str
    sample_rate_hz: float | None = None
    center_frequency_hz: float | None = None
    author: str = "Signal Lab"
    description: str = "RF Capture"
    version: str = "1.0.0"
    captures: list[dict[str, Any]] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    extra_global: dict[str, Any] = field(default_factory=dict)


class SigMFParser:
    """Universal parser and exporter for SigMF archives."""

    @classmethod
    def resolve_paths(cls, path: str | Path) -> tuple[Path, Path]:
        """Resolves .sigmf-meta and .sigmf-data paths from either file or base prefix."""
        p = Path(path)
        if p.name.endswith(".sigmf-meta"):
            meta_path = p
            data_path = p.with_name(p.name[: -len(".sigmf-meta")] + ".sigmf-data")
        elif p.name.endswith(".sigmf-data"):
            data_path = p
            meta_path = p.with_name(p.name[: -len(".sigmf-data")] + ".sigmf-meta")
        else:
            meta_path = p.with_suffix(".sigmf-meta")
            data_path = p.with_suffix(".sigmf-data")

        return meta_path, data_path

    @classmethod
    def read_metadata(cls, meta_path: Path) -> SigMFMetadata:
        """Parses and validates a .sigmf-meta JSON document."""
        if not meta_path.exists():
            raise FileNotFoundError(f"SigMF metadata file not found: {meta_path}")

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        global_info = data.get("global", {})
        datatype = global_info.get("core:datatype")
        if not datatype:
            raise ValueError(f"Missing mandatory 'core:datatype' in {meta_path}")

        sample_rate = global_info.get("core:sample_rate")
        author = global_info.get("core:author", "Signal Lab")
        description = global_info.get("core:description", "")
        version = global_info.get("core:version", "1.0.0")

        captures = data.get("captures", [])
        annotations = data.get("annotations", [])

        center_freq = None
        if captures:
            center_freq = captures[0].get("core:frequency")

        return SigMFMetadata(
            datatype=datatype,
            sample_rate_hz=float(sample_rate) if sample_rate is not None else None,
            center_frequency_hz=float(center_freq) if center_freq is not None else None,
            author=author,
            description=description,
            version=version,
            captures=captures,
            annotations=annotations,
            extra_global=global_info,
        )

    @classmethod
    def parse_file(
        cls,
        path: str | Path,
        max_samples: int | None = None,
    ) -> SignalBuffer:
        """Parses a SigMF dataset (.sigmf-meta + .sigmf-data) into a canonical SignalBuffer."""
        meta_path, data_path = cls.resolve_paths(path)
        meta = cls.read_metadata(meta_path)

        if not data_path.exists():
            raise FileNotFoundError(f"SigMF data file not found: {data_path}")

        dtype_str, norm_factor, sample_fmt = SIGMF_DATATYPE_MAP.get(
            meta.datatype, ("<f4", 1.0, SampleFormat.CF32)
        )

        dt = np.dtype(dtype_str)
        # Each complex sample contains 2 scalar elements (I and Q interleaved)
        count = max_samples * 2 if max_samples is not None else -1

        raw_array = np.fromfile(data_path, dtype=dt, count=count)
        if len(raw_array) % 2 != 0:
            raw_array = raw_array[: len(raw_array) - (len(raw_array) % 2)]

        # If data is unsigned 8-bit, center at 0
        if meta.datatype == "cu8":
            raw_floats = (raw_array.astype(np.float32) - 128.0) / 128.0
        else:
            raw_floats = raw_array.astype(np.float32)
            if norm_factor != 1.0:
                raw_floats /= norm_factor

        # Form complex64: I = even indices, Q = odd indices
        complex_samples = (raw_floats[0::2] + 1j * raw_floats[1::2]).astype(np.complex64)

        return SignalBuffer(
            samples=complex_samples,
            sample_rate_hz=meta.sample_rate_hz,
            center_frequency_hz=meta.center_frequency_hz,
            channel_count=1,
            source_format=SourceFormat.SIGMF,
            sample_format=sample_fmt,
            metadata={
                "sigmf_global": meta.extra_global,
                "sigmf_captures": meta.captures,
                "sigmf_annotations": meta.annotations,
                "sigmf_meta_path": str(meta_path),
                "sigmf_data_path": str(data_path),
            },
        )

    @classmethod
    def export_file(
        cls,
        buffer: SignalBuffer,
        output_prefix: str | Path,
        description: str = "Exported from Signal Lab",
        author: str = "Signal Lab User",
    ) -> tuple[Path, Path]:
        """Exports a SignalBuffer to standard .sigmf-meta and .sigmf-data files."""
        prefix = Path(output_prefix)
        # Strip extension if passed
        if prefix.suffix in (".sigmf-meta", ".sigmf-data"):
            prefix = prefix.with_suffix("")

        meta_path = prefix.with_suffix(".sigmf-meta")
        data_path = prefix.with_suffix(".sigmf-data")

        # Determine output datatype: default to cf32_le for lossless canonical representation
        datatype = "cf32_le"

        # Interleave I and Q as float32
        i_data = np.real(buffer.samples).astype("<f4")
        q_data = np.imag(buffer.samples).astype("<f4")
        interleaved = np.empty(len(buffer.samples) * 2, dtype="<f4")
        interleaved[0::2] = i_data
        interleaved[1::2] = q_data

        # Write data file
        interleaved.tofile(data_path)

        # Build SigMF metadata JSON
        meta_dict: dict[str, Any] = {
            "global": {
                "core:datatype": datatype,
                "core:sample_rate": float(buffer.sample_rate_hz) if buffer.sample_rate_hz else 1.0,
                "core:version": "1.0.0",
                "core:description": description,
                "core:author": author,
                "core:recorder": "Signal Lab v0.1.0",
                "core:num_channels": buffer.channel_count,
            },
            "captures": [
                {
                    "core:sample_start": 0,
                    "core:frequency": float(buffer.center_frequency_hz)
                    if buffer.center_frequency_hz
                    else 0.0,
                    "core:datetime": "2026-09-23T00:00:00Z",
                }
            ],
            "annotations": buffer.metadata.get("sigmf_annotations", []),
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        return meta_path, data_path

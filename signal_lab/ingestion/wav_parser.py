"""WAV audio/IQ capture parser."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import hilbert

from signal_lab.domain.enums import SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer


class WavParser:
    """Parses standard RIFF WAV files into canonical complex64 SignalBuffers."""

    @staticmethod
    def parse_file(
        filepath: str | Path,
        use_analytic_signal_for_mono: bool = True,
        center_frequency_hz: float | None = None,
    ) -> SignalBuffer:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"WAV file not found: {path}")

        sample_rate_hz, raw_data = wavfile.read(path)

        # Detect sample format and normalization factor
        if raw_data.dtype == np.int16:
            norm_factor = 32768.0
            sample_fmt = SampleFormat.PCM16
            data_float = raw_data.astype(np.float32) / norm_factor
        elif raw_data.dtype == np.int32:
            norm_factor = 2147483648.0
            sample_fmt = SampleFormat.PCM32
            data_float = raw_data.astype(np.float32) / norm_factor
        elif raw_data.dtype == np.uint8:
            sample_fmt = SampleFormat.CI8
            # uint8 WAV is offset by 128
            data_float = (raw_data.astype(np.float32) - 128.0) / 128.0
        elif np.issubdtype(raw_data.dtype, np.floating):
            sample_fmt = SampleFormat.CF32
            data_float = raw_data.astype(np.float32)
        else:
            sample_fmt = SampleFormat.UNKNOWN
            data_float = raw_data.astype(np.float32)

        # Check channel count
        if data_float.ndim == 1:
            # Mono capture
            channel_count = 1
            if use_analytic_signal_for_mono:
                # Generate analytic complex signal via Hilbert transform
                complex_samples = hilbert(data_float).astype(np.complex64)
            else:
                complex_samples = (data_float + 0j).astype(np.complex64)
        elif data_float.ndim == 2:
            channel_count = data_float.shape[1]
            if channel_count >= 2:
                # Stereo IQ: Channel 0 is I, Channel 1 is Q
                i_samples = data_float[:, 0]
                q_samples = data_float[:, 1]
                complex_samples = (i_samples + 1j * q_samples).astype(np.complex64)
            else:
                complex_samples = (data_float[:, 0] + 0j).astype(np.complex64)
        else:
            raise ValueError(f"Unsupported WAV dimensions: {data_float.ndim}")

        metadata = {
            "source_path": str(path),
            "original_sample_rate": sample_rate_hz,
            "original_dtype": str(raw_data.dtype),
            "channels": channel_count,
            "duration_s": len(complex_samples) / sample_rate_hz if sample_rate_hz > 0 else 0.0,
        }

        return SignalBuffer(
            samples=complex_samples,
            sample_rate_hz=float(sample_rate_hz),
            center_frequency_hz=center_frequency_hz,
            channel_count=channel_count,
            source_format=SourceFormat.WAV,
            sample_format=sample_fmt,
            start_time=0.0,
            metadata=metadata,
        )

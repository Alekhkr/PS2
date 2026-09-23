"""Unit tests for WAV and Raw IQ file ingestion."""

from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

from signal_lab.domain.enums import ByteOrder, SampleFormat, SourceFormat
from signal_lab.ingestion import RawIQParser, WavParser, load_signal_file
from signal_lab.ingestion.iq_parser import IQFormatConfig


def test_wav_ingestion_mono(tmp_path: Path) -> None:
    """Test reading a mono PCM16 WAV and converting to analytic complex signal."""
    fs = 48000
    duration = 0.05
    t = np.arange(int(fs * duration)) / fs
    audio = (0.5 * np.sin(2 * np.pi * 1000 * t) * 32767).astype(np.int16)

    wav_file = tmp_path / "test_mono.wav"
    wavfile.write(wav_file, fs, audio)

    buf = WavParser.parse_file(wav_file)
    assert buf.sample_rate_hz == 48000.0
    assert buf.source_format == SourceFormat.WAV
    assert buf.sample_format == SampleFormat.PCM16
    assert buf.num_samples == len(audio)
    assert np.iscomplexobj(buf.samples)
    assert buf.samples.dtype == np.complex64


def test_wav_ingestion_stereo_iq(tmp_path: Path) -> None:
    """Test reading a stereo PCM16 WAV where Ch0=I and Ch1=Q."""
    fs = 96000
    n = 2000
    i_data = (np.cos(np.linspace(0, 10, n)) * 20000).astype(np.int16)
    q_data = (np.sin(np.linspace(0, 10, n)) * 20000).astype(np.int16)
    stereo_data = np.stack([i_data, q_data], axis=1)

    wav_file = tmp_path / "test_stereo_iq.wav"
    wavfile.write(wav_file, fs, stereo_data)

    buf = load_signal_file(wav_file, center_frequency_hz=145_000_000.0)
    assert buf.sample_rate_hz == 96000.0
    assert buf.center_frequency_hz == 145_000_000.0
    assert buf.channel_count == 2
    assert buf.num_samples == n
    assert pytest.approx(float(np.real(buf.samples[0])), rel=1e-3) == (20000 / 32768.0)


def test_raw_iq_cf32_ingestion(tmp_path: Path) -> None:
    """Test reading raw complex float32 binary capture."""
    n_samples = 1500
    i_floats = np.linspace(-1.0, 1.0, n_samples, dtype=np.float32)
    q_floats = np.linspace(1.0, -1.0, n_samples, dtype=np.float32)
    interleaved = np.empty(n_samples * 2, dtype=np.float32)
    interleaved[0::2] = i_floats
    interleaved[1::2] = q_floats

    iq_file = tmp_path / "capture.cf32"
    iq_file.write_bytes(interleaved.tobytes())

    cfg = IQFormatConfig(
        sample_format=SampleFormat.CF32,
        sample_rate_hz=2_000_000.0,
        center_frequency_hz=433_920_000.0,
        scale_auto=False,
    )
    buf = RawIQParser.parse_file(iq_file, config=cfg)
    assert buf.num_samples == n_samples
    assert buf.sample_rate_hz == 2_000_000.0
    assert buf.center_frequency_hz == 433_920_000.0
    assert buf.samples.dtype == np.complex64
    assert pytest.approx(float(np.real(buf.samples[0])), rel=1e-5) == -1.0
    assert pytest.approx(float(np.imag(buf.samples[0])), rel=1e-5) == 1.0


def test_raw_iq_ci16_ingestion(tmp_path: Path) -> None:
    """Test reading signed 16-bit integer interleaved IQ."""
    n_samples = 1000
    raw_ints = np.array([16384, -16384] * n_samples, dtype="<i2")

    iq_file = tmp_path / "capture.ci16"
    iq_file.write_bytes(raw_ints.tobytes())

    cfg = IQFormatConfig(
        sample_format=SampleFormat.CI16,
        byte_order=ByteOrder.LITTLE_ENDIAN,
        scale_auto=False,
    )
    buf = load_signal_file(iq_file, iq_config=cfg)
    assert buf.num_samples == n_samples
    assert pytest.approx(float(np.real(buf.samples[0])), rel=1e-3) == 0.5
    assert pytest.approx(float(np.imag(buf.samples[0])), rel=1e-3) == -0.5

"""Golden regression tests on real RF captures in data/wav/ and data/."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from signal_lab.domain.enums import ByteOrder, SampleFormat
from signal_lab.estimation.bandwidth import estimate_occupied_bandwidth
from signal_lab.estimation.carrier import estimate_carrier_frequency
from signal_lab.estimation.detector import detect_signal_regions
from signal_lab.estimation.snr import estimate_snr
from signal_lab.ingestion.iq_parser import IQFormatConfig, RawIQParser
from signal_lab.ingestion.wav_parser import WavParser


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent.parent / "data"


def test_hf_wwv_capture_properties(data_dir: Path) -> None:
    hf_path = data_dir / "wav" / "N6GN_20211115T190749_iq_15.wav"
    if not hf_path.exists():
        pytest.skip(f"Capture {hf_path} not found")

    buf = WavParser.parse_file(hf_path)
    assert buf.sample_rate_hz == pytest.approx(20249.0, rel=1e-3)
    assert len(buf.samples) > 1_000_000

    # Carrier recovery should find the WWV 100 Hz subcarrier tone
    fc_ev = estimate_carrier_frequency(buf)
    assert fc_ev.confidence > 0.8
    assert abs(fc_ev.value) < 500.0  # Within 500 Hz of center

    # SNR should be high for this clean WWV recording
    snr_ev = estimate_snr(buf)
    assert snr_ev.value > 15.0

    # Bursts should be detected
    bursts = detect_signal_regions(buf.slice(0, 100000), threshold_db=6.0)
    assert len(bursts) > 0


def test_vhf_terrestrial_capture_properties(data_dir: Path) -> None:
    vhf_path = data_dir / "wav" / "audio_37996921Hz_13-51-23_11-11-2023.wav"
    if not vhf_path.exists():
        pytest.skip(f"Capture {vhf_path} not found")

    buf = WavParser.parse_file(vhf_path)
    assert buf.sample_rate_hz == 192000.0
    assert len(buf.samples) > 3_000_000

    # VHF signal estimation
    fc_ev = estimate_carrier_frequency(buf)
    assert fc_ev.confidence > 0.8
    assert abs(fc_ev.value) < 15000.0  # Offset within band

    obw_ev = estimate_occupied_bandwidth(buf)
    assert obw_ev.value > 50000.0  # Wideband VHF transmission

    snr_ev = estimate_snr(buf)
    assert snr_ev.value > 5.0


def test_wlan_binary_parsing_and_metrics(data_dir: Path) -> None:
    wlan_path = data_dir / "WLAN_laptop_refMeas_M3_rep1.bin"
    if not wlan_path.exists():
        pytest.skip(f"WLAN capture {wlan_path} not found")

    cfg = IQFormatConfig(
        sample_format=SampleFormat.CI16,
        byte_order=ByteOrder.LITTLE_ENDIAN,
        sample_rate_hz=20e6,
    )
    buf = RawIQParser.parse_file(wlan_path, config=cfg, max_samples=50000)
    assert len(buf.samples) == 50000
    assert buf.sample_rate_hz == 20e6
    assert np.all(np.abs(buf.samples) <= 1.0)
    power_db = 10 * np.log10(np.mean(np.abs(buf.samples) ** 2) + 1e-12)
    assert -30.0 < power_db < 0.0

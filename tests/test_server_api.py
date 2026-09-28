"""Unit tests for Signal Lab FastAPI backend server endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient
import numpy as np

from signal_lab.server import app

client = TestClient(app)


def test_list_experiments() -> None:
    resp = client.get("/api/experiments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    exp_ids = [e["id"] for e in data]
    assert "exp_01_wwv" in exp_ids
    assert "exp_07_wave" in exp_ids


def test_session_load_and_waveform_lod() -> None:
    # Load WWV capture
    load_resp = client.post("/api/session/load", json={"experiment_id": "exp_01_wwv"})
    assert load_resp.status_code == 200
    load_data = load_resp.json()
    sess_id = load_data["session_id"]
    assert "sess_" in sess_id
    assert load_data["sample_rate_hz"] > 0

    # Query multi-resolution LOD waveform
    wave_resp = client.get(
        "/api/waveform",
        params={"session_id": sess_id, "start_sec": 0.0, "end_sec": 0.5, "target_points": 500},
    )
    assert wave_resp.status_code == 200
    wave_data = wave_resp.json()
    assert wave_data["mode"] in ("lod", "raw")
    if wave_data["mode"] == "lod":
        assert len(wave_data["min_i"]) == 500
        assert len(wave_data["max_i"]) == 500
    else:
        assert len(wave_data["i"]) > 0

    # Query constellation
    const_resp = client.get("/api/constellation", params={"session_id": sess_id, "max_symbols": 256})
    assert const_resp.status_code == 200
    const_data = const_resp.json()
    assert len(const_data["i"]) > 0

    # Query blind analysis
    ana_resp = client.get("/api/analyze", params={"session_id": sess_id})
    assert ana_resp.status_code == 200
    ana_data = ana_resp.json()
    assert "carrier_offset_hz" in ana_data
    assert "snr_db" in ana_data
    assert "modulation" in ana_data

    # Query demodulation
    demod_resp = client.post("/api/demodulate", params={"session_id": sess_id, "mod_type": "BPSK"})
    assert demod_resp.status_code == 200
    demod_data = demod_resp.json()
    assert "evm_percent" in demod_data
    assert "hard_bits_preview" in demod_data

    # Query de-interleaver
    deint_resp = client.post("/api/deinterleave", params={"session_id": sess_id, "method": "block", "rows": 8, "cols": 8})
    assert deint_resp.status_code == 200
    deint_data = deint_resp.json()
    assert "deinterleaved_preview" in deint_data
    assert "rank_curve" in deint_data

    # Query FEC decoder (Viterbi & LDPC)
    fec_resp = client.post("/api/fec/decode", params={"session_id": sess_id, "fec_type": "viterbi_conv"})
    assert fec_resp.status_code == 200
    fec_data = fec_resp.json()
    assert "syndrome_score" in fec_data

    # Query Bitstream correlator
    corr_resp = client.post("/api/correlate", params={"session_id": sess_id, "pattern_name": "Barker_13", "threshold": 0.7})
    assert corr_resp.status_code == 200
    corr_data = corr_resp.json()
    assert "matches" in corr_data

    # Query 2D Spectrogram
    spec_resp = client.get("/api/spectrogram", params={"session_id": sess_id, "start_sec": 0.0, "end_sec": 0.1})
    assert spec_resp.status_code == 200
    spec_data = spec_resp.json()
    assert "frequencies" in spec_data
    assert "magnitude_db" in spec_data
    assert len(spec_data["magnitude_db"]) > 0


def test_health_and_session_fallback() -> None:
    # 1. Health check
    h_resp = client.get("/api/health")
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert h_data["status"] == "online"

    # 2. Querying without session_id automatically loads golden default without 404
    wave_resp = client.get("/api/waveform?start_sec=0&end_sec=0.1")
    assert wave_resp.status_code == 200
    wave_data = wave_resp.json()
    assert "peak_amplitude" in wave_data

    # 3. Demodulating without session_id works seamlessly
    demod_resp = client.post("/api/demodulate", params={"mod_type": "QPSK"})
    assert demod_resp.status_code == 200
    demod_data = demod_resp.json()
    assert "hard_bits_preview" in demod_data


def test_demux_and_telemetry_parser() -> None:
    # 1. AX.25 Demux
    ax_resp = client.post(
        "/api/demux/payload",
        params={"payload_hex": "7222777777777777001A2F4B89CDEFEF55AA", "protocol": "ax25"}
    )
    assert ax_resp.status_code == 200
    ax_data = ax_resp.json()
    assert "AX.25" in ax_data["protocol"]
    assert "destination_callsign" in ax_data
    assert "entropy" in ax_data

    # 2. CCSDS Demux
    ccsds_resp = client.post(
        "/api/demux/payload",
        params={"payload_hex": "0864C0010008DEADBEEFCAFEBA00", "protocol": "ccsds"}
    )
    assert ccsds_resp.status_code == 200
    ccsds_data = ccsds_resp.json()
    assert "CCSDS" in ccsds_data["protocol"]
    assert ccsds_data["apid"] == 100
    assert "Science Instrument" in ccsds_data["apid_description"]
    assert ccsds_data["packet_type"] == "Telemetry"


def test_auto_solve_pipeline_and_report() -> None:
    # Test 1-click autonomous solve
    solve_resp = client.post("/api/pipeline/auto-solve")
    assert solve_resp.status_code == 200
    solve_data = solve_resp.json()
    assert solve_data["pipeline_status"] == "COMPLETED"
    assert "stage_1_parameters" in solve_data
    assert "stage_2_demodulation" in solve_data
    assert "stage_3_deinterleaving" in solve_data
    assert "stage_4_fec" in solve_data
    assert "stage_5_correlation" in solve_data

    # Test technical audit report export
    rep_resp = client.get("/api/report/export")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert "markdown" in rep_data
    assert "SIGNAL LAB" in rep_data["markdown"]
    assert "Outcome I" in rep_data["markdown"]


def test_sdr_streaming_engine() -> None:
    from signal_lab.streaming.sdr_ws import SDRSourceMode, SDRStreamer

    streamer = SDRStreamer()
    streamer.mode = SDRSourceMode.SYNTHETIC
    streamer.mod_type = "QPSK"

    # Test chunk generation
    chunk = streamer.get_next_chunk(256)
    assert len(chunk) == 256
    assert chunk.dtype == np.complex64

    # Test telemetry payload
    telemetry = streamer.compute_telemetry_payload(chunk)
    assert "rms_dbfs" in telemetry
    assert "papr_db" in telemetry
    assert len(telemetry["i_samples"]) == 128
    assert len(telemetry["fft_power"]) == 128

    # Test WebSocket endpoint
    with client.websocket_connect("/ws/sdr") as ws:
        # Should receive first streaming telemetry frame
        data = ws.receive_json()
        assert "timestamp" in data
        assert "fft_power" in data
        # Send reconfiguration
        ws.send_json({"action": "set_source", "source": "synthetic", "mod": "16QAM"})



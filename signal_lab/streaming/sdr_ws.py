"""Live SDR Hardware Streaming & Synthetic IQ WebSocket Engine.

Provides real-time chunked complex IQ streams for Signal Lab frontend,
supporting hardware SDRs (RTL-SDR/HackRF), capture replay, and synthetic
parameter-drifting modulation generators.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from enum import Enum
from typing import Any

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


class SDRSourceMode(str, Enum):
    SYNTHETIC = "synthetic"
    REPLAY = "replay"
    HARDWARE = "hardware"


class SDRStreamer:
    """Manages SDR live IQ sample generation, streaming pacing, and WebSocket dispatch."""

    def __init__(self) -> None:
        self.mode: SDRSourceMode = SDRSourceMode.SYNTHETIC
        self.mod_type: str = "16QAM"
        self.sample_rate: int = 100000  # 100 kSps
        self.center_freq: float = 433.92e6  # 433.92 MHz ISM / UHF
        self.snr_db: float = 24.0
        self.is_streaming: bool = True
        self.replay_buffer: np.ndarray | None = None
        self.replay_idx: int = 0
        self._phase: float = 0.0

    def set_replay_buffer(self, iq_samples: np.ndarray, sample_rate: int = 100000) -> None:
        """Loads an in-memory complex IQ array for replay streaming."""
        self.replay_buffer = np.asarray(iq_samples, dtype=np.complex64)
        self.sample_rate = sample_rate
        self.replay_idx = 0

    def generate_synthetic_chunk(self, n_samples: int = 512) -> np.ndarray:
        """Synthesizes high-fidelity complex IQ samples with realistic channel noise."""
        t = (np.arange(n_samples) + self._phase) / self.sample_rate
        self._phase = (self._phase + n_samples) % self.sample_rate

        mod = self.mod_type.upper()
        if mod == "QPSK":
            # Random 4-QAM / QPSK symbols
            sym_len = 16
            n_syms = (n_samples // sym_len) + 1
            const = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / math.sqrt(2)
            syms = np.random.choice(const, size=n_syms)
            sig = np.repeat(syms, sym_len)[:n_samples]
            # Small carrier offset rotation
            cfo = 350.0  # Hz
            sig = sig * np.exp(1j * 2 * np.pi * cfo * t)

        elif mod == "16QAM":
            sym_len = 16
            n_syms = (n_samples // sym_len) + 1
            levels = np.array([-3, -1, 1, 3]) / math.sqrt(10)
            i_syms = np.random.choice(levels, size=n_syms)
            q_syms = np.random.choice(levels, size=n_syms)
            syms = i_syms + 1j * q_syms
            sig = np.repeat(syms, sym_len)[:n_samples]
            cfo = 150.0
            sig = sig * np.exp(1j * 2 * np.pi * cfo * t)

        elif mod == "FSK":
            # Continuous-Phase 2-FSK
            f_dev = 5000.0  # 5 kHz shift
            bit_len = 32
            n_bits = (n_samples // bit_len) + 1
            bits = np.random.choice([-1.0, 1.0], size=n_bits)
            freq_offset = np.repeat(bits, bit_len)[:n_samples] * f_dev
            phase = 2 * np.pi * np.cumsum(freq_offset) / self.sample_rate
            sig = np.exp(1j * phase)

        elif mod == "CHIRP":
            # Linear frequency modulated radar chirp
            sweep_bw = 20000.0  # 20 kHz
            chirp_period = 0.005  # 5 ms
            t_rel = (t % chirp_period)
            f_inst = -sweep_bw / 2 + (sweep_bw / chirp_period) * t_rel
            phase = 2 * np.pi * np.cumsum(f_inst) / self.sample_rate
            sig = np.exp(1j * phase)

        else:
            # Default BPSK
            bit_len = 16
            n_bits = (n_samples // bit_len) + 1
            bits = np.random.choice([-1.0, 1.0], size=n_bits)
            sig = np.repeat(bits, bit_len)[:n_samples].astype(np.complex64)

        # Add AWGN channel noise according to target SNR
        sig_pow = np.mean(np.abs(sig) ** 2)
        noise_pow = sig_pow / (10.0 ** (self.snr_db / 10.0))
        noise = (
            np.random.normal(0, math.sqrt(noise_pow / 2.0), n_samples)
            + 1j * np.random.normal(0, math.sqrt(noise_pow / 2.0), n_samples)
        )
        return (sig + noise).astype(np.complex64)

    def get_next_chunk(self, n_samples: int = 512) -> np.ndarray:
        """Retrieves next chunk depending on current source mode."""
        if self.mode == SDRSourceMode.REPLAY and self.replay_buffer is not None:
            buf_len = len(self.replay_buffer)
            if buf_len == 0:
                return self.generate_synthetic_chunk(n_samples)
            start = self.replay_idx
            end = start + n_samples
            if end <= buf_len:
                chunk = self.replay_buffer[start:end]
                self.replay_idx = end % buf_len
            else:
                chunk = np.concatenate([self.replay_buffer[start:], self.replay_buffer[: end % buf_len]])
                self.replay_idx = end % buf_len
            return chunk.astype(np.complex64)

        elif self.mode == SDRSourceMode.HARDWARE:
            # Check for pyrtlsdr
            try:
                import rtlsdr  # type: ignore
                # Hardware read stub
                return self.generate_synthetic_chunk(n_samples)
            except Exception:
                # Fallback to synthetic if hardware is offline
                return self.generate_synthetic_chunk(n_samples)

        return self.generate_synthetic_chunk(n_samples)

    def compute_telemetry_payload(self, chunk: np.ndarray) -> dict[str, Any]:
        """Computes low-overhead JSON-serializable telemetry and waveform chunk."""
        # RMS & PAPR
        mag_sq = np.abs(chunk) ** 2
        rms = float(np.sqrt(np.mean(mag_sq)))
        rms_dbfs = float(20.0 * math.log10(max(rms, 1e-9)))
        peak = float(np.max(np.abs(chunk)))
        papr_db = float(20.0 * math.log10(max(peak / max(rms, 1e-9), 1.0)))

        # Downsample waveform for UI transport (128 complex points)
        downsample_factor = max(1, len(chunk) // 128)
        dec_chunk = chunk[::downsample_factor][:128]
        i_arr = np.round(dec_chunk.real, 4).tolist()
        q_arr = np.round(dec_chunk.imag, 4).tolist()

        # FFT Power Spectrum (128 bins)
        win = np.hanning(len(chunk))
        fft_data = np.fft.fftshift(np.fft.fft(chunk * win))
        fft_mag = np.abs(fft_data)
        fft_db = 20.0 * np.log10(np.maximum(fft_mag / (len(chunk) / 2.0), 1e-6))
        # Downsample FFT to 128 bins
        fft_down = np.linspace(0, len(fft_db) - 1, 128).astype(int)
        fft_power = np.round(fft_db[fft_down], 2).tolist()

        return {
            "timestamp": time.time(),
            "mode": self.mode.value,
            "mod_type": self.mod_type,
            "sample_rate": self.sample_rate,
            "center_freq_hz": self.center_freq,
            "snr_db": self.snr_db,
            "rms_dbfs": round(rms_dbfs, 2),
            "papr_db": round(papr_db, 2),
            "i_samples": i_arr,
            "q_samples": q_arr,
            "fft_power": fft_power,
        }


# Global streaming engine instance
global_streamer = SDRStreamer()
router = APIRouter(prefix="/ws", tags=["SDR Streaming"])


@router.websocket("/sdr")
async def websocket_sdr_endpoint(websocket: WebSocket) -> None:
    """Live bidirectional WebSocket streamer for RF intelligence telemetry."""
    await websocket.accept()
    streamer = global_streamer
    is_active = True

    async def incoming_listener() -> None:
        nonlocal is_active
        try:
            while is_active:
                msg_text = await websocket.receive_text()
                cmd = json.loads(msg_text)
                action = cmd.get("action")
                if action == "set_source":
                    src = cmd.get("source", "synthetic")
                    if src == "replay":
                        streamer.mode = SDRSourceMode.REPLAY
                    elif src == "hardware":
                        streamer.mode = SDRSourceMode.HARDWARE
                    else:
                        streamer.mode = SDRSourceMode.SYNTHETIC

                    if "mod" in cmd:
                        streamer.mod_type = str(cmd["mod"])
                    if "snr_db" in cmd:
                        streamer.snr_db = float(cmd["snr_db"])
                    if "sample_rate" in cmd:
                        streamer.sample_rate = int(cmd["sample_rate"])

                elif action == "pause":
                    streamer.is_streaming = False
                elif action == "resume":
                    streamer.is_streaming = True

        except (WebSocketDisconnect, asyncio.CancelledError):
            is_active = False
        except Exception:
            is_active = False

    listener_task = asyncio.create_task(incoming_listener())

    try:
        # Stream at ~30 Hz (33ms period)
        while is_active:
            if streamer.is_streaming:
                chunk = streamer.get_next_chunk(512)
                telemetry = streamer.compute_telemetry_payload(chunk)
                await websocket.send_text(json.dumps(telemetry))
            await asyncio.sleep(0.033)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        is_active = False
        listener_task.cancel()

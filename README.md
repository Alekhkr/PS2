# Signal Lab

Automated IQ/WAV Signal Analysis Platform.

A high-precision desktop scientific instrument built with PySide6 and PyQtGraph for authorized analysis of RF signal captures.

## Features
- Ingestion of WAV and arbitrary raw IQ binary formats into canonical `SignalBuffer` containers.
- Deterministic DSP conditioning: DC removal, IQ imbalance correction, frequency shifting, filtering.
- Multi-plot synchronized scientific instrument view (Time domain, PSD/FFT, 2D Waterfall, Constellation).
- Multi-factor parameter estimation (Carrier frequency, occupied bandwidth, SNR, symbol rate candidates).
- Hybrid modulation classification and protocol-driven demodulation (FSK, BPSK, QPSK, 8PSK, QAM16, QAM64).
- Interleaver and FEC hypothesis testing engines (Viterbi, Reed-Solomon, LDPC).
- Bitstream correlation and frame detection.
- Full provenance and audit trail for every measured parameter via `ParameterEvidence`.

## Quick Start: Running Frontend & Backend

### 1. Backend Server (FastAPI + DSP Engine)
```bash
# Direct ASGI launch:
uvicorn app:main --reload --port 8000

# Or via Python runner:
python main.py
```
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Frontend Application (React 19 + TypeScript + Three.js)
```bash
cd frontend
pnpm dev --port 5173
```
- **Interactive Workbench**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

### 3. Native Desktop GUI (PySide6 / Qt)
```bash
python -m signal_lab.gui
```

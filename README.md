# Signal Lab

**Automated IQ/WAV Signal Analysis Platform — Autonomous Terrestrial RF Signal Intelligence Desktop Instrument.**

Signal Lab is a scientific-grade desktop platform built with **PySide6**, **PyQtGraph**, **NumPy**, **SciPy**, and **C++ SIMD kernels** (`pybind11`). It is engineered for the deep, autonomous physical-layer extraction, parameter estimation, modulation classification, synchronization, demodulation, bitstream frame inspection, forward error correction (FEC), and algorithmic provenance auditing of authorized terrestrial RF signal captures.

---

## 1. Key Capabilities

- **Multi-Format Ingestion**: Ingests standard WAV (mono/stereo Hilbert analytic conversion, PCM16, PCM32, CI8, CF32), arbitrary raw binary IQ (`cf32`, `cf64`, `ci16`, `ci8`, `ci32` with byte order configuration), SigMF compliant captures (`.sigmf-meta` and `.sigmf-data`), and memory-mapped chunk streaming (`StreamingSignalBuffer`) for multi-gigabyte recordings.
- **Assumptions Panel**: Interactive configuration modal with live miniature FFT preview for ambiguous raw captures with missing sample rates.
- **Deterministic DSP Conditioning**: DC offset removal, Gram-Schmidt IQ imbalance correction, linear frequency shifting, power normalization, and polyphase resampling.
- **Native C++ Acceleration**: High-performance C++17 SIMD kernels for min-max decimation, Radix-2 Cooley-Tukey FFT, quadratic carrier peak interpolation, Costas loop tracking, and Mueller-Müller timing recovery.
- **Scientific Visualization**: Synchronized multi-plot instrument surface:
  - Top Canvas: Full-width high-resolution 2D Waterfall / Spectrogram
  - Below: Power Spectral Density (Spectrum) with peak markers and 99% Occupied Bandwidth (OBW) boundaries
  - Synchronized Analysis Row: Time-domain I/Q Waveform, Constellation Plot with decision regions, and Signal Profile panel
- **Parameter Estimation**: Sub-bin quadratic carrier frequency offset, 99% OBW power integral, spectral differential SNR, cyclostationary baud rate candidate search, and STFT energy burst detection.
- **Hybrid Modulation Classification**: Decision fusion combining deterministic higher-order cumulants ($C_{40}, C_{42}$) and envelope variance with a trained 1D-ResNet neural classifier (16 modulation classes from RadioMod-R16).
- **Carrier & Symbol Synchronization**: 2nd-order Costas loop (BPSK, QPSK, 8PSK, QAM) with phase lock telemetry and Mueller-Müller timing error recovery with fractional cubic interpolation.
- **Demodulation Pipeline**: Protocol-driven slicing for BPSK, QPSK, 8PSK, QAM16, QAM64, and 2-FSK/4-FSK with EVM % and soft LLR outputs.
- **Bitstream & Frame Inspection**: Synchronized 3-column Binary / Hexadecimal / ASCII inspector with sync word highlighting (Barker-7/11/13, CCSDS 32-bit ASM `0x1ACFFC1D`) and click-to-waveform microsecond navigation.
- **Interleaving & Forward Error Correction (FEC)**:
  - $R \times C$ Block interleaver and deinterleaver
  - Blind $GF(2)$ Gaussian elimination matrix rank-deficiency search
  - NASA standard Rate 1/2, $K=7$ soft/hard Viterbi decoder with polynomial polynomials `(0o171, 0o133)`
  - Galois Field $GF(2^8)$ Reed-Solomon evaluator
  - Iterative Min-Sum message-passing LDPC decoder (IEEE 802.11n rate 1/2)
  - Joint RS + Viterbi concatenated chain
- **Algorithmic Provenance & Evidence Engine**: Full audit trail for every measured parameter via `ParameterEvidence` (value, unit, source, algorithm, confidence score, assumptions, validation status).
- **Technical Report Generation**: One-click export to publication-grade Markdown and JSON session audit dossiers.

---

## 2. Quick Start

### 2.1 Virtual Environment & Dependencies
```bash
# Using uv (recommended)
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev,ml]"
```

### 2.2 Compile C++ SIMD Accelerated Kernels
```bash
# Compile native pybind11 kernels inplace
python setup.py build_ext --inplace
```

### 2.3 Launch Signal Lab Desktop Application
```bash
# Launch the primary desktop instrument
python main.py
# OR
signal-lab
```

---

## 3. Primary Navigation Workflow

The interface is structured into 7 primary scientific workspaces:

1. **OVERVIEW**: Ingestion launchpad, drag-and-drop file target, quick-load hardware benchmark presets (WWV HF, VHF 38 MHz, WLAN 802.11, R16 AMC), and session history.
2. **ANALYSIS**: Main synchronized instrument surface communicating state at a glance:
   - Header: Session ID (`SL-XXXX`), Status (`ANALYSIS COMPLETE` / `IDLE`), Capture File, Format, Duration, Sample Rate, Center Frequency.
   - Top: High-resolution Waterfall.
   - Below: Power Spectral Density with spectral peak and 99% OBW markers.
   - Synchronized Row: Time-Domain Waveform, Constellation Plot, and Signal Profile panel.
3. **SIGNAL**: Dedicated signal conditioning (DC block, Gram-Schmidt IQ imbalance, normalization) and detected burst energy table.
4. **DEMOD**: Constellation scatter with decision boundaries, EVM % quality gauge, Costas loop carrier phase error, and Mueller-Müller timing error convergence curves.
5. **BITS**: Full-width Bitstream & Frame Inspector with synchronized Binary / Hexadecimal / ASCII telemetry and click-to-time waveform navigation.
6. **EVIDENCE**: Parameter Evidence & Algorithmic Provenance table with confidence scores, validation status, and search filter.
7. **REPORT**: Technical Audit Dossier view with 1-click Markdown / JSON preview, clipboard copy, and file export.

---

## 4. Test Suite & Verification

The test suite runs completely offline and includes headless Qt tests, DSP unit tests, real signal capture verification, and the canonical closed-loop golden test.

```bash
# Run full test suite headlessly (80/80 tests)
QT_QPA_PLATFORM=offscreen pytest tests/ -v

# Run canonical golden end-to-end test specifically
QT_QPA_PLATFORM=offscreen pytest tests/test_golden_e2e.py -v

# Run linter
ruff check .
```

### The Canonical Golden Test (`tests/test_golden_e2e.py`)
Verifies the complete closed-loop physical and link layer pipeline:
$$\text{Payload} \xrightarrow{\text{Encode}} \text{Conv}(K=7, R=1/2) \xrightarrow{\text{Interleave}} \text{Block}(8 \times 8) \xrightarrow{\text{Modulate}} \text{QPSK} \xrightarrow{\text{Channel}} \text{CFO} + \text{Phase} + \text{AWGN} \to \text{Signal Lab}$$
$$\to \text{Conditioning} \to \text{Estimation} \to \text{Costas Lock} \to \text{QPSK Slice} \to \text{Deinterleave} \to \text{Viterbi} \to \text{Correlation} \to \mathbf{100\%\ Payload\ Match}$$

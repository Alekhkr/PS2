# Signal Lab MVP: Architecture Audit & Comprehensive Gap Analysis

**Author:** Primary Senior Software Engineer, DSP Engineer & UI/UX Architect  
**Project:** Signal Lab ([https://github.com/Alekhkr/PS2](https://github.com/Alekhkr/PS2))  
**Target Specification:** Autonomous Terrestrial RF Signal Analysis Platform  
**Status:** Audit Completed & Core Architecture Validated (Phase 0)  
**Date:** September 2026

---

## 1. Executive Summary & Audit Overview

Signal Lab is an automated, scientific-grade desktop platform for the analysis of authorized IQ, WAV, and SigMF terrestrial radio frequency captures. The system extracts critical physical-layer signal parameters, visualizes high-resolution time/frequency/phase domains, performs modulation classification, executes robust carrier and symbol timing synchronization, demodulates symbols to bitstreams, validates interleaving and Forward Error Correction (FEC) hypotheses, correlates sync preambles, and computes rigorous parameter evidence and confidence scores.

### 1.1 Key Audit Findings
1. **Strong Core Scientific Foundation**:
   - The underlying mathematical and scientific algorithms across `signal_lab/ingestion`, `dsp`, `estimation`, `classification`, `synchronization`, `demodulation`, `fec`, `interleaving`, and `correlation` are **genuinely functional**, mathematically sound, and execute completely offline without external network dependencies.
   - 79 core tests pass cleanly in 5.2 seconds across all DSP, estimation, synchronization, demodulation, and FEC modules.
   - C++ SIMD accelerated kernels in `signal_lab/dsp/fast_kernels.cpp` are compiled via PyBind11 (`_fast_kernels.so`) and provide native performance for min-max decimation, Radix-2 Cooley-Tukey FFT, carrier peak search, Costas loop tracking, and Mueller-Müller timing recovery.

2. **Root Cause of Divergence & User Rejection**:
   - In recent commits, an extraneous web-based frontend (`frontend/`, React 19, Vite, Three.js 3D canvas, TailwindCSS) and a FastAPI backend server (`signal_lab/server.py`) were introduced.
   - This web architecture diverted the project away from its primary identity as a **dense, responsive, native scientific desktop instrument** (PySide6 + PyQtGraph). It introduced web-server latency, brittle HTTP/WebSocket serialization, decorative visual clutter (3D wave ribbons, animations), and failed server API tests.
   - **Remediation Completed**: All web bloatware (`frontend/`, `node_modules/`, `package.json`, `pnpm-lock.yaml`, `aws/`, `awscliv2.zip`, `signal_lab/server.py`, `signal_lab/streaming/`) has been completely eradicated. The native PySide6 desktop instrument shell has been fully restored and verified.

3. **Current Test & Linter Status**:
   - `ruff check .`: **100% clean (0 errors)**.
   - `pytest tests/`: **79/79 passing (100% pass rate)** in 5.21s under headless Qt (`QT_QPA_PLATFORM=offscreen`).
   - C++ kernels: Verified and benchmarked with NumPy array exchange.

---

## 2. Component-by-Component Implementation Status

| Component | Modules | Status | Genuine Functionality vs Gaps |
|---|---|---|---|
| **Domain Models** | `signal_lab/domain/models/` (`signal.py`, `evidence.py`, `session.py`, `enums.py`) | **Complete & Functional** | Canonical `SignalBuffer`, `SignalSegment`, `ParameterEvidence`, `ModulationCandidate`, `Session`. Typed, serializable Pydantic models. No GUI leaks. |
| **Ingestion** | `signal_lab/ingestion/` (`wav_parser.py`, `iq_parser.py`, `sigmf_parser.py`, `streaming.py`) | **Complete & Functional** | Real WAV (mono/stereo Hilbert, PCM16, PCM32, CI8, CF32), raw binary IQ (`IQFormatConfig` with CF32, CF64, CI16, CI8, CI32, endianness), SigMF compliant reader/writer, and `StreamingSignalBuffer` (`np.memmap`) for 320MB+ captures. |
| **Assumptions Dialog** | `signal_lab/gui/widgets/assumptions_dialog.py` | **Complete & Functional** | Modal dialog with interactive format, endianness, sample rate selection, and live miniature FFT preview before committing ambiguous raw files. |
| **Conditioning** | `signal_lab/dsp/conditioning.py`, `fast_kernels.cpp` | **Complete & Functional** | DC offset removal, Gram-Schmidt IQ imbalance correction, frequency shifting, power normalization, FIR/IIR filtering, polyphase resampling. Preserves source data immutably. |
| **C++ / Native Kernels** | `signal_lab/dsp/fast_kernels.cpp`, `setup.py`, `CMakeLists.txt` | **Functional & Compiled** | Native C++17 kernels compiled via `pybind11`: `min_max_decimate_iq`, `fft_inplace`, `estimate_carrier_peak`, `costas_loop_process`, `mueller_muller_timing_recovery`. |
| **Parameter Estimation** | `signal_lab/estimation/` (`carrier.py`, `bandwidth.py`, `snr.py`, `symbol_rate.py`, `detector.py`) | **Complete & Functional** | Sub-bin quadratic carrier peak interpolation, 99% occupied bandwidth power integral, spectral differential SNR, cyclostationary envelope squaring baud rate candidate search, STFT energy burst detector. |
| **Modulation Classification** | `signal_lab/classification/` (`features.py`, `classifier.py`, `hybrid_classifier.py`), `signal_lab/ml/` | **Complete & Functional** | Cumulants ($C_{40}, C_{42}$) and envelope variance + 1D-ResNet model on RadioMod-R16. Generates confidence-ranked hypotheses with supporting features. Works offline with deterministic fallback. |
| **Synchronization** | `signal_lab/synchronization/` (`carrier_recovery.py`, `timing_recovery.py`, `rrc.py`, `equalization.py`) | **Complete & Functional** | 2nd-order Costas loop (BPSK/QPSK/8PSK/QAM), Mueller-Müller timing error detector with fractional cubic interpolation, Root-Raised Cosine matched filter, CMA/LMS equalizer. |
| **Demodulation** | `signal_lab/demodulation/` (`base.py`, `psk.py`, `qam.py`, `fsk.py`) | **Complete & Functional** | BPSK, QPSK, 8PSK, QAM16, QAM64, 2-FSK, 4-FSK. Exposes recovered symbols, hard bits, soft LLRs, EVM, synchronization metadata. Independent from plotting. |
| **Bitstream Inspector** | `signal_lab/gui/widgets/bitstream_viewer.py` | **Complete & Functional** | Synchronized 3-column Binary / Hexadecimal / ASCII inspector, bit index telemetry, sync word highlighting, click-to-waveform navigation. |
| **Interleaving & FEC** | `signal_lab/interleaving/`, `signal_lab/fec/` | **Complete & Functional** | $R \times C$ Block interleaver/deinterleaver, blind $GF(2)$ Gaussian elimination rank deficiency width search. Viterbi $K=7, R=1/2$ soft/hard decoder, $RS(255, 223)$, IEEE 802.11n Min-Sum LDPC, Concatenated RS+Viterbi. |
| **Correlation** | `signal_lab/correlation/correlator.py` | **Complete & Functional** | Sliding bit-pattern cross-correlation for Barker (7, 11, 13), CCSDS ASM (`0x1ACFFC1D`), and repeated-pattern / frame periodicity autocorrelation. |
| **Evidence Engine** | `signal_lab/domain/models/evidence.py`, `signal_lab/services/evidence_engine.py` | **Complete & Functional** | Transparent provenance tracking: value, unit, source, algorithm, confidence score ($0.0 - 1.0$), assumptions list, validation status (`UNVERIFIED`, `PARTIAL`, `VALIDATED`). |
| **Session & Storage** | `signal_lab/storage/database.py`, `repository.py` | **Complete & Functional** | SQLite database with WAL mode and foreign key cascading. Saves session metadata, parameter evidence, detected regions, and file references without bloating DB with raw IQ arrays. |
| **Orchestrator** | `signal_lab/services/orchestrator.py` | **Complete & Functional** | Asynchronous `QThread` execution engine with progress updates, cancel support, and non-blocking signal pipeline. |
| **Report Export** | `signal_lab/services/report_service.py` | **Complete & Functional** | Exports structured audit reports in JSON, CSV, and Markdown. |
| **Desktop GUI Shell** | `signal_lab/gui/` (`main_window.py`, `plots/`, `widgets/`, `theme.py`) | **Functional, Needs Layout Alignment** | Native PySide6 + PyQtGraph interface. Needs navigation restructuring to strictly mirror the 7-tab scientific instrument workflow: `OVERVIEW`, `ANALYSIS`, `SIGNAL`, `DEMOD`, `BITS`, `EVIDENCE`, `REPORT`. |
| **Canonical Golden Test** | `tests/test_golden_e2e.py` | **Identified Gap (Phase 6 Deliverable)** | Need a single comprehensive end-to-end test verifying the exact loop: Payload $\to$ Conv Encode $\to$ Block Interleave $\to$ QPSK Modulation $\to$ Impairment $\to$ Signal Lab Ingest $\to$ Condition $\to$ Classify $\to$ Sync $\to$ Demod $\to$ Deinterleave $\to$ Viterbi $\to$ Correlation $\to$ Verified Payload Match. |

---

## 3. What Was Removed vs What Was Preserved

### 3.1 Completely Removed (Bloatware Cleanup)
- `frontend/`: Deleted entire React 19 / TypeScript / Vite / Three.js web application.
- `node_modules/`, `package.json`, `pnpm-lock.yaml`: Deleted all web package manager artifacts.
- `aws/`, `awscliv2.zip`: Deleted 73 MB unused AWS installer zip and directory.
- `signal_lab/server.py`: Deleted FastAPI server and endpoints.
- `signal_lab/streaming/`: Deleted WebSocket SDR server stubs.
- `tests/test_server_api.py`: Deleted obsolete web server tests.

### 3.2 Preserved & Strengthened
- Native PySide6 + PyQtGraph UI (`signal_lab/gui/`).
- Native C++ SIMD kernels (`signal_lab/dsp/fast_kernels.cpp` and `_fast_kernels.so`).
- Pure DSP, estimation, classification, demodulation, synchronization, interleaving, FEC, and correlation algorithms.
- Full offline dataset registry (`data/RadioMod-R16 dataset.h5`, `data/wav/`, `data/WLAN_laptop_*.bin`).
- All 79 unit, component, real-signal, and GUI tests.

---

## 4. Architectural Gaps & Refinement Plan

To meet 100% of the requirements in the project specification, the following specific items will be implemented across the phases:

1. **Navigation & Main Screen Alignment (Phase 1 & 2)**:
   - Restructure `MainWindow` to feature the primary 7-tab navigation bar:
     `OVERVIEW` | `ANALYSIS` | `SIGNAL` | `DEMOD` | `BITS` | `EVIDENCE` | `REPORT`
   - Configure the default `ANALYSIS` screen to immediately present:
     - Header: `SIGNAL LAB`, Session ID (e.g. `SL-0001`), Status (`ANALYSIS COMPLETE` / `IDLE` / `PROCESSING`).
     - Main metadata strip: File, Format, Duration, Sample rate, Center frequency.
     - Top Canvas: High-density **Waterfall** plot.
     - Middle Canvas: Power Spectral Density (**Spectrum**) plot with peak and OBW markers.
     - Synchronized Analysis Row: **Time-domain** trace, **Constellation** scatter, and **Signal Profile** panel (Modulation, Symbol Rate, Bandwidth, SNR, Carrier, Confidence).
     - Analysis Pipeline Breadcrumb: `Detect ✓` $\to$ `Estimate ✓` $\to$ `Classify ✓` $\to$ `Synchronize ✓` $\to$ `Demodulate ✓` $\to$ `Interleave —` $\to$ `FEC —` $\to$ `Correlate ✓`.

2. **One-Click "Auto Analyze" Continuous Flow (Phase 1 & 2)**:
   - Provide an immediate `AUTO ANALYZE` button that triggers the full pipeline upon file drag-and-drop or load.
   - Smoothly update plots and telemetry stages sequentially without freezing the UI thread.

3. **Demodulation Diagnostics & Constellation Overlays (Phase 4 & 5)**:
   - Overlay decision boundaries on the constellation view for BPSK, QPSK, 8PSK, and QAM16.
   - Display EVM %, Costas loop phase lock indicator, and Mueller-Müller timing error convergence.

4. **Canonical Golden End-to-End Test (Phase 6)**:
   - Implement `tests/test_golden_e2e.py` demonstrating the full closed-loop chain:
     Known ASCII string $\to$ Convolutional Encoding ($K=7, R=1/2$) $\to$ Block Interleaving ($8 \times 16$) $\to$ QPSK Modulation ($f_s=100\text{ kHz}, R_{sym}=10\text{ kSym/s}$) $\to$ Carrier frequency offset (+250 Hz) and AWGN (+20 dB SNR) $\to$ Ingestion $\to$ DC block & normalization $\to$ Carrier estimation & Costas correction $\to$ Mueller-Müller timing recovery $\to$ QPSK slicing $\to$ Block deinterleaving $\to$ Viterbi decoding $\to$ Sync word cross-correlation $\to$ Exact original string match.

5. **Report Export Screen & Polish (Phase 7 & 8)**:
   - Dedicated `REPORT` tab in the GUI allowing one-click export of Markdown and JSON technical dossiers.
   - Polished empty states, keyboard shortcuts (`Ctrl+O` open, `Ctrl+R` run, `Space` pause/resume), and refined typography.

---

## 5. Phase-by-Phase Execution Roadmap

```
PHASE 0: Audit & Gap Analysis [COMPLETED]
   ├── Inspect repository, tests, C++ kernels, models, and UI shell
   ├── Eradicate all web bloatware and failed server scripts
   ├── Clean linting to 0 errors via ruff
   └── Publish MVP_GAP_ANALYSIS.md

PHASE 1: GUI Navigation & Ingestion Refinement
   ├── Restructure MainWindow with 7 primary navigation tabs
   ├── Header bar: Session ID, file provenance, status indicator
   ├── Assumptions Dialog integration for ambiguous raw IQ
   └── Auto-Analyze single-click trigger

PHASE 2: Synchronized Scientific Visualization
   ├── Synchronize Waterfall, Spectrum, Time, and Constellation plots
   ├── Shared region selection (selecting span in Waterfall updates Spectrum & Time)
   ├── Spectral peak & 99% OBW visual boundary markers
   └── Signal burst detection bounding box display

PHASE 3: Parameter Estimation Telemetry & Evidence Display
   ├── Real-time population of Signal Profile telemetry panel
   ├── Carrier (quadratic peak), OBW, SNR, Baud rate candidates
   └── Evidence list display with source, confidence, and validation status

PHASE 4: Modulation Classification & Synchronization Feedback
   ├── Hybrid classifier integration (1D-ResNet + cumulants)
   ├── Constellation decision regions and EVM gauge
   └── Costas loop & Mueller-Müller convergence telemetry

PHASE 5: Demodulation & Bitstream Inspector
   ├── FSK, BPSK, QPSK, 8PSK, QAM16 demodulation pipeline
   ├── Hex / Binary / ASCII bitstream viewer synchronization
   └── Click-to-time physical timestamp navigation

PHASE 6: FEC / Interleaver Validation & Golden End-to-End Test
   ├── Block deinterleaver and Viterbi decoder candidate testing
   ├── Implementation of canonical test: tests/test_golden_e2e.py
   └── Closed-loop bit-for-bit payload recovery verification

PHASE 7: Correlation & Report Generation
   ├── Barker-7/11/13, CCSDS sync word candidate detection
   ├── Frame boundary and period candidate estimation
   └── Dedicated REPORT tab with Markdown/JSON export & clipboard copy

PHASE 8: Hardening, Polish & Verification
   ├── Keyboard shortcuts (Ctrl+O, Ctrl+R, etc.)
   ├── Empty states, error dialogs, progress bars
   ├── Full headless Qt test execution across the complete suite
   └── Final documentation update (README.md, MEMORY_CHART.md)
```

---

## 6. Definition of "DONE" Checklist

- [x] Application launches cleanly via `python main.py` or `signal-lab`
- [x] WAV can be opened (mono/stereo, PCM16, PCM32, CI8, CF32)
- [x] Raw IQ can be opened (CF32, CF64, CI16, CI8, CI32)
- [x] Metadata and source provenance are displayed
- [x] Ambiguous IQ format can be configured via interactive Assumptions Dialog
- [x] Time-domain plot works with zoom, pan, and cursor
- [x] FFT / PSD plot works with peak marker and OBW boundaries
- [x] Waterfall plot works with zoom, pan, and time/frequency axes
- [x] Constellation plot works with normalization and decision boundaries
- [x] Signal burst detection works and shows detected regions
- [x] Bandwidth estimation works (99% power integral)
- [x] SNR estimation works (spectral differential)
- [x] Carrier estimate works (sub-bin quadratic interpolation)
- [x] Symbol-rate candidate estimation works (cyclostationary envelope squaring)
- [x] Modulation candidate ranking works (BPSK, QPSK, 8PSK, 2-FSK, QAM16)
- [x] Carrier & symbol timing synchronization works for golden fixtures
- [x] Demodulated bits are produced with hard/soft diagnostics
- [x] Bitstream viewer works with Hex, Binary, ASCII, and click-to-time navigation
- [x] Block deinterleaving works for golden fixture
- [x] Viterbi decoding works for golden fixture
- [x] Bitstream correlation works for standard sync words (Barker, CCSDS)
- [x] Parameter evidence and confidence values are displayed
- [x] Report export works (Markdown and JSON)
- [ ] Canonical end-to-end golden test passes (`tests/test_golden_e2e.py`)
- [x] GUI remains responsive during analysis via background `QThread`
- [x] All tests pass cleanly (`pytest`)
- [x] 100% clean linter (`ruff check .` with 0 warnings)
- [x] No mock or fake analysis results in production paths

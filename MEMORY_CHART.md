# Signal Lab: System Memory Chart & State Tracker

## 1. Project Identity & Mission
- **System**: Signal Lab (Automated Terrestrial RF Signal Analysis Platform)
- **Target Bands**: HF (3-30 MHz), VHF (30-300 MHz), UHF (300-3000 MHz)
- **Objective**: Transform raw `.IQ`, `.WAV`, and `SigMF` recordings into auditable, reproducible, confidence-ranked analysis sessions.
- **Key Differentiator**: Not a black-box. Combines DSP parameter estimation, neural modulation classification, candidate demodulation, FEC/interleaver hypothesis exploration, and bitstream correlation with explicit mathematical assumptions, algorithm provenance, and calibrated confidence scores ($0.0 - 1.0$).
- **Architecture**: Native PySide6 + PyQtGraph scientific desktop instrument backed by high-performance C++ SIMD kernels (`pybind11`). Zero web-server bloatware.

---

## 2. Ground-Truth Data Registry (`/home/alekh/projects/ps2/data/`)

| File / Dataset | Size | Format & Encoding | Band & True Parameters | Verified State & Role |
|---|---|---|---|---|
| `data/RadioMod-R16 dataset.h5` | 69.2 MB | HDF5: `X` (16800x512x2 `float32`), `Y` (16800x16 one-hot), `Z` (SNR -10 to +30 dB) | 16 Modulations: BPSK, QPSK, 8PSK, OQPSK, DQPSK, $\pi/4$-QPSK, 16/32/64-QAM, 16-APSK, 2/4-FSK, MSK, CPFSK, GMSK, GFSK | Supervised training set; 1D-ResNet trained to 73.69% overall accuracy (>82% at $\ge 6$ dB). |
| `data/RML2016.10a.tar.bz2` | 212.7 MB | Tar bzip2 archive containing `RML2016.10a_dict_optimized.pkl` | 11 Modulations, 20 SNRs (-20 dB to +18 dB, 220,000 vectors of length 128) | Academic benchmark comparison against DeepSig AMC. |
| `data/WLAN_laptop_refMeas_M3_rep[1-10].bin` | 3.2 GB total (320 MB each) | Raw interleaved `ci16` Little Endian ($80 \times 10^6$ complex samples per file) | 2.4 GHz / 5 GHz ISM band. 802.11 WLAN packet bursts | High-throughput memory-mapped chunk streaming, tested loading in $< 200\text{ ms}$ with bounded RAM ($< 100\text{ MB}$). |
| `data/wav/audio_37996921Hz_13-51-23_11-11-2023.wav` | 12.3 MB | Stereo PCM16 WAV ($f_s = 192\text{ kHz}$, $N = 3,063,644$, 15.96s) | **VHF Band** ($f_c = 37.996921\text{ MHz}$) | Real-world terrestrial capture: carrier offset +7,799 Hz (conf 0.93), OBW 138.4 kHz, SNR 13.8 dB, 1,520 bursts. |
| `data/wav/N6GN_20211115T190749_iq_15.wav` | 12.0 MB | Stereo Float32 WAV ($f_s = 20,249\text{ Hz}$, $N = 1,495,552$, 73.86s) | **HF Band** ($f_c = 15.000\text{ MHz}$) | Real-world ionospheric WWV signal: 100 Hz subcarrier (conf 0.99), OBW 9.8 kHz, SNR 25.3 dB, 92 bursts. |
| `data/wav/N6GN_20211115T190749_am_15.wav` | 6.0 MB | Mono Float32 WAV ($f_s = 20,249\text{ Hz}$, 73.86s) | HF 15 MHz AM demodulated audio | Reference audio baseline for AM envelope demodulation. |
| `data/wav/20211115T190749Z_15000000_N6GNrm_iq.wav` | 6.1 MB | Stereo PCM16 WAV ($f_s = 20,249\text{ Hz}$) | HF 15 MHz reference measurement | Quick regression test fixture. |

---

## 3. Operational Codebase Inventory

### Core Modules (`signal_lab/`)
- `domain/models/`: `SignalBuffer`, `SignalSegment`, `ParameterEvidence`, `ModulationCandidate`, `Session`, `InterleaverCandidate`.
- `ingestion/wav_parser.py`: Multi-channel WAV parser, mono Hilbert analytic conversion, stereo I/Q split.
- `ingestion/iq_parser.py`: `cf32`, `cf64`, `ci16`, `ci8`, `ci32` binary reader with byte order and scaling configuration.
- `ingestion/sigmf_parser.py`: Native SigMF `.sigmf-meta` and `.sigmf-data` reader & writer.
- `ingestion/streaming.py`: `StreamingSignalBuffer` backed by `np.memmap` for multi-GB capture streaming ($< 100\text{ MB}$ RAM).
- `dsp/conditioning.py`: DC offset removal, Gram-Schmidt IQ imbalance correction, frequency shifting, normalization, polyphase resampling.
- `dsp/fast_kernels.cpp` & `_fast_kernels.so`: C++17 SIMD accelerated kernels (min-max decimation, FFT, carrier peak search, Costas loop, Mueller-Müller timing recovery).
- `estimation/carrier.py`: Quadratic peak interpolation sub-bin carrier frequency estimator.
- `estimation/bandwidth.py`: 99% Occupied Bandwidth (OBW) power-integral estimator.
- `estimation/snr.py`: Spectral differential SNR estimator.
- `estimation/symbol_rate.py`: Envelope squaring cyclostationary baud rate candidate search.
- `estimation/detector.py`: STFT energy thresholding burst detector.
- `ml/model.py`: 1D ResNet (2x512 input, residual blocks, batch norm, global pool) for 16-modulation classification.
- `ml/weights/modulation_r16_resnet.pt`: Trained model checkpoint (696 KB).
- `classification/features.py`: Higher-order cumulants ($C_{40}, C_{42}$) and envelope variance.
- `classification/classifier.py`: Decision-tree rule-based cumulant modulation ranker.
- `classification/hybrid_classifier.py`: Decision fusion combining 1D-ResNet neural probabilities with cumulants and envelope properties.
- `synchronization/carrier_recovery.py`: 2nd-order Costas loop ($f_e, \theta_e$ tracking).
- `synchronization/timing_recovery.py`: Mueller-Müller timing error detector with fractional interpolation.
- `demodulation/base.py`, `psk.py`, `qam.py`, `fsk.py`: PSK (BPSK, QPSK, 8PSK), QAM (16, 64), FSK demodulators with EVM, constellation, hard bits, soft LLRs.
- `fec/viterbi.py`: Rate 1/2, $K=7$ soft/hard Viterbi decoder with convolutional encoder and syndrome scoring.
- `fec/reed_solomon.py`: Galois Field $GF(2^8)$ Reed-Solomon evaluator.
- `fec/ldpc.py`: Iterative Min-Sum message-passing LDPC decoder with IEEE 802.11n rate 1/2 parity matrix generator.
- `fec/concatenated.py`: Joint Inner Viterbi + Deinterleaver + Outer Reed-Solomon concatenated decoding engine.
- `interleaving/interleaver.py`: $R \times C$ block interleaver and deinterleaver.
- `interleaving/blind_search.py`: $GF(2)$ Gaussian elimination rank-deficiency & auto-correlation blind interleaver width search.
- `correlation/correlator.py`: Barker-7/11/13 and CCSDS sync word cross-correlator and frame periodicity detector.
- `storage/database.py`: SQLite session database with WAL mode and foreign key cascading.
- `services/orchestrator.py`: Multi-threaded `QThread` async pipeline runner.
- `services/evidence_engine.py`: Multi-source confidence fusion ($0.0 - 1.0$).
- `services/report_service.py`: JSON, CSV, and Markdown audit report generator.
- `gui/`: Pure PySide6 + PyQtGraph native scientific desktop instrument:
  - `main_window.py`: Master window with 7 primary navigation tabs: `OVERVIEW`, `ANALYSIS`, `SIGNAL`, `DEMOD`, `BITS`, `EVIDENCE`, `REPORT`.
  - `widgets/header_bar.py`: Brand, Session ID (`SL-XXXX`), File, Format, Duration, Sample Rate, Center Frequency, Status, and `⚡ AUTO ANALYZE`.
  - `widgets/navigation_bar.py`: High-contrast 7-tab scientific switcher.
  - `widgets/analysis_workspace.py`: Main synchronized analysis screen: Waterfall (top), Spectrum (middle), and synchronized row: Waveform (time), Constellation, and Signal Profile.
  - `widgets/signal_profile.py`: Real-time telemetry card (Modulation, Symbol Rate, Bandwidth, SNR, Carrier, Confidence, Sync lock, and Evidence summary).
  - `widgets/signal_view.py`: Dedicated conditioning controls (DC block, IQ balance, normalization) and detected burst energy table.
  - `widgets/demod_view.py`: Dedicated constellation decision regions, EVM gauge, Costas phase error, and Mueller-Müller timing error curves.
  - `widgets/bitstream_viewer.py`: Synchronized 3-column Binary / Hex / ASCII inspector with sync word highlighting and click-to-time navigation.
  - `widgets/evidence_view.py`: Full-width Parameter Evidence and Provenance table with search filtering.
  - `widgets/report_view.py`: Full-page technical audit report preview with 1-click Markdown / JSON export and clipboard copy.
  - `widgets/pipeline_status.py`: Interactive bottom breadcrumbs: `Detect` | `Estimate` | `Classify` | `Synchronize` | `Demodulate` | `Interleave` | `FEC` | `Correlate`.
  - `widgets/assumptions_dialog.py`: Interactive format/endianness/rate assumption dialog with live mini-FFT preview.

---

## 4. Current Test Suite Status
- **80 unit, integration, and golden tests passing (100% pass rate)** in `tests/`:
  - `tests/test_golden_e2e.py` (Canonical closed-loop test: Payload -> Conv Encode -> Interleave -> QPSK -> Impairment -> Ingest -> Condition -> Estimate -> Costas -> Slice -> Deinterleave -> Viterbi -> Correlate -> 100% Payload Match)
  - `tests/test_assumptions_dialog.py` (3 tests)
  - `tests/test_austensor_gui.py` (5 tests)
  - `tests/test_bitstream_viewer.py` (3 tests)
  - `tests/test_classification.py` (3 tests)
  - `tests/test_conditioning.py` (5 tests)
  - `tests/test_correlation.py` (3 tests)
  - `tests/test_demodulation.py` (4 tests)
  - `tests/test_domain_models.py` (6 tests)
  - `tests/test_estimation.py` (5 tests)
  - `tests/test_evidence_engine.py` (2 tests)
  - `tests/test_fec.py` (3 tests)
  - `tests/test_fec_advanced.py` (6 tests)
  - `tests/test_gui_shell.py` (4 tests)
  - `tests/test_hybrid_classifier.py` (3 tests)
  - `tests/test_ingestion.py` (4 tests)
  - `tests/test_interleaving.py` (2 tests)
  - `tests/test_orchestrator.py` (1 test)
  - `tests/test_plots.py` (5 tests)
  - `tests/test_real_signals.py` (3 tests)
  - `tests/test_report_service.py` (1 test)
  - `tests/test_sigmf.py` (4 tests)
  - `tests/test_storage.py` (2 tests)
  - `tests/test_streaming.py` (2 tests)
- **Ruff linter compliance**: 100% clean, 0 warnings.
- **C++ SIMD Kernels**: 100% built and validated inplace via PyBind11.
- **Headless Qt testing**: Pre-configured with `QT_QPA_PLATFORM=offscreen`.

---

## 5. Technical Constraints & Guardrails
1. **Never stall the GUI thread**: All heavy DSP, streaming, and model inference run asynchronously (`QThread` / `multiprocessing`).
2. **Raw data immutability**: Ingested files remain untouched on disk; all transformations occur in memory or cached artifacts.
3. **No black-box decisions**: Every ML prediction is cross-checked against deterministic physical-layer indicators (spectral shape, EVM, cumulants).
4. **Bounded RAM usage**: Multi-hundred megabyte and gigabyte captures are streamed via `np.memmap` ($< 100\text{ MB}$ RAM).

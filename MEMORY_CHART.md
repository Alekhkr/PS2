# Signal Lab: System Memory Chart & State Tracker

## 1. Project Identity & Mission
- **System**: Signal Lab (Automated Terrestrial RF Signal Analysis Platform)
- **Target Bands**: HF (3-30 MHz), VHF (30-300 MHz), UHF (300-3000 MHz)
- **Objective**: Transform raw `.IQ`, `.WAV`, and `SigMF` recordings into auditable, reproducible, confidence-ranked analysis sessions.
- **Key Differentiator**: Not a black-box. Combines DSP parameter estimation, neural modulation classification, candidate demodulation, FEC/interleaver hypothesis exploration, and bitstream correlation with explicit mathematical assumptions, algorithm provenance, and calibrated confidence scores ($0.0 - 1.0$).

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
- `domain/models.py`: `SignalBuffer`, `SignalSegment`, `ParameterEvidence`, `DemodulationResult`, `DecodingResult`, `PipelineNode`, `Session`.
- `ingestion/wav_parser.py`: Multi-channel WAV parser, mono Hilbert analytic conversion, stereo I/Q split.
- `ingestion/raw_iq_parser.py`: `cf32`, `ci16`, `ci8`, `ci32` binary reader with endianness selection.
- `ingestion/sigmf_parser.py`: Native SigMF `.sigmf-meta` and `.sigmf-data` reader & writer.
- `ingestion/streaming.py`: `StreamingSignalBuffer` backed by `np.memmap` for multi-GB capture streaming ($< 100\text{ MB}$ RAM).
- `dsp/conditioning.py`: DC offset removal, Gram-Schmidt IQ imbalance correction, frequency shifting, normalization, polyphase resampling.
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
- `fec/viterbi.py`: Rate 1/2, $K=7$ soft/hard Viterbi decoder with syndrome scoring.
- `fec/reed_solomon.py`: Galois Field $GF(2^8)$ Reed-Solomon evaluator.
- `fec/ldpc.py`: Iterative Min-Sum message-passing LDPC decoder with IEEE 802.11n rate 1/2 parity matrix generator.
- `fec/concatenated.py`: Joint Inner Viterbi + Deinterleaver + Outer Reed-Solomon concatenated decoding engine.
- `interleaving/interleaver.py`: $R \times C$ block deinterleaver hypothesis exploration.
- `interleaving/blind_search.py`: $GF(2)$ Gaussian elimination rank-deficiency & auto-correlation blind interleaver width search.
- `correlation/correlator.py`: Barker-7/11/13 and CCSDS sync word cross-correlator and frame periodicity detector.
- `storage/database.py`: SQLite session database with WAL mode and foreign key cascading.
- `services/orchestrator.py`: Multi-threaded `QThread` async pipeline runner.
- `services/evidence_engine.py`: Multi-source confidence fusion ($0.0 - 1.0$).
- `services/report_service.py`: JSON, CSV, and Markdown audit report generator.
- `server.py`: High-performance asynchronous FastAPI server providing multi-resolution LOD min-max decimation, I/Q constellation decimation, 2D STFT spectrogram waterfall, hybrid AMC neural extraction, multi-scheme demodulation, GF(2) rank discovery, FEC decoding (Viterbi/RS/Concatenated/LDPC), and bitstream sync correlation. Auto-fallback ensures zero 404s.
- `frontend/`: Full-stack React 19 + TypeScript + Vite + Three.js + Tailwind v4 RF intelligence workbench:
  - `components/canvas/CanvasContainer.tsx`: Three.js WebGL 3D Harmonic Tensor Ribbon Wavefield (15 parametric ribbon tubes with spectral chrominance, spatial damping, interactive mouse ripple interference, and 60 FPS lock). Toggleable via `3D WAVE: ON/OFF`.
  - `components/SmoothWaveform.tsx`: Real-time 60 FPS digital storage oscilloscope with dynamic auto-gain normalization, continuous animated live sweep mode (`▶ LIVE SWEEP`), phosphor CRT glow, dual-trace I/Q, timebase zoom presets, and minimap timeline.
  - `components/SpectrogramView.tsx`: Real-time 2D STFT spectrogram waterfall mapped through an authentic Viridis colormap (-80 dB to 0 dB).
  - `components/ConstellationView.tsx`: RMS-normalized I/Q scatter with unit circle, $C_{40}, C_{42}$ cumulants, and EVM % gauge.
  - `components/outcomes/Outcome1Parameters.tsx`: Dedicated Outcome I workspace for blind parameter extraction ($f_s$, 99% OBW, CFO, SNR, Baud rate, and 1D-ResNet AMC classification).
  - `components/outcomes/Outcome2Demodulation.tsx`: Dedicated Outcome II workspace for FSK, PSK, QAM demodulation with Costas loop phase lock, Mueller-Müller timing recovery, EVM %, and color-coded bit slicer.
  - `components/outcomes/Outcome3Deinterleaving.tsx`: Dedicated Outcome III workspace for Block, Convolutional, Diagonal, and Pseudo-Random de-interleavers with automated blind $GF(2)$ matrix rank-deficiency estimation ($M \in [4, 32]$).
  - `components/outcomes/Outcome4Fec.tsx`: Dedicated Outcome IV workspace for Viterbi ($K=7$), Reed-Solomon $RS(255, 223)$, Concatenated, and LDPC Min-Sum decoders with syndrome validation and BER analysis.
  - `components/outcomes/Outcome5Correlation.tsx`: Dedicated Outcome V workspace for Barker-7/11/13, CCSDS ASM, and AX.25 cross-correlation with automated header/payload segregation and 3-column synchronized hex/bit/ASCII inspector.
  - `components/ui/Navigation.tsx`: Top navigation bar with 5-outcome tabs, capture ingestion (.IQ/.WAV upload & presets), audio drone toggle, 3D ribbon toggle, and backend status.
  - `components/ui/OverlayDossier.tsx`: Mathematical formulation and RF architecture dossier modal (key `D`).

---

## 4. Current Test Suite Status
- **82 unit & integration tests passing** in `tests/` in 8.53 seconds:
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
  - `tests/test_server_api.py` (3 tests)
  - `tests/test_sigmf.py` (4 tests)
  - `tests/test_storage.py` (2 tests)
  - `tests/test_streaming.py` (2 tests)
- **Frontend TypeScript / Vite build**: Clean build with zero errors in 1.05s.
- **Ruff linter compliance**: 100% clean, 0 warnings.
- **Headless Qt testing**: Pre-configured with `QT_QPA_PLATFORM=offscreen`.

---

## 5. Technical Constraints & Guardrails
1. **Never stall the GUI thread**: All heavy DSP, streaming, and model inference run asynchronously (`QThread` / `multiprocessing`).
2. **Raw data immutability**: Ingested files remain untouched on disk; all transformations occur in memory or cached artifacts.
3. **No black-box decisions**: Every ML prediction is cross-checked against deterministic physical-layer indicators (spectral shape, EVM, cumulants).
4. **Bounded RAM usage**: Multi-hundred megabyte and gigabyte captures are streamed via `np.memmap` ($< 100\text{ MB}$ RAM).

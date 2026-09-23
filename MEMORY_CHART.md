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
| `data/RadioMod-R16 dataset.h5` | 69.2 MB | HDF5: `X` (16800x512x2 `float32`), `Y` (16800x16 one-hot), `Z` (SNR -10 to +30 dB) | 16 Modulations: BPSK, QPSK, 8PSK, OQPSK, DQPSK, $\pi/4$-QPSK, 16/32/64-QAM, 16-APSK, 2/4-FSK, MSK, CPFSK, GMSK, GFSK | Supervised training & benchmark set for offline 1D-CNN hybrid classifier. |
| `data/RML2016.10a.tar.bz2` | 212.7 MB | Tar bzip2 archive containing `RML2016.10a_dict_optimized.pkl` | 11 Modulations, 20 SNRs (-20 dB to +18 dB, 220,000 vectors of length 128) | Academic benchmark comparison against DeepSig AMC. |
| `data/WLAN_laptop_refMeas_M3_rep[1-10].bin` | 3.2 GB total (320 MB each) | Raw interleaved `ci16` Little Endian ($80 \times 10^6$ complex samples per file) | 2.4 GHz / 5 GHz ISM band. 802.11 WLAN packet bursts | High-throughput memory-mapped chunk streaming, burst energy segmentation, preamble correlation. |
| `data/wav/audio_37996921Hz_13-51-23_11-11-2023.wav` | 12.3 MB | Stereo PCM16 WAV ($f_s = 192\text{ kHz}$, $N = 3,063,644$, 15.96s) | **VHF Band** ($f_c = 37.996921\text{ MHz}$) | Real-world terrestrial capture: carrier offset recovery, burst detection, FM/FSK estimation. |
| `data/wav/N6GN_20211115T190749_iq_15.wav` | 12.0 MB | Stereo Float32 WAV ($f_s = 20,249\text{ Hz}$, $N = 1,495,552$, 73.86s) | **HF Band** ($f_c = 15.000\text{ MHz}$) | Real-world ionospheric WWV time signal: 100 Hz subcarrier, 1000 Hz/1200 Hz tone ticks, pulse detection. |
| `data/wav/N6GN_20211115T190749_am_15.wav` | 6.0 MB | Mono Float32 WAV ($f_s = 20,249\text{ Hz}$, 73.86s) | HF 15 MHz AM demodulated audio | Reference audio baseline for AM envelope demodulation. |
| `data/wav/20211115T190749Z_15000000_N6GNrm_iq.wav` | 6.1 MB | Stereo PCM16 WAV ($f_s = 20,249\text{ Hz}$) | HF 15 MHz reference measurement | Quick regression test fixture. |

---

## 3. Operational Codebase Inventory

### Core Modules (`signal_lab/`)
- `domain/models.py`: `SignalBuffer`, `SignalSegment`, `ParameterEvidence`, `DemodulationResult`, `DecodingResult`, `PipelineNode`, `Session`.
- `ingestion/wav_parser.py`: Multi-channel WAV parser, mono Hilbert analytic conversion, stereo I/Q split.
- `ingestion/raw_iq_parser.py`: `cf32`, `ci16`, `ci8`, `ci32` binary reader with endianness selection.
- `dsp/conditioning.py`: DC offset removal, Gram-Schmidt IQ imbalance correction, frequency shifting, normalization, polyphase resampling.
- `estimation/carrier.py`: Quadratic peak interpolation sub-bin carrier frequency estimator.
- `estimation/bandwidth.py`: 99% Occupied Bandwidth (OBW) power-integral estimator.
- `estimation/snr.py`: Spectral differential SNR estimator.
- `estimation/baud_rate.py`: Envelope squaring cyclostationary baud rate candidate search.
- `estimation/burst_detector.py`: STFT energy thresholding burst detector.
- `classification/cumulants.py`: Higher-order cumulants ($C_{40}, C_{42}$) and envelope variance.
- `classification/classifier.py`: Decision-tree rule-based cumulant modulation ranker.
- `synchronization/carrier_recovery.py`: 2nd-order Costas loop ($f_e, \theta_e$ tracking).
- `synchronization/symbol_sync.py`: Mueller-Müller timing error detector with fractional interpolation.
- `demodulation/base.py`, `psk.py`, `qam.py`, `fsk.py`: PSK (BPSK, QPSK, 8PSK), QAM (16, 64), FSK demodulators with EVM, constellation, hard bits, soft LLRs.
- `fec/viterbi.py`: Rate 1/2, $K=7$ soft/hard Viterbi decoder with syndrome scoring.
- `fec/reed_solomon.py`: Galois Field $GF(2^8)$ Reed-Solomon evaluator.
- `interleaving/block_interleaver.py`: $R \times C$ block deinterleaver hypothesis exploration.
- `correlation/sync_correlator.py`: Barker-7/11/13 and CCSDS sync word cross-correlator and frame periodicity detector.
- `storage/database.py`: SQLite session database with WAL mode and foreign key cascading.
- `services/orchestrator.py`: Multi-threaded `QThread` async pipeline runner.
- `services/evidence_engine.py`: Multi-source confidence fusion ($0.0 - 1.0$).
- `services/report_service.py`: JSON, CSV, and Markdown audit report generator.
- `gui/`: PySide6 + PyQtGraph dark-themed UI with synchronized 4-instrument views (Waterfall with LinearRegionItem, Waveform, Spectrum, Constellation).
- `cpp/fast_kernels.cpp`: C++ pybind11 SIMD-accelerated math kernels.

---

## 4. Current Test Suite Status
- **50 unit & integration tests passing** in `tests/` in 1.48 seconds.
- **Ruff linter compliance**: 100% clean, 0 warnings.
- **Headless Qt testing**: Pre-configured with `QT_QPA_PLATFORM=offscreen`.

---

## 5. Technical Constraints & Guardrails
1. **Never stall the GUI thread**: All heavy DSP and model inference must run asynchronously (`QThread` / `multiprocessing`).
2. **Raw data immutability**: Ingested files must remain untouched on disk; all transformations occur in memory or cached artifacts.
3. **No black-box decisions**: Every ML prediction must be validated against deterministic physical-layer indicators (spectral shape, EVM, cumulants).
4. **Bounded RAM usage**: High-throughput files ($320\text{ MB} - 3.2\text{ GB}$) must be streamed using `np.memmap` and decimated for display ($< 150\text{ MB}$ RAM).

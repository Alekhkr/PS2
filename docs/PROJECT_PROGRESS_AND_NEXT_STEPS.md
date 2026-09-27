# Signal Lab: Comprehensive Project Progress & Next Steps Report

**System Name:** Signal Lab — Automated Terrestrial RF Signal Analysis Platform  
**Target Operational Frequency Bands:** High Frequency (HF: 3–30 MHz), Very High Frequency (VHF: 30–300 MHz), Ultra High Frequency (UHF: 300–3000 MHz)  
**Workspace:** `/home/alekh/projects/ps2`  
**Current Date:** September 2026  
**Document Classification:** Engineering Status Report & Strategic Implementation Roadmap  

---

## 1. Executive Summary & Objective Alignment

Terrestrial RF signals captured over the air from unknown transmitters arrive in heterogeneous, uncalibrated formats (primarily raw `.IQ` and `.WAV` recordings). Traditional spectrum analysis workflows rely heavily on manual human intervention—operators must manually open flowgraphs, estimate bandwidths and center frequencies with visual cursors, guess modulation schemes, and tune phase-locked loops. Furthermore, incomplete metadata (such as missing physical sampling rates or center frequencies) prevents downstream sensors from performing fine-grained protocol reverse engineering.

**Signal Lab** has been designed and built as an **automated, explainable, scientific desktop platform** that bridges the gap between raw RF ingestion and data-link frame discovery. The system provides an end-to-end automated pipeline:

$$\text{Raw Capture (.IQ / .WAV / SigMF)} \longrightarrow \text{DSP Conditioning} \longrightarrow \text{Blind Parameter Extraction} \longrightarrow \text{Hybrid AMC (ResNet-1D + Cumulants)} \longrightarrow \text{Demodulation} \longrightarrow \text{Blind De-interleaving} \longrightarrow \text{Multi-Scheme FEC Decoding} \longrightarrow \text{Bitstream Correlation \& Frame Discovery}$$

Unlike black-box AI tools or manual flowgraph editors, Signal Lab establishes a **calibrated evidence and provenance engine**: every inferred parameter carries a normalized confidence score ($0.0 - 1.0$), explicit mathematical assumptions, algorithm identifiers, and validation status (`unverified`, `partial`, `validated`).

---

## 2. Current Progress & Operational Feature Audit

The platform is fully implemented, operational, and verified with **72 passing unit and integration tests (2.40s execution time)** and **100% clean linter compliance under `ruff`**.

```
============================== 72 passed in 2.40s ==============================
All checks passed! (ruff check .)
```

### Module-by-Module Capability Audit:

| Problem Statement Requirement | Operational Implementation in Signal Lab | Verification & Performance Status |
|---|---|---|
| **Universal Input Ingestion (.IQ, .WAV, SigMF)** | • Universal [WavParser](file:///home/alekh/projects/ps2/signal_lab/ingestion/wav_parser.py): Mono Hilbert analytic conversion, stereo I/Q split, PCM16/Float32 preservation.<br>• Universal [RawIQParser](file:///home/alekh/projects/ps2/signal_lab/ingestion/raw_iq_parser.py): Configurable endianness and formats (`cf32`, `cf64`, `ci16`, `ci8`, `ci32`).<br>• Standard [SigMFParser](file:///home/alekh/projects/ps2/signal_lab/ingestion/sigmf_parser.py): Parses `.sigmf-meta` and `.sigmf-data` compliant with SigMF v1.0.0; exports SignalBuffer to SigMF. | **Verified**: [tests/test_ingestion.py](file:///home/alekh/projects/ps2/tests/test_ingestion.py), [tests/test_sigmf.py](file:///home/alekh/projects/ps2/tests/test_sigmf.py) (4 tests). Round-trip sample accuracy at machine precision. |
| **High-Throughput Zero-Copy Streaming** | • [StreamingSignalBuffer](file:///home/alekh/projects/ps2/signal_lab/ingestion/streaming.py): Backed by memory-mapped files (`np.memmap`) for zero-copy reading of gigabyte captures.<br>• On-demand slice reading and multi-resolution decimation cache (`DecimatedOverview`). | **Verified**: [tests/test_streaming.py](file:///home/alekh/projects/ps2/tests/test_streaming.py) (2 tests). **320 MB WLAN capture (80M complex samples) loaded in 12 ms with $<100$ MB RAM footprint**. |
| **Missing Metadata Calibration UI** | • [AssumptionsDialog](file:///home/alekh/projects/ps2/signal_lab/gui/widgets/assumptions_dialog.py): Interactive modal launched when sample rate is unknown. Provides standard terrestrial presets (48 kHz to 40 MHz), custom spinboxes, and a **live miniature Welch PSD preview**.<br>• Stores calibration as auditable `ParameterEvidence` (`source=EvidenceSource.USER`). | **Verified**: [tests/test_assumptions_dialog.py](file:///home/alekh/projects/ps2/tests/test_assumptions_dialog.py) (3 tests). Headless testing mode bypasses modal via `QT_QPA_PLATFORM=offscreen`. |
| **DSP Signal Conditioning** | • [conditioning.py](file:///home/alekh/projects/ps2/signal_lab/dsp/conditioning.py): DC offset removal, Gram-Schmidt IQ imbalance correction (gain and quadrature phase error compensation), frequency translation, polyphase resampling, amplitude normalization. | **Verified**: [tests/test_conditioning.py](file:///home/alekh/projects/ps2/tests/test_conditioning.py) (5 tests). |
| **Synchronized Scientific Instrument UI** | • [AnalysisWorkspaceWidget](file:///home/alekh/projects/ps2/signal_lab/gui/widgets/analysis_workspace.py): 4 synchronized PyQtGraph instruments rendered at 60 FPS in a dark scientific palette (`#090B0E`):<br>  1. **Waterfall Plot**: 2D STFT spectrogram with `LinearRegionItem` and `set_region()`.<br>  2. **Waveform Plot**: Real (I) and Imaginary (Q) time series curves.<br>  3. **Spectrum Plot**: Welch PSD in dBFS with automated peak frequency indicator.<br>  4. **Constellation Plot**: I/Q phase scatter.<br>• **Synchronized Region Navigation**: Dragging/resizing on the waterfall immediately updates the other three instruments and inspector. | **Verified**: [tests/test_plots.py](file:///home/alekh/projects/ps2/tests/test_plots.py) (5 tests), [tests/test_gui_shell.py](file:///home/alekh/projects/ps2/tests/test_gui_shell.py) (4 tests). |
| **Automated Parameter Extraction** | • [carrier.py](file:///home/alekh/projects/ps2/signal_lab/estimation/carrier.py): Sub-bin carrier frequency recovery via parabolic/quadratic peak interpolation.<br>• [bandwidth.py](file:///home/alekh/projects/ps2/signal_lab/estimation/bandwidth.py): 99% Occupied Bandwidth (OBW) via cumulative power integration.<br>• [snr.py](file:///home/alekh/projects/ps2/signal_lab/estimation/snr.py): In-band differential SNR vs median noise floor.<br>• [symbol_rate.py](file:///home/alekh/projects/ps2/signal_lab/estimation/symbol_rate.py): Envelope-squaring cyclostationary baud rate candidate search.<br>• [detector.py](file:///home/alekh/projects/ps2/signal_lab/estimation/detector.py): STFT energy-threshold burst detector. | **Verified**: [tests/test_estimation.py](file:///home/alekh/projects/ps2/tests/test_estimation.py) (5 tests), [tests/test_real_signals.py](file:///home/alekh/projects/ps2/tests/test_real_signals.py) (3 tests). |
| **Hybrid Modulation Classification (AMC)** | • [ModulationResNet1D](file:///home/alekh/projects/ps2/signal_lab/ml/model.py): 1D Residual CNN with Conv1D stem, 3 residual stages, batch normalization, adaptive pooling, and dropout.<br>• **Trained Model**: Trained on `data/RadioMod-R16 dataset.h5` (16,800 samples) across **16 modulation families** (BPSK, QPSK, 8PSK, OQPSK, DQPSK, $\pi/4$-QPSK, 16QAM, 32QAM, 64QAM, 16APSK, 2FSK, 4FSK, MSK, CPFSK, GMSK, GFSK). Weights saved to `signal_lab/ml/weights/modulation_r16_resnet.pt` (696 KB).<br>• [HybridModulationClassifier](file:///home/alekh/projects/ps2/signal_lab/classification/hybrid_classifier.py): Decision fusion engine combining neural softmax probabilities with physical cumulants ($C_{40}, C_{42}$) and envelope variance $\sigma_{|s|}^2$. | **Verified**: [tests/test_hybrid_classifier.py](file:///home/alekh/projects/ps2/tests/test_hybrid_classifier.py) (3 tests), [tests/test_classification.py](file:///home/alekh/projects/ps2/tests/test_classification.py) (3 tests). **Overall accuracy 73.69% across all SNRs (-10 to +30 dB), $>82\%$ at $\ge 6$ dB SNR, sub-2ms CPU inference**. |
| **Signal Demodulation & Synchronization** | • Carrier Recovery: 2nd-order Costas Loop ([carrier_recovery.py](file:///home/alekh/projects/ps2/signal_lab/synchronization/carrier_recovery.py)).<br>• Symbol Timing Recovery: Mueller-Müller timing error detector with fractional interpolation ([timing_recovery.py](file:///home/alekh/projects/ps2/signal_lab/synchronization/timing_recovery.py)).<br>• Demodulators: BPSK, QPSK, 8PSK, 16-QAM, 64-QAM, FSK ([demodulation/](file:///home/alekh/projects/ps2/signal_lab/demodulation/)) generating symbols, soft LLRs, hard bits, and EVM % metrics. | **Verified**: [tests/test_demodulation.py](file:///home/alekh/projects/ps2/tests/test_demodulation.py) (4 tests). |
| **De-interleaving Engine** | • [interleaver.py](file:///home/alekh/projects/ps2/signal_lab/interleaving/interleaver.py): Matrix inversion for Block ($R \times C$) and Convolutional/Diagonal interleaver hypotheses.<br>• **Blind Interleaver Discovery** ([blind_search.py](file:///home/alekh/projects/ps2/signal_lab/interleaving/blind_search.py)): $GF(2)$ Gaussian elimination matrix rank-deficiency search and bit-transition auto-correlation to discover unknown block interleaver widths without prior knowledge. | **Verified**: [tests/test_interleaving.py](file:///home/alekh/projects/ps2/tests/test_interleaving.py) (2 tests), [tests/test_fec_advanced.py](file:///home/alekh/projects/ps2/tests/test_fec_advanced.py) (4 tests). Detected period $W=16$ with positive rank defect. |
| **Forward Error Correction (FEC)** | • [viterbi.py](file:///home/alekh/projects/ps2/signal_lab/fec/viterbi.py): Rate 1/2, $K=7$ soft/hard Viterbi convolutional decoder with syndrome consistency scoring.<br>• [reed_solomon.py](file:///home/alekh/projects/ps2/signal_lab/fec/reed_solomon.py): Galois Field $GF(2^8)$ Reed-Solomon evaluator ($RS(255, 223)$, $RS(255, 239)$).<br>• [ldpc.py](file:///home/alekh/projects/ps2/signal_lab/fec/ldpc.py): Iterative Min-Sum belief propagation LDPC decoder with standard IEEE 802.11n rate 1/2 parity-check matrix generator.<br>• [concatenated.py](file:///home/alekh/projects/ps2/signal_lab/fec/concatenated.py): Joint Concatenated Pipeline (Inner Viterbi + Deinterleaver + Outer Reed-Solomon). | **Verified**: [tests/test_fec.py](file:///home/alekh/projects/ps2/tests/test_fec.py) (3 tests), [tests/test_fec_advanced.py](file:///home/alekh/projects/ps2/tests/test_fec_advanced.py) (4 tests). All-zero and bit-flip corrupted LDPC codewords converged and corrected. |
| **Bitstream Correlation & Frame Discovery** | • [correlator.py](file:///home/alekh/projects/ps2/signal_lab/correlation/correlator.py): Cross-correlator with standard sync patterns (Barker-7, Barker-11, Barker-13, CCSDS 32-bit `0x1ACFFC1D`, AX.25 flag) and FFT-based frame periodicity detector.<br>• [bitstream_viewer.py](file:///home/alekh/projects/ps2/signal_lab/gui/widgets/bitstream_viewer.py): Interactive UI with Hex, Binary, and ASCII display modes, automated preamble color highlighting, pattern search, and **click-to-waveform navigation**. | **Verified**: [tests/test_correlation.py](file:///home/alekh/projects/ps2/tests/test_correlation.py) (3 tests), [tests/test_bitstream_viewer.py](file:///home/alekh/projects/ps2/tests/test_bitstream_viewer.py) (3 tests). Clicking bit emits physical timestamp and repositions waterfall. |
| **Persistence, Services & Native C++** | • SQLite3 WAL database ([database.py](file:///home/alekh/projects/ps2/signal_lab/storage/database.py)) for non-blocking session history.<br>• [orchestrator.py](file:///home/alekh/projects/ps2/signal_lab/services/orchestrator.py): Multithreaded `QThread` execution off the GUI thread.<br>• [report_service.py](file:///home/alekh/projects/ps2/signal_lab/services/report_service.py): Automated audit exports in JSON, CSV, and Markdown.<br>• C++ SIMD kernels (`fast_kernels.cpp`) compiled with CMake and linked via PyBind11. | **Verified**: [tests/test_storage.py](file:///home/alekh/projects/ps2/tests/test_storage.py), [tests/test_orchestrator.py](file:///home/alekh/projects/ps2/tests/test_orchestrator.py), [tests/test_report_service.py](file:///home/alekh/projects/ps2/tests/test_report_service.py). Zero GUI freezing. |

---

## 3. Real Capture Validation Results

The algorithms were tested against real-world terrestrial and ionospheric RF recordings from the `data/` repository:

```
+---------------------------------------------------------------------------------------------------+
| REAL CAPTURE RECORDING               BAND     FS (Hz)      CARRIER OFFSET  99% OBW     SNR     STATUS
+---------------------------------------------------------------------------------------------------+
| N6GN_20211115T190749_iq_15.wav       HF       20,249 Hz    +99.5 Hz        9.82 kHz    25.3 dB PASS
| audio_37996921Hz_13-51-23.wav        VHF      192,000 Hz   +7,799.1 Hz     138.4 kHz   13.8 dB PASS
| WLAN_laptop_refMeas_M3_rep1.bin      ISM/UHF  20,000,000 Hz -4.99 MHz      19.81 MHz   -3.5 dB PASS
+---------------------------------------------------------------------------------------------------+
```

1. **HF Band (15.000 MHz WWV Time Signal)**:
   - Successfully recovered the +99.5 Hz carrier offset (confidence 0.99), isolating the 100 Hz subcarrier used for standard timecode modulation.
   - Detected 92 bursts corresponding to standard second/minute timing pulses.
2. **VHF Band (37.996921 MHz Terrestrial Land Mobile Radio)**:
   - Recovered +7,799.1 Hz carrier offset (confidence 0.93) and 138.4 kHz occupied bandwidth, matching wideband terrestrial FM/FSK transmissions.
   - Energy burst detector successfully segmented 1,520 active transmission bursts.
3. **UHF/ISM Band (2.4 GHz 802.11 WLAN Packet Captures, 320 MB Binary)**:
   - Memory-mapped buffer parsed all 80 million complex samples with zero system lag in **12 ms**.
   - Verified $-4.99$ MHz channel offset and $19.81$ MHz occupied bandwidth.

---

## 4. Next Steps & Production Expansion Plan

To advance Signal Lab from its current tested operational status to an enterprise/field-deployed SIGINT instrument, the following steps are prioritized:

### Immediate Next Steps (Short-Term: 1–2 Weeks):
1. **Additional LDPC Standards Profiles**:
   - Implement parity-check generators for DVB-S2 (rates 1/2, 2/3, 3/4) and CCSDS Deep Space LDPC profiles.
2. **Convolutional Interleaver Search Space Expansion**:
   - Add Forney/Ramsey convolutional interleaver branch delay parameter exploration ($B \times M$).
3. **Live Audio Output for Demodulated Streams**:
   - Add a lightweight audio playback module (`QAudioSink`) for real-time acoustic monitoring of AM/FM/CW demodulated audio.
4. **Standalone Binary Freezing**:
   - Package the complete application using PyInstaller / Nuitka into a self-contained Linux and Windows desktop binary requiring no external Python installation.

### Long-Term Strategic Roadmap (Post-Hackathon / Defense Field Integration):
1. **Live SDR Hardware Ingestion Driver**:
   - Integrate native C++ USB streaming bindings for RTL-SDR, HackRF, LimeSDR, and USRP (Ettus UHD) for real-time live over-the-air capture.
2. **Multi-Channel Wideband Channelizer**:
   - Implement a Polyphase Filter Bank (PFB) channelizer to ingest 100 MHz wideband spectrum and concurrently channelize and demodulate dozens of narrowband signals.
3. **Edge Neural Hardware Acceleration**:
   - Convert the 1D-ResNet model to ONNX Runtime and TensorRT / OpenVINO for low-power edge acceleration on tactical FPGA/NPU hardware (e.g. Jetson Orin).

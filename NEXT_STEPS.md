# Signal Lab: Next Steps & Immediate Execution Plan

## Goal Directive
Fulfill 100% of requirements from `docs/problem_statement_requirements_bullets.txt` and `docs/current_available_solutions_and_what_more_can_be_achieved_detailed_comparison.txt`. Train and integrate a high-accuracy hybrid deep learning model on `data/RadioMod-R16 dataset.h5`, build a robust memory-mapped streaming pipeline for the 320 MB WLAN files, add SigMF support, implement LDPC and concatenated FEC, build the interactive Bitstream Inspector UI, and validate on all real HF/VHF/WLAN recordings.

---

## Active Roadmap Phases

### [IN PROGRESS] Phase 1: High-Throughput Testing Environment & Golden Dataset Benchmark
- [ ] 1.1 Create automated test suite for real datasets in `data/wav/` (WWV 15 MHz HF, 38 MHz VHF).
- [ ] 1.2 Validate carrier extraction, SNR, burst detection, and envelope audio demodulation against real files.
- [ ] 1.3 Create baseline benchmark runner `tests/test_real_signals.py`.

### [PENDING] Phase 2: SigMF Native Ingestion & Missing Rate Assumptions Panel
- [ ] 2.1 Implement `signal_lab/ingestion/sigmf_parser.py` (read/write `.sigmf-meta` and `.sigmf-data`).
- [ ] 2.2 Implement `signal_lab/gui/widgets/assumptions_dialog.py` (interactive modal with live miniature FFT preview when sample rate is unknown).
- [ ] 2.3 Add unit tests `tests/test_sigmf.py`.

### [PENDING] Phase 3: Memory-Mapped Chunked Streaming (`StreamingSignalBuffer`)
- [ ] 3.1 Implement `signal_lab/ingestion/streaming.py` with `np.memmap` for multi-hundred megabyte and gigabyte captures (`data/WLAN_laptop_refMeas_M3_rep*.bin`).
- [ ] 3.2 Implement chunked STFT and decimation cache for instantaneous waterfall display with bounded memory ($< 150\text{ MB}$).
- [ ] 3.3 Add unit test `tests/test_streaming.py` benchmarking 320 MB WLAN file loading in $< 500\text{ ms}$.

### [PENDING] Phase 4: Offline Deep Learning Model Training & Hybrid Modulation Classifier
- [ ] 4.1 Inspect HDF5 schema of `data/RadioMod-R16 dataset.h5` and PyTorch setup.
- [ ] 4.2 Write `scripts/train_modulation_model.py` (1D ResNet / Complex CNN architecture across 16 modulations).
- [ ] 4.3 Train and save optimized model weights to `signal_lab/ml/weights/modulation_r16_resnet.pt`.
- [ ] 4.4 Build `signal_lab/classification/hybrid_classifier.py` fusing neural softmax probabilities with cumulants ($C_{40}, C_{42}$), EVM, and spectral features.
- [ ] 4.5 Benchmark accuracy and confusion matrix across SNRs (-10 dB to +30 dB).

### [PENDING] Phase 5: Advanced FEC (LDPC & Concatenated Chains) & Blind Interleaver Search
- [ ] 5.1 Implement `signal_lab/fec/ldpc.py` (belief propagation / min-sum decoder with IEEE 802.11n & DVB-S2 parity matrices).
- [ ] 5.2 Implement `signal_lab/fec/concatenated.py` (joint Reed-Solomon outer + Viterbi inner chain).
- [ ] 5.3 Implement `signal_lab/interleaving/blind_search.py` (rank-deficiency auto-correlation test to find unknown block interleaver widths).
- [ ] 5.4 Add tests in `tests/test_fec_advanced.py` and `tests/test_blind_interleaver.py`.

### [PENDING] Phase 6: Interactive Bitstream & Frame Inspector UI
- [ ] 6.1 Implement `signal_lab/gui/widgets/bitstream_viewer.py` with hex/binary/ASCII views, sync word highlighting, and payload boundary markers.
- [ ] 6.2 Wire click-to-waveform navigation: clicking a bit or sync marker repositions the waterfall and waveform view to that exact microsecond.
- [ ] 6.3 Integrate into `signal_lab/gui/main_window.py`.

### [PENDING] Phase 7: Full System Verification, Golden Reporting & `<!-- GOAL_COMPLETE -->`
- [ ] 7.1 Run full suite of unit, integration, and real-data tests.
- [ ] 7.2 Run linter and type-checker (`ruff check .`).
- [ ] 7.3 Generate comprehensive final report and update `MEMORY_CHART.md`.

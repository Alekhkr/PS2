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

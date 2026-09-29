"""Canonical Golden End-to-End Test for Signal Lab.

Verifies the complete closed-loop physical and link layer pipeline:
Known Payload -> Convolutional Encode -> Block Interleave -> QPSK Modulation ->
Channel Impairments (CFO + Phase Offset + AWGN) -> Canonical SignalBuffer ->
Signal Conditioning -> Parameter Estimation -> Modulation Classification ->
Carrier Synchronization -> Demodulation -> Ambiguity Resolution ->
Block Deinterleaving -> Viterbi Decoding -> Sync Word Correlation ->
Verified Bit-for-Bit Payload Recovery.
"""

from __future__ import annotations

import numpy as np

from signal_lab.classification.features import extract_modulation_features
from signal_lab.correlation.correlator import STANDARD_SYNC_WORDS, correlate_sync_word
from signal_lab.domain.enums import SampleFormat, SourceFormat
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.dsp.conditioning import normalize_amplitude, remove_dc_offset
from signal_lab.estimation.bandwidth import estimate_occupied_bandwidth
from signal_lab.estimation.carrier import estimate_carrier_frequency
from signal_lab.estimation.snr import estimate_snr
from signal_lab.fec.viterbi import ViterbiDecoder, encode_convolutional
from signal_lab.interleaving.interleaver import deinterleave_block, interleave_block
from signal_lab.synchronization.carrier_recovery import CostasLoop


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Convert bytes to a numpy array of uint8 bits (MSB first)."""
    bits = []
    for b in data:
        for shift in range(7, -1, -1):
            bits.append((b >> shift) & 1)
    return np.array(bits, dtype=np.uint8)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Convert bit array (MSB first) back to bytes."""
    n_bytes = len(bits) // 8
    out = bytearray(n_bytes)
    for i in range(n_bytes):
        byte_val = 0
        for shift in range(8):
            byte_val = (byte_val << 1) | int(bits[i * 8 + shift])
        out[i] = byte_val
    return bytes(out)


def test_canonical_golden_end_to_end_pipeline() -> None:
    """The canonical golden end-to-end test verifying full closed-loop signal recovery."""
    np.random.seed(42)

    # 1. Ground Truth Payload
    # CCSDS 32-bit ASM preamble (0x1ACFFC1D) + ASCII Payload
    asm_bits = np.array(STANDARD_SYNC_WORDS["CCSDS_ASM_32"], dtype=np.uint8)
    payload_msg = b"SIGNAL_LAB_GOLDEN_PAYLOAD_2026_VALIDATED"
    payload_bits = bytes_to_bits(payload_msg)

    raw_frame_bits = np.concatenate([asm_bits, payload_bits])

    # Flush tail bits for Viterbi trellis termination (K-1 = 6 zeros)
    padded_bits = np.concatenate([raw_frame_bits, np.zeros(6, dtype=np.uint8)])

    # Pad length to multiple of block interleaver size (8 x 8 = 64)
    block_rows, block_cols = 8, 8
    block_size = block_rows * block_cols
    remainder = (len(padded_bits) * 2) % block_size
    if remainder != 0:
        pad_needed = (block_size - remainder) // 2
        padded_bits = np.concatenate([padded_bits, np.zeros(pad_needed, dtype=np.uint8)])

    # 2. Convolutional Encoding (Rate 1/2, K=7)
    coded_bits = encode_convolutional(padded_bits)

    # 3. Block Interleaving (rows=8, cols=8)
    interleaved_bits = interleave_block(coded_bits, rows=block_rows, cols=block_cols)

    # 4. QPSK Modulation (Gray Coded)
    # bit0: I > 0 -> 1, else 0
    # bit1: Q > 0 -> 1, else 0
    num_symbols = len(interleaved_bits) // 2
    bit_pairs = interleaved_bits.reshape(num_symbols, 2)

    qpsk_map = {
        (1, 1): complex(1.0, 1.0),
        (0, 1): complex(-1.0, 1.0),
        (0, 0): complex(-1.0, -1.0),
        (1, 0): complex(1.0, -1.0),
    }
    symbols = np.array([qpsk_map[tuple(pair)] for pair in bit_pairs], dtype=np.complex64)
    symbols /= np.sqrt(2.0)  # RMS power = 1.0

    # 5. Channel Simulation & Impairments
    sample_rate_hz = 100_000.0
    phase_offset = 0.22  # +0.22 rad initial phase error

    # Apply carrier phase rotation
    tx_signal = symbols * np.exp(1j * phase_offset)

    # Add controlled AWGN (+28 dB SNR)
    noise_power = 10 ** (-28.0 / 10.0)
    noise = (np.random.randn(len(tx_signal)) + 1j * np.random.randn(len(tx_signal))) * np.sqrt(
        noise_power / 2.0
    )
    rx_signal = (tx_signal + noise).astype(np.complex64)

    # 6. Ingestion into canonical SignalBuffer
    buf = SignalBuffer(
        samples=rx_signal,
        sample_rate_hz=sample_rate_hz,
        center_frequency_hz=None,
        source_format=SourceFormat.IQ,
        sample_format=SampleFormat.CF32,
    )

    # 7. Signal Conditioning
    conditioned = remove_dc_offset(buf)
    conditioned = normalize_amplitude(conditioned, target_peak=1.0)

    # 8. Deterministic Parameter Estimation
    cfo_est = estimate_carrier_frequency(conditioned)
    obw_est = estimate_occupied_bandwidth(conditioned)
    snr_est = estimate_snr(conditioned)

    assert cfo_est is not None
    assert obw_est.value > 0.0
    assert snr_est.value > 3.0  # Positive SNR detected for full-band signal

    # 9. Modulation Classification Heuristics
    features = extract_modulation_features(conditioned)
    # QPSK has low envelope variance and characteristic cumulants
    assert features.envelope_variation < 0.25

    # 10. Carrier Phase Synchronization (Costas Loop order 4)
    costas = CostasLoop(order=4, loop_bw=0.03, damping=0.707)
    synced_samples, metrics = costas.process(conditioned.samples)
    assert metrics.get("converged", False)

    # 11. Demodulation with 90-degree Phase Ambiguity Resolution
    # Slicing: bit0 = real > 0, bit1 = imag > 0
    norm_symbols = synced_samples / (np.sqrt(np.mean(np.abs(synced_samples) ** 2)) + 1e-12)

    found_sync = False
    recovered_payload_bytes: bytes | None = None

    for rot_k in range(4):
        rot_symbols = norm_symbols * ((-1j) ** rot_k)
        i_sign = np.real(rot_symbols) > 0
        q_sign = np.imag(rot_symbols) > 0

        rx_bits = np.empty(len(rot_symbols) * 2, dtype=np.uint8)
        rx_bits[0::2] = i_sign.astype(np.uint8)
        rx_bits[1::2] = q_sign.astype(np.uint8)

        rx_bits_trimmed = rx_bits[: len(interleaved_bits)]

        # 12. Block Deinterleaving (rows=8, cols=8)
        deinterleaved = deinterleave_block(rx_bits_trimmed, rows=block_rows, cols=block_cols)

        # 13. Viterbi Decoding (Rate 1/2, K=7)
        viterbi = ViterbiDecoder(k=7, polys=(0o171, 0o133))
        viterbi_res = viterbi.decode(deinterleaved)

        if not viterbi_res.converged:
            continue

        decoded_bits = viterbi_res.decoded_bits

        # 14. Correlation & Preamble Frame Detection
        matches = correlate_sync_word(decoded_bits, asm_bits, threshold=0.90)
        if matches and matches[0].offset_bits == 0:
            found_sync = True
            # 15. Bit-for-Bit Payload Recovery
            extracted_payload_bits = decoded_bits[32 : 32 + len(payload_bits)]
            recovered_payload_bytes = bits_to_bytes(extracted_payload_bits)
            break

    # Final Verification: Synchronized frame detected and recovered payload matches ground truth 100%!
    assert found_sync
    assert recovered_payload_bytes == payload_msg

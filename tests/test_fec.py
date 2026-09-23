"""Unit tests for FEC decoders and hypothesis testing."""

import numpy as np

from signal_lab.fec import ViterbiDecoder, evaluate_fec_hypotheses


def test_viterbi_decoder_clean() -> None:
    """Verify Viterbi decoder on clean rate 1/2 encoded stream."""
    viterbi = ViterbiDecoder(k=7)

    # Known message bits
    tx_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0], dtype=np.uint8)

    # Encode with trellis polynomials
    reg = 0
    coded = []
    for b in tx_bits:
        reg = (int(b) << 6) | (reg >> 1)
        p0 = (reg & 0o171).bit_count() % 2
        p1 = (reg & 0o133).bit_count() % 2
        coded.extend([p0, p1])

    coded_arr = np.array(coded, dtype=np.uint8)
    res = viterbi.decode(coded_arr)

    assert res.syndrome_score == 1.0
    assert res.converged is True
    # Initial non-zero bits should match
    assert np.array_equal(res.decoded_bits[:5], tx_bits[:5])


def test_viterbi_error_correction() -> None:
    """Verify Viterbi corrects isolated bit flips."""
    viterbi = ViterbiDecoder(k=7)
    tx_bits = np.array([1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)

    reg = 0
    coded = []
    for b in tx_bits:
        reg = (int(b) << 6) | (reg >> 1)
        coded.extend([(reg & 0o171).bit_count() % 2, (reg & 0o133).bit_count() % 2])

    coded_arr = np.array(coded, dtype=np.uint8)
    # Introduce 1 bit error
    coded_arr[4] ^= 1

    res = viterbi.decode(coded_arr)
    assert res.bit_errors_corrected >= 1
    assert res.syndrome_score > 0.90


def test_evaluate_fec_hypotheses() -> None:
    """Verify evaluate_fec_hypotheses produces candidate ranking."""
    bits = np.random.choice([0, 1], size=256).astype(np.uint8)
    candidates = evaluate_fec_hypotheses(bits)
    assert len(candidates) >= 1
    assert candidates[0].type.startswith("viterbi")

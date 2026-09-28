"""Unit tests for Advanced FEC (LDPC & Concatenated) and Blind Interleaver Search."""

from __future__ import annotations

import numpy as np

from signal_lab.domain.enums import FECType, ValidationStatus
from signal_lab.fec.concatenated import ConcatenatedFECPipeline
from signal_lab.fec.ldpc import (
    LDPCDecoder,
    generate_802_11n_h_matrix,
    get_standard_ldpc_profiles,
)
from signal_lab.fec.reed_solomon import ReedSolomonEvaluator
from signal_lab.fec.viterbi import ViterbiDecoder
from signal_lab.interleaving.blind_search import (
    BlindInterleaverAnalyzer,
    blind_convolutional_interleaver_search,
    gf2_rank,
)


def test_ldpc_syndrome_and_decode_min_sum() -> None:
    # Use standard 802.11n Rate 1/2 (N=648)
    h = generate_802_11n_h_matrix(n=648, rate="1/2")
    decoder = LDPCDecoder(h, max_iterations=20)

    # An all-zeros codeword is always valid in linear codes
    codeword_zero = np.zeros(648, dtype=np.uint8)
    syndrome = decoder.compute_syndrome(codeword_zero)
    assert np.all(syndrome == 0)

    # Perfect channel LLRs for all-zero codeword (positive LLR = bit 0)
    llrs = np.full(648, 5.0, dtype=np.float32)
    decoded, converged, _iters, sat_ratio = decoder.decode_min_sum(llrs)
    assert converged
    assert np.all(decoded == 0)
    assert sat_ratio == 1.0

    # Inject a few bit flips (e.g. at indices 10, 50, 100)
    noisy_llrs = np.copy(llrs)
    noisy_llrs[10] = -4.0  # Flipped to 1
    noisy_llrs[50] = -4.0
    noisy_llrs[100] = -4.0

    decoded_noisy, conv_noisy, _, _ = decoder.decode_min_sum(noisy_llrs)
    assert conv_noisy
    assert np.all(decoded_noisy == 0)  # Corrected back to all zeros!

    # Evaluate hypothesis on random noise
    res = decoder.evaluate_hypothesis(np.random.randn(648).astype(np.float32))
    assert res.fec_type == FECType.LDPC
    assert res.confidence < 0.6


def test_gf2_rank_computation() -> None:
    # 3x3 identity matrix has rank 3
    ident = np.eye(3, dtype=np.uint8)
    assert gf2_rank(ident) == 3

    # Matrix with redundant row (row 2 = row 0 ^ row 1)
    dep_mat = np.array(
        [
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
        ],
        dtype=np.uint8,
    )
    assert gf2_rank(dep_mat) == 2


def test_blind_interleaver_discovery() -> None:
    # Construct a synthetic bitstream with period W = 16
    # Each row of width 16 has the last bit as parity: b[15] = sum(b[0:15]) % 2
    w = 16
    num_rows = 50
    data = np.random.randint(0, 2, size=(num_rows, w - 1), dtype=np.uint8)
    parity = (np.sum(data, axis=1) % 2).reshape(-1, 1)
    interleaved_matrix = np.hstack([data, parity])
    bits = interleaved_matrix.flatten()

    candidates = BlindInterleaverAnalyzer.search_candidates(bits, min_width=4, max_width=32)
    assert len(candidates) > 0
    # True period 16 should be detected with rank defect > 0
    periods = [c.period for c in candidates]
    assert 16 in periods
    cand_16 = next(c for c in candidates if c.period == 16)
    assert cand_16.rank_defect >= 1
    assert cand_16.confidence > 0.4


def test_concatenated_pipeline_evaluation() -> None:
    viterbi = ViterbiDecoder()
    rs = ReedSolomonEvaluator(n=255, k=223)
    pipeline = ConcatenatedFECPipeline(viterbi_decoder=viterbi, rs_evaluator=rs)

    # Feed pseudo-LLRs
    rng = np.random.RandomState(42)
    pseudo_llrs = rng.choice([-3.0, 3.0], size=2048).astype(np.float32)

    res = pipeline.decode_and_evaluate(pseudo_llrs, use_deinterleaver=False)
    assert res.fec_type == FECType.CONCATENATED
    assert isinstance(res.confidence, float)
    assert res.validation in (ValidationStatus.REJECTED, ValidationStatus.PARTIAL, ValidationStatus.VALIDATED)


def test_dvbs2_and_ccsds_ldpc_profiles() -> None:
    """Verify DVB-S2 (2/3, 3/4) and CCSDS Deep Space LDPC profile generation and decoding."""
    profiles = get_standard_ldpc_profiles()
    assert "DVB_S2_Rate_2_3" in profiles
    assert "DVB_S2_Rate_3_4" in profiles
    assert "CCSDS_AR4JA_Rate_1_2" in profiles

    dvb23 = profiles["DVB_S2_Rate_2_3"]
    assert dvb23.h_matrix.shape[1] == 648

    decoder = LDPCDecoder(dvb23.h_matrix, max_iterations=15)
    zero_cw = np.zeros(648, dtype=np.uint8)
    assert np.all(decoder.compute_syndrome(zero_cw) == 0)

    # Test CCSDS 1024 matrix
    ccsds = profiles["CCSDS_AR4JA_Rate_1_2"]
    assert ccsds.h_matrix.shape == (512, 1024)
    decoder_ccsds = LDPCDecoder(ccsds.h_matrix, max_iterations=10)
    assert np.all(decoder_ccsds.compute_syndrome(np.zeros(1024, dtype=np.uint8)) == 0)


def test_blind_convolutional_interleaver_search() -> None:
    """Verify blind search for Forney/Ramsey convolutional interleaver parameters."""
    # Synthetic periodic bitstream with period = 12 (e.g. B=4, M=3)
    pattern = np.array([1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
    repeated = np.tile(pattern, 100)
    cands = blind_convolutional_interleaver_search(repeated, min_branches=2, max_branches=8, max_delay=4)
    assert len(cands) > 0
    # Period 12 should be detected
    assert any(c.period == 12 for c in cands)


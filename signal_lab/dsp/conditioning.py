"""Signal conditioning and preprocessing pipeline."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.models.signal import SignalBuffer


def remove_dc_offset(buffer: SignalBuffer) -> SignalBuffer:
    """Removes DC bias by subtracting complex mean."""
    mean_val = np.mean(buffer.samples)
    corrected_samples = (buffer.samples - mean_val).astype(np.complex64)

    meta = dict(buffer.metadata)
    meta["dc_offset_removed"] = {"real": float(np.real(mean_val)), "imag": float(np.imag(mean_val))}

    return SignalBuffer(
        samples=corrected_samples,
        sample_rate_hz=buffer.sample_rate_hz,
        center_frequency_hz=buffer.center_frequency_hz,
        channel_count=buffer.channel_count,
        source_format=buffer.source_format,
        sample_format=buffer.sample_format,
        start_time=buffer.start_time,
        metadata=meta,
    )


def correct_iq_imbalance(buffer: SignalBuffer) -> SignalBuffer:
    """Applies Gram-Schmidt orthogonalization to correct amplitude and phase IQ imbalance."""
    i_samples = np.real(buffer.samples)
    q_samples = np.imag(buffer.samples)

    # 1. Amplitude power estimation
    p_i = np.mean(i_samples**2)
    p_q = np.mean(q_samples**2)

    # Scale Q to match I power
    amp_scale = np.sqrt(p_i / (p_q + 1e-12))
    q_scaled = q_samples * amp_scale

    # 2. Phase estimation via cross-correlation
    sin_phi = np.mean(i_samples * q_scaled) / (p_i + 1e-12)
    sin_phi = np.clip(sin_phi, -0.999, 0.999)
    cos_phi = np.sqrt(1.0 - sin_phi**2)

    # Orthogonalize
    q_corr = (q_scaled - i_samples * sin_phi) / cos_phi
    corrected_samples = (i_samples + 1j * q_corr).astype(np.complex64)

    meta = dict(buffer.metadata)
    meta["iq_imbalance_correction"] = {
        "amplitude_ratio": float(amp_scale),
        "phase_error_rad": float(np.arcsin(sin_phi)),
    }

    return SignalBuffer(
        samples=corrected_samples,
        sample_rate_hz=buffer.sample_rate_hz,
        center_frequency_hz=buffer.center_frequency_hz,
        channel_count=buffer.channel_count,
        source_format=buffer.source_format,
        sample_format=buffer.sample_format,
        start_time=buffer.start_time,
        metadata=meta,
    )


def normalize_amplitude(buffer: SignalBuffer, target_peak: float = 1.0) -> SignalBuffer:
    """Normalizes maximum absolute amplitude to target_peak."""
    peak = float(np.max(np.abs(buffer.samples)))
    if peak > 1e-12:
        norm_samples = (buffer.samples * (target_peak / peak)).astype(np.complex64)
    else:
        norm_samples = buffer.samples.copy()

    meta = dict(buffer.metadata)
    meta["normalization"] = {"original_peak": peak, "target_peak": target_peak}

    return SignalBuffer(
        samples=norm_samples,
        sample_rate_hz=buffer.sample_rate_hz,
        center_frequency_hz=buffer.center_frequency_hz,
        channel_count=buffer.channel_count,
        source_format=buffer.source_format,
        sample_format=buffer.sample_format,
        start_time=buffer.start_time,
        metadata=meta,
    )


def frequency_shift(buffer: SignalBuffer, freq_shift_hz: float) -> SignalBuffer:
    """Mixes signal with complex exponential to translate frequency by freq_shift_hz."""
    if buffer.sample_rate_hz is None or buffer.sample_rate_hz <= 0:
        raise ValueError("Cannot frequency shift without known sample_rate_hz")

    num_samples = len(buffer.samples)
    t = np.arange(num_samples) / buffer.sample_rate_hz
    lo = np.exp(1j * 2 * np.pi * freq_shift_hz * t).astype(np.complex64)
    shifted_samples = (buffer.samples * lo).astype(np.complex64)

    new_fc = (
        (buffer.center_frequency_hz + freq_shift_hz)
        if buffer.center_frequency_hz is not None
        else None
    )

    meta = dict(buffer.metadata)
    meta["frequency_shift_hz"] = freq_shift_hz

    return SignalBuffer(
        samples=shifted_samples,
        sample_rate_hz=buffer.sample_rate_hz,
        center_frequency_hz=new_fc,
        channel_count=buffer.channel_count,
        source_format=buffer.source_format,
        sample_format=buffer.sample_format,
        start_time=buffer.start_time,
        metadata=meta,
    )


def resample_signal(buffer: SignalBuffer, target_sample_rate_hz: float) -> SignalBuffer:
    """Resamples signal to target_sample_rate_hz using polyphase filtering."""
    if buffer.sample_rate_hz is None or buffer.sample_rate_hz <= 0:
        raise ValueError("Cannot resample without known sample_rate_hz")

    if abs(buffer.sample_rate_hz - target_sample_rate_hz) < 1.0:
        return buffer

    # Simplify rational fraction
    from fractions import Fraction

    ratio = Fraction(target_sample_rate_hz / buffer.sample_rate_hz).limit_denominator(1000)
    up, down = ratio.numerator, ratio.denominator

    resampled_samples = signal.resample_poly(buffer.samples, up, down).astype(np.complex64)

    meta = dict(buffer.metadata)
    meta["resample"] = {
        "source_rate": buffer.sample_rate_hz,
        "target_rate": target_sample_rate_hz,
        "up": up,
        "down": down,
    }

    return SignalBuffer(
        samples=resampled_samples,
        sample_rate_hz=target_sample_rate_hz,
        center_frequency_hz=buffer.center_frequency_hz,
        channel_count=buffer.channel_count,
        source_format=buffer.source_format,
        sample_format=buffer.sample_format,
        start_time=buffer.start_time,
        metadata=meta,
    )

"""Signal Detection and Energy-based Region Segmentation."""

from __future__ import annotations

import numpy as np
from scipy import signal

from signal_lab.domain.models.signal import SignalBuffer, SignalSegment


def estimate_noise_floor_db(psd: np.ndarray) -> float:
    """Estimates the noise floor using median PSD power."""
    # Median is robust against narrow-band signal peaks
    median_pwr = float(np.median(psd))
    return 10.0 * np.log10(median_pwr + 1e-18)


def detect_signal_regions(
    buffer: SignalBuffer,
    threshold_db: float = 8.0,
    min_duration_s: float = 0.0002,
    stft_nperseg: int = 512,
) -> list[SignalSegment]:
    """Detects active signal bursts using time-frequency energy thresholding."""
    if buffer.num_samples < stft_nperseg:
        return []

    fs = buffer.sample_rate_hz or 1.0

    # Compute short-time energy envelope via STFT
    noverlap = stft_nperseg // 2
    freqs, times, sxx = signal.spectrogram(
        buffer.samples,
        fs=fs,
        window="hann",
        nperseg=stft_nperseg,
        noverlap=noverlap,
        return_onesided=False,
        scaling="density",
    )

    # Shift zero freq to center
    freqs = np.fft.fftshift(freqs)
    sxx = np.fft.fftshift(sxx, axes=0)

    # Time power profile (integrated across all frequencies)
    time_power = np.mean(sxx, axis=0)
    noise_floor = np.median(time_power)
    thresh = noise_floor * (10.0 ** (threshold_db / 10.0))

    active_mask = time_power > thresh
    if not np.any(active_mask):
        return []

    # Find contiguous active regions
    segments: list[SignalSegment] = []
    in_burst = False
    start_t_idx = 0

    for idx, is_active in enumerate(active_mask):
        if is_active and not in_burst:
            in_burst = True
            start_t_idx = idx
        elif not is_active and in_burst:
            in_burst = False
            duration = times[idx - 1] - times[start_t_idx]
            if duration >= min_duration_s:
                seg = _create_segment_from_stft(
                    buffer, freqs, times, sxx, start_t_idx, idx - 1, noise_floor
                )
                segments.append(seg)

    # Handle burst ending at the end of the capture
    if in_burst:
        duration = times[-1] - times[start_t_idx]
        if duration >= min_duration_s:
            seg = _create_segment_from_stft(
                buffer, freqs, times, sxx, start_t_idx, len(times) - 1, noise_floor
            )
            segments.append(seg)

    return segments


def _create_segment_from_stft(
    buffer: SignalBuffer,
    freqs: np.ndarray,
    times: np.ndarray,
    sxx: np.ndarray,
    t_start_idx: int,
    t_end_idx: int,
    noise_floor: float,
) -> SignalSegment:
    fs = buffer.sample_rate_hz or 1.0
    start_time_s = float(times[t_start_idx])
    end_time_s = float(times[t_end_idx])
    start_sample = max(0, int(start_time_s * fs))
    end_sample = min(buffer.num_samples, int(end_time_s * fs))

    # Slice spectrum for this time window to estimate center freq & SNR
    window_sxx = np.mean(sxx[:, t_start_idx : t_end_idx + 1], axis=1)
    peak_f_idx = int(np.argmax(window_sxx))
    center_f_offset = float(freqs[peak_f_idx])
    actual_center_f = (
        (buffer.center_frequency_hz + center_f_offset)
        if buffer.center_frequency_hz is not None
        else center_f_offset
    )

    # Estimate SNR
    peak_pwr = float(np.max(window_sxx))
    snr_db = 10.0 * np.log10(peak_pwr / (noise_floor + 1e-18))

    return SignalSegment(
        start_sample=start_sample,
        end_sample=end_sample,
        start_time_s=start_time_s,
        duration_s=end_time_s - start_time_s,
        center_frequency_hz=actual_center_f,
        snr_db=float(snr_db),
        metadata={"detection_method": "stft_energy_threshold"},
    )

"""Statistical and Higher-Order Feature Extraction for Modulation Analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from signal_lab.domain.models.signal import SignalBuffer


@dataclass
class ModulationFeatures:
    """Extracted statistical features for signal classification."""

    envelope_variation: float  # Var(|x|) / E[|x|]^2 (Low for FSK/PSK, High for QAM)
    crest_factor: float  # Peak / RMS amplitude
    kurtosis_real: float  # Kurtosis of In-phase component
    kurtosis_imag: float  # Kurtosis of Quadrature component
    c40_cumulant: complex  # 4th-order cumulant C40 = E[x^4] - 3*E[x^2]^2
    c42_cumulant: float  # 4th-order cumulant C42 = E[|x|^4] - |E[x^2]|^2 - 2*E[|x|^2]^2
    phase_std: float  # Standard deviation of instantaneous phase


def extract_modulation_features(buffer: SignalBuffer) -> ModulationFeatures:
    """Calculates key statistical cumulants and envelope properties."""
    samples = buffer.samples
    if len(samples) < 32:
        return ModulationFeatures(
            envelope_variation=0.0,
            crest_factor=1.0,
            kurtosis_real=0.0,
            kurtosis_imag=0.0,
            c40_cumulant=0j,
            c42_cumulant=0.0,
            phase_std=0.0,
        )

    # Normalize samples to unit variance
    pwr = float(np.mean(np.abs(samples) ** 2))
    if pwr > 1e-12:
        x = samples / np.sqrt(pwr)
    else:
        x = samples

    mag = np.abs(x)
    mean_mag = float(np.mean(mag))
    var_mag = float(np.var(mag))
    env_var = var_mag / (mean_mag**2 + 1e-12)

    peak_mag = float(np.max(mag))
    rms_mag = float(np.sqrt(np.mean(mag**2)))
    crest = peak_mag / (rms_mag + 1e-12)

    k_real = float(stats.kurtosis(np.real(x)))
    k_imag = float(stats.kurtosis(np.imag(x)))

    # 4th order cumulants
    m20 = np.mean(x**2)
    m21 = np.mean(np.abs(x) ** 2)
    m40 = np.mean(x**4)
    m42 = np.mean(np.abs(x) ** 4)

    c40 = m40 - 3.0 * (m20**2)
    c42 = m42 - np.abs(m20) ** 2 - 2.0 * (m21**2)

    phase_std = float(np.std(np.unwrap(np.angle(x))))

    return ModulationFeatures(
        envelope_variation=env_var,
        crest_factor=crest,
        kurtosis_real=k_real,
        kurtosis_imag=k_imag,
        c40_cumulant=complex(c40),
        c42_cumulant=float(c42),
        phase_std=phase_std,
    )

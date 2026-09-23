"""Power Spectral Density (PSD / FFT) visualization widget."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from scipy import signal

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.plots.base_plot import style_plot_widget
from signal_lab.gui.theme import ScientificPalette


class SpectrumPlotWidget(pg.PlotWidget):
    """Scientific spectrum visualizer displaying FFT / Welch PSD in dBFS."""

    def __init__(self, parent: pg.QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        style_plot_widget(self, title="SPECTRUM (PSD)")
        self.setLabel("left", "Power", units="dBFS")
        self.setLabel("bottom", "Frequency", units="Hz")

        self.spectrum_curve = self.plot(
            pen=pg.mkPen(color=ScientificPalette.ACCENT_CYAN, width=1.5),
            name="PSD",
        )
        self.peak_scatter = pg.ScatterPlotItem(
            size=8,
            pen=pg.mkPen(color=ScientificPalette.ACCENT_RED, width=1.5),
            brush=pg.mkBrush(color=ScientificPalette.BG_BASE),
        )
        self.addItem(self.peak_scatter)

    def set_signal(self, buffer: SignalBuffer, nperseg: int = 2048) -> None:
        """Compute and display Welch PSD for the given signal buffer."""
        if buffer.num_samples == 0:
            self.clear_spectrum()
            return

        fs = buffer.sample_rate_hz or 1.0
        nperseg = min(nperseg, buffer.num_samples)
        if nperseg < 16:
            return

        freqs, psd = signal.welch(
            buffer.samples,
            fs=fs,
            window="hann",
            nperseg=nperseg,
            return_onesided=False,
            scaling="density",
        )

        # Shift zero-frequency component to center
        freqs = np.fft.fftshift(freqs)
        psd = np.fft.fftshift(psd)

        # Add center frequency offset if known
        if buffer.center_frequency_hz is not None:
            freqs += buffer.center_frequency_hz

        # Convert to dBFS
        psd_db = 10 * np.log10(psd + 1e-15)
        # Normalize relative to max peak
        peak_val = np.max(psd_db)
        psd_norm = psd_db - peak_val

        self.spectrum_curve.setData(freqs, psd_norm)

        # Highlight peak
        peak_idx = int(np.argmax(psd_norm))
        self.peak_scatter.setData([{"pos": (freqs[peak_idx], psd_norm[peak_idx])}])

    def clear_spectrum(self) -> None:
        """Clear plot data."""
        self.spectrum_curve.setData([], [])
        self.peak_scatter.setData([])
